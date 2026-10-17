//! Core wallet operations for mobile (mirrors walletd, no broadcast).

use acp_crypto::{
    protocol_params::{MIN_FEE_UNITS, UNITS_PER_ACP},
    AddressV0, KeystoreV3, Mnemonic, Seed, Transaction, TxHex, TxInput, TxOutput, WalletIdentity,
};
use rand_core::OsRng;
use reqwest::blocking::Client;
use serde_json::{json, Value};
use std::time::Duration;

#[derive(Debug, thiserror::Error, uniffi::Error)]
pub enum AcpWalletException {
    #[error("invalid address")]
    InvalidAddress,
    #[error("invalid mnemonic")]
    InvalidMnemonic,
    #[error("invalid amount")]
    InvalidAmount,
    #[error("insufficient funds")]
    InsufficientFunds,
    #[error("rpc: {message}")]
    Rpc { message: String },
    #[error("internal: {message}")]
    Internal { message: String },
}

impl From<anyhow::Error> for AcpWalletException {
    fn from(e: anyhow::Error) -> Self {
        let msg = e.to_string();
        if msg.contains("invalid") && msg.contains("address") {
            AcpWalletException::InvalidAddress
        } else if msg.contains("mnemonic") {
            AcpWalletException::InvalidMnemonic
        } else if msg.contains("insufficient") {
            AcpWalletException::InsufficientFunds
        } else if msg.contains("RPC") || msg.contains("rpc") {
            AcpWalletException::Rpc { message: msg }
        } else {
            AcpWalletException::Internal { message: msg }
        }
    }
}

#[derive(uniffi::Record)]
pub struct CreatedWallet {
    pub address: String,
    pub mnemonic: String,
    /// Encrypted-ready keystore v3 JSON — required for stable address re-derivation (PQC keys).
    pub keystore_json: String,
}

#[derive(uniffi::Record)]
pub struct SignedTransfer {
    pub raw_tx: String,
    pub txid: String,
}

#[derive(uniffi::Record)]
pub struct FeeEstimate {
    pub fee_acp: String,
    pub fee_units: u64,
}

#[derive(Debug, Clone)]
struct Utxo {
    txid_hex: String,
    vout: u32,
    amount_units: u64,
}

fn rpc(client: &Client, rpc_url: &str, method: &str, params: Value) -> Result<Value, AcpWalletException> {
    let body = json!({
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    });
    let mut req = client.post(rpc_url).json(&body);
    if let Ok(t) = std::env::var("ACP_RPC_TOKEN") {
        let t = t.trim().to_string();
        if !t.is_empty() {
            req = req.header("x-acp-rpc-token", t);
        }
    }
    let res: Value = req
        .send()
        .map_err(|e| AcpWalletException::Rpc {
            message: e.to_string(),
        })?
        .json()
        .map_err(|e| AcpWalletException::Rpc {
            message: e.to_string(),
        })?;
    if let Some(err) = res.get("error") {
        return Err(AcpWalletException::Rpc {
            message: err.to_string(),
        });
    }
    Ok(res["result"].clone())
}

fn identity_from_mnemonic(mnemonic: &str) -> Result<(WalletIdentity, Seed), AcpWalletException> {
    let m = Mnemonic::parse(mnemonic.trim()).map_err(|_| AcpWalletException::InvalidMnemonic)?;
    let seed = m.to_seed("");
    let id = WalletIdentity::new_from_seed(&seed, OsRng).map_err(|e| AcpWalletException::Internal {
        message: e.to_string(),
    })?;
    Ok((id, seed))
}

fn identity_from_keystore_json(keystore_json: &str) -> Result<WalletIdentity, AcpWalletException> {
    let ks: KeystoreV3 = serde_json::from_str(keystore_json.trim()).map_err(|e| {
        AcpWalletException::Internal {
            message: format!("invalid keystore_json: {e}"),
        }
    })?;
    WalletIdentity::from_keystore_v3(&ks).map_err(|e| AcpWalletException::Internal {
        message: e.to_string(),
    })
}

fn format_acp(units: u64) -> String {
    let whole = units / UNITS_PER_ACP;
    let frac = units % UNITS_PER_ACP;
    let mut s = format!("{}.{:08}", whole, frac);
    while s.contains('.') && s.ends_with('0') {
        s.pop();
    }
    if s.ends_with('.') {
        s.pop();
    }
    if s.is_empty() {
        "0".to_string()
    } else {
        s
    }
}

fn acp_decimal_str_to_units(s: &str) -> Result<u64, AcpWalletException> {
    let s = s.trim();
    if s.is_empty() || s == "." {
        return Err(AcpWalletException::InvalidAmount);
    }
    let (whole_s, frac_raw) = match s.split_once('.') {
        Some((w, f)) => (w, f),
        None => (s, ""),
    };
    let whole: u64 = if whole_s.is_empty() {
        0
    } else {
        whole_s
            .parse()
            .map_err(|_| AcpWalletException::InvalidAmount)?
    };
    let mut frac = frac_raw.chars().take(8).collect::<String>();
    while frac.len() < 8 {
        frac.push('0');
    }
    let frac_n: u64 = frac.parse().map_err(|_| AcpWalletException::InvalidAmount)?;
    whole
        .checked_mul(UNITS_PER_ACP)
        .and_then(|w| w.checked_add(frac_n))
        .ok_or(AcpWalletException::InvalidAmount)
}

