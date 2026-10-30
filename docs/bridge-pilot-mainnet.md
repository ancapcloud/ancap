> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# ACP -> BSC bridge pilot (mainnet)

## Status

As of 2026-05-23, the pilot is no longer just a plan.
It has already completed a real end-to-end ACP -> BSC run successfully, and the runtime also exposes a live reverse BSC -> ACP payout path.

### Current deployed contracts
- `WACP`: `0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402`
- `BridgeGateway`: `0x57c24FF77B23a82328cb88914D4FD4EEBd93321b`
- canonical public index: [OFFICIAL_CONTRACT_ADDRESSES.md](./OFFICIAL_CONTRACT_ADDRESSES.md)

### Current runtime state
- `BRIDGE_RAIL_ENABLED=true`
- `BRIDGE_RAIL_PAUSED=false`
- `BRIDGE_DRY_RUN=false`
- latest verified bridge status returned `confirmations_acp=1`
- latest verified bridge status returned `confirmations_bsc=18`
- BSC mint signer path is active
- reverse public status currently resolves to live (`redeem_available=true`, `redeem_mode="live"`) when reserve health is not critical

### Confirmed successful pilot operation
- operation id: `9320ecb4-c407-4ad2-8a4c-5c634b2259d8`
- ACP deposit tx: `6c38d15141424819700e043fbd664826d37b0e0de14179a5f18906c2b3b4838e`
- BSC mint tx: `a656c01758cd51f0fdd82627e6ac6ab5e7d24acbe4b694cd5e41cb1692ad8f8b`
- final status: `COMPLETED`
- minted amount: `1 wACP`

## What was fixed to make pilot work

1. Intent creation API FK ordering bug fixed.
2. ACP watcher now detects real reserve deposits and matches them to pending intents.
3. ACP confirmations are passed through runtime and currently verify as `1` in the latest checked environment.
4. Orchestrator submits live BSC mint txs.
5. BSC watcher normalizes tx hashes with `0x` before receipt lookup.
6. API exposes:
   - `acp_tx_hash`
   - `bsc_tx_hash_mint`
   - `deposit_ref_hex`
   - `bsc_log_index`
   - `version`
7. Frontend intent list shows those result fields, links mint tx to BscScan, and links ACP deposit tx to the built-in ANCAP ACP tx viewer.
8. Reverse path runtime now also covers burn detection, ACP payout submit, and payout confirmation.

## Current operator flow

### 1. Preconditions
- Docker stack must be healthy.
- ACP node/RPC must be reachable.
- BSC RPC must be reachable.
- `bridge.env` must contain live values.
- Operator secrets must stay in `Sicret/bridge-bsc/` only.

### 2. Health checks
Run these before any pilot:
- `GET /api/v1/bridge/status`
- `GET /api/v1/bridge/reserve-summary`
- `POST /api/v1/system/jobs/tick`
- `POST /api/v1/bridge/admin/reconcile` (requires platform-admin bearer token + `X-Bridge-Operator-Secret`)
- open `/bridge/acp-bsc`

Expected:
- bridge enabled
- not paused
- `dry_run=false`
- reconciliation `ok=true`

### 3. Create intent
Authenticated user creates `ACP -> BSC` intent via UI or API.
Intent should start in `PENDING_DEPOSIT`.

### 4. Send ACP to reserve
User sends exact ACP amount to:
- `BRIDGE_RESERVE_ACP_ADDRESS`

Watcher should move operation:
- `PENDING_DEPOSIT -> CONFIRMED_ON_ACP`

### 5. Mint on BSC
Orchestrator submits BSC tx through `BridgeGateway.mintWrapped(...)`.
Operation moves to:
- `MINT_REQUESTED`

### 6. Confirm on BSC
BSC watcher reads receipt/logs and advances operation through:
- `MINT_REQUESTED -> MINTED_ON_BSC -> COMPLETED`

### 7. Verify outcome
Check all of:
- `/api/v1/bridge/status`
- reconciliation delta is zero
- operation result fields exposed by API
- BscScan tx exists and succeeded
- ACP deposit tx link opens under `/acp/tx/{txid}`
- recipient wallet `balanceOf(wACP)` increased

## Recommended next step

Run one more small controlled ACP -> BSC pilot.
Goal is repeatability, not just one successful pass.

In parallel, treat reverse rail truthfully:
- reverse runtime is already live enough to process real burn -> payout -> confirmation flows
- but it still needs replay/recovery hardening, broader validation, and possibly softer public wording if product does not want a plain `live` posture yet
- if docs should say `pending-rollout`, then runtime/API/UI must be changed back intentionally; right now they do not

## Notes
- Keep caps conservative until there is at least one more successful run.
- Do not commit mnemonics or private keys.
- Reverse direction `BSC -> ACP` is no longer just internal-only in runtime truth; docs must not pretend otherwise.
