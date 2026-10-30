> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# ACP Wallet — Technical Specification

Normative for mobile SDK and app. Source of truth in code: `ACP-crypto/`, `walletd`, `app/api/routers/wallet_acp.py`.

## Network

| Field | Value |
|-------|--------|
| Chain | ANCAP ACP (native UTXO) |
| Default RPC | `https://acp1.ancap.cloud/rpc` |
| Address prefix | `acp1` (bech32-like) |
| Regex (API) | `^acp1[a-z0-9]{20,100}$` |
| Decimals | **8** (`UNITS_PER_ACP = 10^8`) |
| Min fee | `MIN_FEE_UNITS` in `acp-crypto` protocol params |

## Keys

| Item | Spec |
|------|------|
| Mnemonic | BIP39 (12 words default via `walletd new`) |
| Keystore | **Keystore v3 JSON** — required on device for stable address (PQC keys are RNG-seeded once) |
| Derivation | `WalletIdentity::new_from_seed` / `from_keystore_v3` |
| Spend signature | Ed25519 + PQC hybrid (Keystore v3) |
| Receive address | `AddressV0` from **view** public key → bech32 `acp1...` |

Mobile vault must store: `keystore_json` + mnemonic (backup) + address (cache).

## Amounts

- All on-chain amounts are **integer smallest units** (8 decimals).
- Display: decimal string, e.g. `1.5` ACP = `150000000` units.
- Conversion in mobile SDK: `parseUnits` / `formatUnits` with `decimals = 8`.

## Transactions (UTXO)

1. Scan UTXOs for `from` address (walletd / RPC).
2. Select inputs (greedy largest-first in `walletd transfer`).
3. Build outputs: `to` + change.
4. Sign with spend key.
5. Broadcast: JSON-RPC `sendrawtransaction` with `{ "tx": "<hex>" }`.

## Transaction statuses (UI)

`draft` → `signing` → `broadcasting` → `pending` → `confirmed` | `failed`

Confirmations: compare tx block height to chain tip (`getblockcount`).

## wACP (BSC)

| Field | Value |
|-------|--------|
| Token | BEP-20 wACP |
| Decimals | **18** |
| Mapping | `wacp_wei = acp_smallest * 10^10` |

See `docs/bridge-spec-v1.md` and `app/services/bridge_decimal.py`.

## Explorer links

From mobile config API:

- ACP tx: `{acpExplorerTxBase}/{txid}`
- BSC: `{bscExplorerBase}/tx/{hash}`

## Errors (API)

| Code | Meaning |
|------|---------|
| 400 | Invalid address / amount |
| 502 | RPC or walletd failure |
| 503 | RPC not configured / maintenance |

## References

- `ACP-crypto/acp-wallet/src/bin/walletd.rs`
- `docs/bridge-spec-v1.md`
- `docs/mobile/API_MOBILE.md`