fn scan_utxos(client: &Client, rpc_url: &str, address: &str) -> Result<Vec<Utxo>, AcpWalletException> {
    let tip = rpc(client, rpc_url, "getblockcount", json!({}))?
        .as_u64()
        .ok_or_else(|| AcpWalletException::Rpc {
            message: "getblockcount did not return u64".into(),
        })?;
    if tip == 0 {
        return Ok(vec![]);
    }

    let mut unspent: std::collections::BTreeMap<String, Utxo> = std::collections::BTreeMap::new();
    let mut spent: std::collections::HashSet<String> = std::collections::HashSet::new();

    for h in 1..=tip {
        let bh = rpc(client, rpc_url, "getblockhash", json!({ "height": h }))?
            .as_str()
            .ok_or_else(|| AcpWalletException::Rpc {
                message: "getblockhash did not return string".into(),
            })?
            .to_string();

        let block = rpc(
            client,
            rpc_url,
            "getblock",
            json!({ "blockhash": bh, "verbose": 2 }),
        )?;
        let txs = block
            .get("tx")
            .and_then(|v| v.as_array())
            .ok_or_else(|| AcpWalletException::Rpc {
                message: "getblock.tx missing".into(),
            })?;

        for tx in txs {
            let txid = tx
                .get("txid")
                .and_then(|v| v.as_str())
                .ok_or_else(|| AcpWalletException::Rpc {
                    message: "tx.txid missing".into(),
                })?
                .to_string();

            if let Some(vin) = tx.get("vin").and_then(|v| v.as_array()) {
                for i in vin {
                    let prev = match i.get("prev_txid").and_then(|v| v.as_str()) {
                        Some(s) => s,
                        None => continue,
                    };
                    let vout = match i.get("vout").and_then(|v| v.as_u64()) {
                        Some(n) => n as u32,
                        None => continue,
                    };
                    let key = format!("{prev}:{vout}");
                    spent.insert(key.clone());
                    unspent.remove(&key);
                }
            }

            if let Some(vout) = tx.get("vout").and_then(|v| v.as_array()) {
                for (idx, o) in vout.iter().enumerate() {
                    let addr = o.get("recipient_address").and_then(|v| v.as_str());
                    if addr != Some(address) {
                        continue;
                    }
                    let amt = json_amount_units(
                        o.get("amount")
                            .ok_or_else(|| AcpWalletException::Rpc {
                                message: "vout.amount missing".into(),
                            })?,
                    )?;
                    let vout_index = idx as u32;
                    let key = format!("{txid}:{vout_index}");
                    if spent.contains(&key) {
                        continue;
                    }
                    unspent.insert(
                        key,
                        Utxo {
                            txid_hex: txid.clone(),
                            vout: vout_index,
                            amount_units: amt,
                        },
                    );
                }
            }
        }
    }

    Ok(unspent.into_values().collect())
}

fn json_amount_units(v: &Value) -> Result<u64, AcpWalletException> {
    if v.is_null() {
        return Err(AcpWalletException::Rpc {
            message: "amount is null".into(),
        });
    }
    if let Some(n) = v.as_u64() {
        return Ok(n);
    }
    if let Some(s) = v.as_str() {
        return s
            .trim()
            .parse()
            .map_err(|_| AcpWalletException::Rpc {
                message: "amount string is not u64".into(),
            });
    }
    Err(AcpWalletException::Rpc {
        message: "unsupported amount type".into(),
    })
}

pub fn acp_create_wallet() -> Result<CreatedWallet, AcpWalletException> {
    let m = Mnemonic::generate_12().map_err(|e| AcpWalletException::Internal {
        message: e.to_string(),
    })?;
    let words = m.words();
    let (id, seed) = identity_from_mnemonic(&words)?;
    let address = id.receive_address_v0().map_err(|e| AcpWalletException::Internal {
        message: e.to_string(),
    })?;
    let keystore = id.to_keystore_v3(&seed).map_err(|e| AcpWalletException::Internal {
        message: e.to_string(),
    })?;
    let keystore_json = serde_json::to_string(&keystore).map_err(|e| AcpWalletException::Internal {
        message: e.to_string(),
    })?;
    Ok(CreatedWallet {
        address,
        mnemonic: words,
        keystore_json,
    })
}

pub fn acp_import_mnemonic(mnemonic: String) -> Result<String, AcpWalletException> {
    let (id, _seed) = identity_from_mnemonic(&mnemonic)?;
    id.receive_address_v0().map_err(|e| AcpWalletException::Internal {
        message: e.to_string(),
    })
}

