//! Minimal wallet helper for ANCAP backend (custodial hot-wallet).
//!
//! Commands (stdout is JSON):
//! - `walletd new` -> {"address":"acp1...","mnemonic":"..."}
//! - `walletd address --mnemonic "..."` -> {"address":"acp1..."}
//! - `walletd balance --rpc URL --address acp1...` -> {"address":"acp1...","units":"123","acp":"1.23"}
//! - `walletd transfer --rpc URL --mnemonic "..." --to acp1... --amount-acp 1.5`
//!     -> {"accepted":true,"txid":"..."} (accepted=false includes "reason")
//! - `walletd sign-transfer --rpc URL --mnemonic "..." --to acp1... --amount-acp 1.5`
//!     -> {"raw_tx":"...","txid":"..."} (local sign only; use submit to broadcast)
//! - `walletd submit --rpc URL --raw-tx HEX`
//!     -> {"accepted":true,"txid":"..."}

use anyhow::{anyhow, Context};
use acp_crypto::{
    protocol_params::{MIN_FEE_UNITS, UNITS_PER_ACP},
    AddressV0, KeystoreV3, Mnemonic, Transaction, TxHex, TxInput, TxOutput, WalletIdentity,
};
use rand_core::OsRng;
use reqwest::blocking::Client;
use serde_json::{json, Value};
use std::collections::{BTreeMap, HashSet};
use std::io::Read;
use std::time::Duration;

const RPC_USER_AGENT: &str = "ancap-walletd/1.0";
// Covers the protocol's 10,000 indexed inputs plus keystore/JSON overhead.
const MAX_PRIVATE_REQUEST_BYTES: usize = 2 * 1024 * 1024;

fn rpc(client: &Client, rpc_url: &str, method: &str, params: Value) -> anyhow::Result<Value> {
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
    let res: Value = req.send()?.json()?;
    if let Some(err) = res.get("error") {
        anyhow::bail!("RPC error: {}", err);
    }
    Ok(res["result"].clone())
}

fn best_height(client: &Client, rpc_url: &str) -> anyhow::Result<u64> {
    rpc(client, rpc_url, "getblockcount", json!({}))?
        .as_u64()
        .ok_or_else(|| anyhow!("getblockcount did not return u64"))
}

fn get_chain_id(client: &Client, rpc_url: &str) -> anyhow::Result<u32> {
    let chain_id = rpc(client, rpc_url, "getnetworkinfo", json!({}))?
        .get("chain_id")
        .and_then(|v| v.as_u64())
        .ok_or_else(|| anyhow!("getnetworkinfo.chain_id missing"))?;
    let chain_id = u32::try_from(chain_id).context("invalid chain id")?;
    if let Ok(expected) = std::env::var("ACP_EXPECTED_CHAIN_ID") {
        if chain_id != expected.parse::<u32>().context("invalid expected chain id")? {
            anyhow::bail!("unexpected chain id");
        }
    }
    Ok(chain_id)
}

#[derive(Debug, Clone)]
struct Utxo {
    txid_hex: String,
    vout: u32,
    amount_units: u64,
}

