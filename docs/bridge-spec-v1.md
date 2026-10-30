> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# ANCAP wACP / BSC bridge spec v1

## 1. Goal

Bridge native ACP value into a BSC-side wrapped token (`wACP`) with operator-controlled minting, reserve-backed accountability, and clear status / audit surfaces.

### Wrap ratio (cutover 2026-10-04)

- **1 ACP ↔ 10 wACP** (locked in `app/services/bridge_decimal.py` as `WACP_PER_ACP = 10`).
- Conversion uses ACP 8 decimals ↔ wACP 18 decimals with scale `10^11` (`10^10` decimal pad × 10).
- Pre-cutover mints used 1:1 (`10^10` scale). Reverse redeem after cutover pays **1 ACP per 10 wACP** for all burns (legacy disclosure in `/legal/risk` and `/legal/market-data`).
- Pause bridge during deploy; unpause only after reserve proof is healthy under the new liability math.

## 2. Scope

v1 includes:
- ACP -> BSC intent registration
- reserve deposit confirmation on ACP
- BSC mint execution
- BSC -> ACP redeem intent / quote / burn-detection / payout-confirmation path
- reserve summary and public bridge status
- operator recovery/admin controls

## 3. Forward rail FSM

`PENDING_DEPOSIT` -> `CONFIRMED_ON_ACP` -> `MINT_REQUESTED` -> `MINTED_ON_BSC` -> `COMPLETED`

## 4. Reverse rail FSM

Normative reverse FSM target:
`BURN_REQUESTED` -> `BURN_CONFIRMED` -> `ACP_PAYOUT_SENT` -> `COMPLETED`

State semantics for reverse rail:
- `BURN_CONFIRMED` = confirmed `ReleaseRequested` event was matched idempotently to an operation
- `ACP_PAYOUT_SENT` = ACP payout transaction was submitted and `acp_tx_hash` recorded
- `COMPLETED` = ACP watcher later observed that payout tx on ACP with sufficient confirmations

## 5. Current implementation note as of 2026-05-23

Reverse rail is now live in runtime behavior, not merely staged internally:
- public bridge status currently exposes live redeem metadata when reserve health is acceptable
- intent registration exists
- quote/floor/remainder transparency exists
- BSC watcher ingests reverse burn requests
- orchestrator submits ACP payout and records `ACP_PAYOUT_SENT`
- ACP watcher performs final `COMPLETED` transition after ACP confirmation

Important nuance:
- runtime being live does **not** mean the reverse rail is fully hardened operationally
- replay/recovery validation, operator drills, and clearer public UX wording are still open follow-up work
- if the product wants reverse status to read as `pending-rollout`, runtime/API/UI must be changed deliberately to match that story

Failed / manual paths: `FAILED`, `DISPUTED`, `REORGED`.

## 6. Key roles (separation)

| Role | Access |
|------|--------|
| Deposit watcher | **Read-only** ACP RPC; no spend keys |
| Reserve (cold / semi-cold) | Funds majority of backing; manual/top-up procedures |
| Release signer | **Isolated hot** wallet; minimal balance; rotatable; in current implementation reuse the existing ACP hot-wallet / `walletd` operational path until a stricter dedicated signer split is introduced |

## 7. Smart contract (BSC) — v1 capabilities

- **WACP:** ERC-20, 18 decimals; `mint` / burn path only via **gateway** (single gateway address).
- **BridgeGateway:** `pause`; **mintCapPerDay**; **maxSingleMint**; owner/operator mint to user after off-chain proof; user `requestRelease(acpAddress, amount)` burns wACP held by gateway after `transferFrom` user; emits **`ReleaseRequested`** with `requestId`, `from`, `amount`, `acpAddress`.
- Emergency: unknown off-chain state -> **do not mint** until classified.

## 8. Reserve/accounting expectations

- Public bridge status and reserve summary must remain consistent.
- Reconciliation must explain both forward minted supply and reverse completed / outstanding liabilities.
- Reserve proof maturity still needs dedicated snapshots, stale-data detection, and operator mismatch alerting.

## 9. Operator truth rule

Docs, public status, and runtime behavior must not contradict each other.
If runtime says redeem is live, docs must not still claim `pending-rollout`.
If product wants a softer rollout posture, change runtime/API/UI intentionally and then document that exact truth.