/// Rebuild from mnemonic only — NOT a stable restore path.
/// Dilithium keygen uses OsRng at create time; only keystore v3 roundtrips the address.
/// Kept for smoke tests that assert mnemonic ≠ original address.
pub fn acp_import_wallet(mnemonic: String) -> Result<CreatedWallet, AcpWalletException> {
    let words = mnemonic.split_whitespace().collect::<Vec<_>>().join(" ");
    let (id, seed) = identity_from_mnemonic(&words)?;
    let address = id.receive_address_v0().map_err(|e| AcpWalletException::Internal {
        message: e.to_string(),
    })?;
    let keystore = id.to_keystore_v3(&seed).map_err(|e| AcpWalletException::Internal {
        message: e.to_string(),
    })?;
    let keystore_json = serde_json::to_string(&keystore).map_err(|e| AcpWalletException::Internal {
        message: e.to_string(),
    })?;
    Ok(CreatedWallet {
        address,
        mnemonic: words,
        keystore_json,
    })
}

pub fn acp_address_from_keystore(keystore_json: String) -> Result<String, AcpWalletException> {
    let id = identity_from_keystore_json(&keystore_json)?;
    id.receive_address_v0().map_err(|e| AcpWalletException::Internal {
        message: e.to_string(),
    })
}

pub fn acp_validate_address(address: String) -> bool {
    let s = address.trim();
    if !s.starts_with("acp1") {
        return false;
    }
    AddressV0::decode(s).is_ok()
}

pub fn acp_address_from_mnemonic(mnemonic: String) -> Result<String, AcpWalletException> {
    acp_import_mnemonic(mnemonic)
}

pub fn acp_estimate_fee_default() -> Result<FeeEstimate, AcpWalletException> {
    Ok(FeeEstimate {
        fee_acp: format_acp(MIN_FEE_UNITS),
        fee_units: MIN_FEE_UNITS,
    })
}

pub fn acp_sign_transfer(
    rpc_url: String,
    keystore_json: String,
    to_address: String,
    amount_acp: String,
    fee_acp: Option<String>,
) -> Result<SignedTransfer, AcpWalletException> {
    let transfer_units = acp_decimal_str_to_units(&amount_acp)?;
    if transfer_units == 0 {
        return Err(AcpWalletException::InvalidAmount);
    }
    let fee_units = if let Some(ref v) = fee_acp {
        let parsed = acp_decimal_str_to_units(v)?;
        if parsed < MIN_FEE_UNITS {
            return Err(AcpWalletException::InvalidAmount);
        }
        parsed
    } else {
        MIN_FEE_UNITS
    };

    let client = Client::builder()
        .timeout(Duration::from_secs(60))
        .build()
        .map_err(|e| AcpWalletException::Internal {
            message: e.to_string(),
        })?;

    let chain_id = rpc(&client, &rpc_url, "getnetworkinfo", json!({}))?
        .get("chain_id")
        .and_then(|v| v.as_u64())
        .map(|v| v as u32)
        .ok_or_else(|| AcpWalletException::Rpc {
            message: "getnetworkinfo.chain_id missing".into(),
        })?;

    let id = identity_from_keystore_json(&keystore_json)?;
    let from_address = id.receive_address_v0().map_err(|e| AcpWalletException::Internal {
        message: e.to_string(),
    })?;

    let to_addr = AddressV0::decode(to_address.trim()).map_err(|_| AcpWalletException::InvalidAddress)?;

    let mut utxos = scan_utxos(&client, &rpc_url, &from_address)?;
    utxos.sort_by_key(|u| std::cmp::Reverse(u.amount_units));

    let mut picked: Vec<Utxo> = vec![];
    let mut sum: u64 = 0;
    for u in utxos {
        picked.push(u.clone());
        sum = sum.saturating_add(u.amount_units);
        if sum >= transfer_units.saturating_add(fee_units) {
            break;
        }
    }
    if sum < transfer_units.saturating_add(fee_units) {
        return Err(AcpWalletException::InsufficientFunds);
    }

    let change = sum - transfer_units - fee_units;
    let mut outputs = vec![TxOutput::to_address_v0(transfer_units, &to_addr)];
    if change > 0 {
        let from_decoded = AddressV0::decode(&from_address).map_err(|_| AcpWalletException::InvalidAddress)?;
        outputs.push(TxOutput::to_address_v0(change, &from_decoded));
    }

    let inputs: Vec<TxInput> = picked
        .iter()
        .map(|u| TxInput {
            prev_txid: TxHex::decode_txid(&u.txid_hex).expect("txid decode"),
            vout: u.vout,
            amount: u.amount_units,
        })
        .collect();

    let mut tx = Transaction::new_unsigned(chain_id, inputs, outputs);
    // AddressV0 is derived from the view public key; stateful ownership
    // validation therefore requires its matching signature.
    tx.sign(&id.view).map_err(|e| AcpWalletException::Internal {
        message: e.to_string(),
    })?;
    let raw_tx = TxHex::encode_tx(&tx).map_err(|e| AcpWalletException::Internal {
        message: e.to_string(),
    })?;
    let txid = TxHex::encode_txid(&tx.txid().map_err(|e| AcpWalletException::Internal {
        message: e.to_string(),
    })?);

    Ok(SignedTransfer { raw_tx, txid })
}