/// Scan chain for UTXOs to a given bech32 address.
/// NOTE: This is O(chain) and intended for small chains / bootstrap.
fn scan_utxos(client: &Client, rpc_url: &str, address: &str) -> anyhow::Result<Vec<Utxo>> {
    let tip = best_height(client, rpc_url)?;
    if tip == 0 {
        return Ok(vec![]);
    }

    // Unspent outputs to `address`: key is "txid:vout"
    let mut unspent: BTreeMap<String, Utxo> = BTreeMap::new();
    let mut spent: HashSet<String> = HashSet::new();

    for h in 1..=tip {
        let bh = rpc(client, rpc_url, "getblockhash", json!({ "height": h }))?
            .as_str()
            .ok_or_else(|| anyhow!("getblockhash did not return string"))?
            .to_string();

        // verbose=2 returns {"tx": [decoded tx objects...]}
        let block = rpc(client, rpc_url, "getblock", json!({ "blockhash": bh, "verbose": 2 }))?;
        let txs = block
            .get("tx")
            .and_then(|v| v.as_array())
            .ok_or_else(|| anyhow!("getblock.tx missing"))?;

        for tx in txs {
            let txid = tx
                .get("txid")
                .and_then(|v| v.as_str())
                .ok_or_else(|| anyhow!("tx.txid missing"))?
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
                            .ok_or_else(|| anyhow!("vout.amount missing"))?,
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

/// Convert smallest units to an ACP decimal string without `f64` (whole-chain amounts exceed
/// IEEE-754 integer precision; `f64` can drift and confuse users vs RPC `amount`).
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

fn acp_decimal_str_to_units(s: &str) -> anyhow::Result<u64> {
    let s = s.trim();
    if s.is_empty() || s == "." {
        anyhow::bail!("amount-acp is empty");
    }
    let (whole_s, frac_raw) = match s.split_once('.') {
        Some((w, f)) => (w, f),
        None => (s, ""),
    };
    let whole: u64 = if whole_s.is_empty() {
        0
    } else {
        whole_s.parse().map_err(|_| anyhow!("invalid whole ACP"))?
    };
    let mut frac = frac_raw.chars().take(8).collect::<String>();
    while frac.len() < 8 {
        frac.push('0');
    }
    let frac_n: u64 = frac.parse().map_err(|_| anyhow!("invalid fractional ACP"))?;
    whole
        .checked_mul(UNITS_PER_ACP)
        .and_then(|w| w.checked_add(frac_n))
        .ok_or_else(|| anyhow!("amount-acp overflow"))
}

fn json_amount_units(v: &Value) -> anyhow::Result<u64> {
    if v.is_null() {
        anyhow::bail!("amount is null");
    }
    if let Some(n) = v.as_u64() {
        return Ok(n);
    }
    if let Some(n) = v.as_i64() {
        return u64::try_from(n).map_err(|_| anyhow!("negative amount"));
    }
    if let Some(s) = v.as_str() {
        return s
            .trim()
            .parse()
            .map_err(|_| anyhow!("amount string is not u64"));
    }
    if let Some(f) = v.as_f64() {
        if !f.is_finite() || f < 0.0 {
            anyhow::bail!("invalid amount float");
        }
        // Reject non-integer floats to avoid silent precision loss.
        let r = f.round();
        if (r - f).abs() > 1e-6 {
            anyhow::bail!("amount must be an integer in smallest units");
        }
        if r > (u64::MAX as f64) {
            anyhow::bail!("amount too large");
        }
        return Ok(r as u64);
    }
    anyhow::bail!("amount has unsupported JSON type")
}

fn identity_from_mnemonic(mnemonic: &str) -> anyhow::Result<(WalletIdentity, acp_crypto::Seed)> {
    let m = Mnemonic::parse(mnemonic.trim())?;
    let seed = m.to_seed("");
    let id = WalletIdentity::new_from_seed(&seed, OsRng)?;
    Ok((id, seed))
}

fn identity_from_keystore_json(keystore_json: &str) -> anyhow::Result<WalletIdentity> {
    let ks: KeystoreV3 = serde_json::from_str(keystore_json.trim())
        .context("invalid keystore_json")?;
    WalletIdentity::from_keystore_v3(&ks).map_err(Into::into)
}

fn cmd_new() -> anyhow::Result<Value> {
    let m = Mnemonic::generate_12()?;
    let (id, seed) = identity_from_mnemonic(&m.words())?;
    let address = id.receive_address_v0()?;
    let view_wire = id.view_pubkey_wire()?;
    let keystore = id.to_keystore_v3(&seed)?;
    let keystore_json = serde_json::to_string(&keystore)?;
    Ok(json!({
        "address": address,
        "mnemonic": m.words(),
        "keystore_json": keystore_json,
        "view_pubkey_wire_hex": hex::encode(view_wire),
        "privacy_profile": acp_crypto::PRIVACY_PROFILE
    }))
}

fn cmd_address(
    mnemonic: Option<&str>,
    keystore_json: Option<&str>,
    index: u32,
) -> anyhow::Result<Value> {
    let id = if let Some(kj) = keystore_json {
        identity_from_keystore_json(kj)?
    } else if let Some(m) = mnemonic {
        identity_from_mnemonic(m)?.0
    } else {
        anyhow::bail!("either --mnemonic or --keystore-json is required")
    };
    let address = id.receive_subaddress_v0(index)?;
    let view_wire = id.view_pubkey_wire()?;
    Ok(json!({
        "address": address,
        "index": index,
        "view_pubkey_wire_hex": hex::encode(view_wire),
        "redacted": acp_crypto::redact_address(&address),
        "privacy_profile": acp_crypto::PRIVACY_PROFILE
    }))
}

fn cmd_balance(rpc_url: &str, address: &str) -> anyhow::Result<Value> {
    AddressV0::decode(address).context("invalid ACP address")?;
    let client = Client::builder()
        .user_agent(RPC_USER_AGENT)
        .timeout(Duration::from_secs(30))
        .build()?;
    let utxos = scan_utxos(&client, rpc_url, address)?;
    let units: u64 = utxos.iter().map(|u| u.amount_units).sum();
    Ok(json!({
        "address": address,
        "units": units.to_string(),
        "acp": format_acp(units),
        "utxo_count": utxos.len()
    }))
}

fn cmd_sign_transfer(
    rpc_url: &str,
    keystore_json: &str,
    to: &str,
    amount_acp: &str,
    fee_acp: Option<&str>,
) -> anyhow::Result<Value> {
    let signed = acp_mobile_ffi::acp_sign_transfer(
        rpc_url.to_string(),
        keystore_json.to_string(),
        to.to_string(),
        amount_acp.to_string(),
        fee_acp.map(|s| s.to_string()),
    )
    .map_err(|e| anyhow!("{e}"))?;
    Ok(json!({
        "raw_tx": signed.raw_tx,
        "txid": signed.txid
    }))
}

fn cmd_submit(rpc_url: &str, raw_tx: &str) -> anyhow::Result<Value> {
    let mut hex = raw_tx.trim().to_string();
    if hex.starts_with("0x") || hex.starts_with("0X") {
        hex = hex[2..].to_string();
    }
    let client = Client::builder()
        .user_agent(RPC_USER_AGENT)
        .timeout(Duration::from_secs(60))
        .build()?;
    let send_res = rpc(&client, rpc_url, "sendrawtransaction", json!({ "tx": hex }))?;
    let accepted = send_res.get("accepted").and_then(|v| v.as_bool()).unwrap_or(false);
    if accepted {
        Ok(json!({
            "accepted": true,
            "txid": send_res.get("txid").and_then(|v| v.as_str()).unwrap_or("")
        }))
    } else {
        Ok(json!({
            "accepted": false,
            "reason": send_res.get("reason").and_then(|v| v.as_str()).unwrap_or("unknown")
        }))
    }
}

fn parse_utxo_spec(spec: &str) -> anyhow::Result<Utxo> {
    // Format: txid:vout:units  (txid hex, vout u32, amount in smallest units)
    let parts: Vec<&str> = spec.trim().split(':').collect();
    if parts.len() != 3 {
        anyhow::bail!("--utxo expects txid:vout:units, got {spec}");
    }
    let txid_hex = parts[0].trim().to_string();
    if txid_hex.len() < 16 {
        anyhow::bail!("invalid --utxo txid");
    }
    let vout: u32 = parts[1]
        .trim()
        .parse()
        .context("invalid --utxo vout")?;
    let amount_units: u64 = parts[2]
        .trim()
        .parse()
        .context("invalid --utxo units")?;
    if amount_units == 0 {
        anyhow::bail!("--utxo units must be > 0");
    }
    Ok(Utxo {
        txid_hex,
        vout,
        amount_units,
    })
}

fn cmd_transfer(
    rpc_url: &str,
    mnemonic: Option<&str>,
    keystore_json: Option<&str>,
    to: &str,
    amount_acp: &str,
    fee_acp: Option<&str>,
    preloaded_utxos: Option<Vec<Utxo>>,
) -> anyhow::Result<Value> {
    let transfer_units = acp_decimal_str_to_units(amount_acp)?;
    if transfer_units == 0 {
        anyhow::bail!("amount-acp must be > 0");
    }
    let fee_units = if let Some(v) = fee_acp {
        let parsed_fee_units = acp_decimal_str_to_units(v)?;
        if parsed_fee_units < MIN_FEE_UNITS {
            anyhow::bail!("fee-acp must be >= {}", format_acp(MIN_FEE_UNITS));
        }
        parsed_fee_units
    } else {
        MIN_FEE_UNITS
    };

    let client = Client::builder()
        .user_agent(RPC_USER_AGENT)
        .timeout(Duration::from_secs(60))
        .build()?;
    let chain_id = get_chain_id(&client, rpc_url)?;

    let id = if let Some(kj) = keystore_json {
        identity_from_keystore_json(kj)?
    } else if let Some(m) = mnemonic {
        identity_from_mnemonic(m)?.0
    } else {
        anyhow::bail!("either --mnemonic or --keystore-json is required")
    };
    let from_address = id.receive_address_v0()?;
    if let Ok(expected) = std::env::var("ACP_EXPECTED_SOURCE_ADDRESS") {
        if from_address != expected {
            anyhow::bail!("unexpected source wallet");
        }
    }
    let scan_window = acp_crypto::DEFAULT_SUBADDR_SCAN_WINDOW;

    // Prefer preloaded UTXOs (from ANCAP UTXO index) to avoid O(tip) tip-scans (~30k blocks).
    let mut utxos: Vec<Utxo> = if let Some(pre) = preloaded_utxos.filter(|v| !v.is_empty()) {
        pre
    } else {
        let mut scanned: Vec<Utxo> = vec![];
        let mut seen = std::collections::HashSet::<String>::new();
        for idx in 0..=scan_window {
            let addr = id.receive_subaddress_v0(idx)?;
            for u in scan_utxos(&client, rpc_url, &addr)? {
                let key = format!("{}:{}", u.txid_hex, u.vout);
                if seen.insert(key) {
                    scanned.push(u);
                }
            }
        }
        scanned
    };
    // simple greedy: largest-first to minimize inputs
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
        return Ok(json!({
            "accepted": false,
            "reason": "insufficient funds"
        }));
    }

    let change = sum - transfer_units - fee_units;
    let to_addr_decoded = AddressV0::decode(to.trim()).context("invalid 'to' address")?;
    let mut outputs = vec![TxOutput::to_address_v0(transfer_units, &to_addr_decoded)];
    if change > 0 {
        // Keep change on the indexed primary address. Rotating operator change
        // without registering it made role balances incomplete.
        let change_addr = id.receive_address_v0()?;
        let change_decoded = AddressV0::decode(&change_addr)?;
        outputs.push(TxOutput::to_address_v0(change, &change_decoded));
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
    // AddressV0 commits to the view public key, so that key authorizes spends.
    tx.sign(&id.view)?;
    let tx_hex = TxHex::encode_tx(&tx)?;
    let txid = TxHex::encode_txid(&tx.txid()?);

    let send_res = rpc(&client, rpc_url, "sendrawtransaction", json!({ "tx": tx_hex }))?;
    let accepted = send_res.get("accepted").and_then(|v| v.as_bool()).unwrap_or(false);
    if accepted {
        Ok(json!({ "accepted": true, "txid": txid }))
    } else {
        Ok(json!({
            "accepted": false,
            "txid": txid,
            "reason": send_res.get("reason").and_then(|v| v.as_str()).unwrap_or("unknown")
        }))
    }
}

fn main() {
    if let Err(e) = real_main() {
        println!("{}", json!({ "ok": false, "error": e.to_string() }));
        std::process::exit(1);
    }
}

fn read_private_request(reader: impl Read) -> anyhow::Result<Vec<String>> {
    let mut bytes = Vec::new();
    reader.take((MAX_PRIVATE_REQUEST_BYTES + 1) as u64).read_to_end(&mut bytes)?;
    if bytes.len() > MAX_PRIVATE_REQUEST_BYTES {
        anyhow::bail!("private request too large");
    }
    let args: Vec<String> = serde_json::from_slice(&bytes)
        .map_err(|_| anyhow!("invalid private request"))?;
    if args.is_empty() || args[0] == "--request-stdin" {
        anyhow::bail!("invalid private request");
    }
    Ok(args)
}

fn real_main() -> anyhow::Result<()> {
    let raw: Vec<String> = std::env::args().skip(1).collect();
    let private = raw.first().map(String::as_str) == Some("--request-stdin");
    let request = if private {
        if raw.len() != 1 { anyhow::bail!("private request accepts no argv options"); }
        read_private_request(std::io::stdin().lock())?
    } else { raw };
    let mut args = request.into_iter();
    let cmd = args.next().ok_or_else(|| anyhow!("missing command"))?;

    let out = match cmd.as_str() {
        "new" => cmd_new()?,
        "address" => {
            let mut mnemonic: Option<String> = None;
            let mut keystore_json: Option<String> = None;
            let mut keystore_file: Option<String> = None;
            let mut index: u32 = 0;
            while let Some(a) = args.next() {
                if a == "--mnemonic" {
                    mnemonic = args.next();
                } else if a == "--keystore-json" {
                    keystore_json = args.next();
                } else if a == "--keystore-file" {
                    keystore_file = args.next();
                } else if a == "--index" {
                    index = args
                        .next()
                        .ok_or_else(|| anyhow!("--index requires a value"))?
                        .parse()
                        .context("invalid --index")?;
                    if index > acp_crypto::DEFAULT_SUBADDR_SCAN_WINDOW {
                        anyhow::bail!(
                            "--index must be <= {}",
                            acp_crypto::DEFAULT_SUBADDR_SCAN_WINDOW
                        );
                    }
                }
            }
            if keystore_json.is_none() {
                if let Some(path) = keystore_file {
                    keystore_json = Some(std::fs::read_to_string(path)?);
                }
            }
            cmd_address(mnemonic.as_deref(), keystore_json.as_deref(), index)?
        }
        "balance" => {
            let mut rpc_url: Option<String> = None;
            let mut address: Option<String> = None;
            while let Some(a) = args.next() {
                match a.as_str() {
                    "--rpc" => rpc_url = args.next(),
                    "--address" => address = args.next(),
                    _ => {}
                }
            }
            let rpc_url = rpc_url.ok_or_else(|| anyhow!("--rpc is required"))?;
            let address = address.ok_or_else(|| anyhow!("--address is required"))?;
            cmd_balance(&rpc_url, &address)?
        }
        "transfer" => {
            let mut rpc_url: Option<String> = None;
            let mut mnemonic: Option<String> = None;
            let mut keystore_json: Option<String> = None;
            let mut keystore_file: Option<String> = None;
            let mut to: Option<String> = None;
            let mut amount_acp: Option<String> = None;
            let mut fee_acp: Option<String> = None;
            let mut preloaded: Vec<Utxo> = vec![];
            while let Some(a) = args.next() {
                match a.as_str() {
                    "--rpc" => rpc_url = args.next(),
                    "--mnemonic" => mnemonic = args.next(),
                    "--keystore-json" => keystore_json = args.next(),
                    "--keystore-file" => keystore_file = args.next(),
                    "--mnemonic-file" => {
                        let path = args.next().ok_or_else(|| anyhow!("mnemonic file required"))?;
                        mnemonic = Some(std::fs::read_to_string(path)?.trim().to_string());
                    }
                    "--to" => to = args.next(),
                    "--amount-acp" => amount_acp = args.next(),
                    "--fee-acp" => fee_acp = args.next(),
                    "--utxo" => {
                        let spec = args
                            .next()
                            .ok_or_else(|| anyhow!("--utxo requires txid:vout:units"))?;
                        preloaded.push(parse_utxo_spec(&spec)?);
                    }
                    _ => {}
                }
            }
            if keystore_json.is_none() {
                if let Some(path) = keystore_file {
                    keystore_json = Some(std::fs::read_to_string(path)?);
                }
            }
            let rpc_url = rpc_url.ok_or_else(|| anyhow!("--rpc is required"))?;
            let to = to.ok_or_else(|| anyhow!("--to is required"))?;
            let amount_acp = amount_acp.ok_or_else(|| anyhow!("--amount-acp is required"))?;
            cmd_transfer(
                &rpc_url,
                mnemonic.as_deref(),
                keystore_json.as_deref(),
                &to,
                &amount_acp,
                fee_acp.as_deref(),
                if preloaded.is_empty() {
                    None
                } else {
                    Some(preloaded)
                },
            )?
        }
        "sign-transfer" => {
            let mut rpc_url: Option<String> = None;
            let mut keystore_json: Option<String> = None;
            let mut keystore_file: Option<String> = None;
            let mut to: Option<String> = None;
            let mut amount_acp: Option<String> = None;
            let mut fee_acp: Option<String> = None;
            while let Some(a) = args.next() {
                match a.as_str() {
                    "--rpc" => rpc_url = args.next(),
                    "--keystore-json" => keystore_json = args.next(),
                    "--keystore-file" => keystore_file = args.next(),
                    "--to" => to = args.next(),
                    "--amount-acp" => amount_acp = args.next(),
                    "--fee-acp" => fee_acp = args.next(),
                    _ => {}
                }
            }
            if keystore_json.is_none() {
                if let Some(path) = keystore_file {
                    keystore_json = Some(std::fs::read_to_string(path)?);
                }
            }
            let rpc_url = rpc_url.ok_or_else(|| anyhow!("--rpc is required"))?;
            let keystore_json =
                keystore_json.ok_or_else(|| anyhow!("--keystore-json or --keystore-file is required"))?;
            let to = to.ok_or_else(|| anyhow!("--to is required"))?;
            let amount_acp = amount_acp.ok_or_else(|| anyhow!("--amount-acp is required"))?;
            cmd_sign_transfer(
                &rpc_url,
                &keystore_json,
                &to,
                &amount_acp,
                fee_acp.as_deref(),
            )?
        }
        "submit" => {
            let mut rpc_url: Option<String> = None;
            let mut raw_tx: Option<String> = None;
            while let Some(a) = args.next() {
                match a.as_str() {
                    "--rpc" => rpc_url = args.next(),
                    "--raw-tx" => raw_tx = args.next(),
                    _ => {}
                }
            }
            let rpc_url = rpc_url.ok_or_else(|| anyhow!("--rpc is required"))?;
            let raw_tx = raw_tx.ok_or_else(|| anyhow!("--raw-tx is required"))?;
            cmd_submit(&rpc_url, &raw_tx)?
        }
        _ => anyhow::bail!("unknown command: {cmd}"),
    };

    println!("{}", json!({ "ok": true, "result": out }));
    Ok(())
}

#[cfg(test)]
mod private_request_tests {
    use super::*;

    #[test]
    fn private_channel_preserves_secret_and_rejects_invalid_shapes() {
        let args = read_private_request(br#"["address","--mnemonic","fixture secret"]"#.as_slice()).unwrap();
        assert_eq!(args[2], "fixture secret");
        for invalid in ["{}", "[]", "[1]", "[\"--request-stdin\"]"] {
            assert!(read_private_request(invalid.as_bytes()).is_err());
        }
        assert!(read_private_request(vec![b' '; MAX_PRIVATE_REQUEST_BYTES + 1].as_slice()).is_err());
        let mut indexed = vec!["transfer".to_string()];
        for _ in 0..acp_crypto::protocol_params::MAX_TX_INPUTS_OUTPUTS {
            indexed.push("--utxo".into());
            indexed.push(format!("{}:4294967295:21000000000000000", "a".repeat(64)));
        }
        let encoded = serde_json::to_vec(&indexed).unwrap();
        assert_eq!(read_private_request(encoded.as_slice()).unwrap(), indexed);
    }
}

