> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Bridge launch checklist

## Goal

Bring ACP -> BSC custodial rail to a safe live pilot state and keep all public/operator surfaces aligned with real runtime status.

## Current reality

This checklist is now mostly a verification checklist, not a theoretical launch plan.
The rail already completed one real pilot successfully on 2026-05-04.

### Live state already confirmed
- BSC contracts deployed
- API/runtime wired
- ACP deposit detection working
- live BSC mint submission working
- BSC receipt confirmation working
- reconciliation clean
- first pilot operation completed

## Contracts
- `WACP`: `0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402`
- `BridgeGateway`: `0x57c24FF77B23a82328cb88914D4FD4EEBd93321b`

## Runtime checklist

### 1. Environment
Confirm `Sicret/bridge-bsc/bridge.env` contains correct live values:
- `BRIDGE_RAIL_ENABLED=true`
- `BRIDGE_RAIL_PAUSED=false`
- `BRIDGE_DRY_RUN=false`
- `BRIDGE_BSC_RPC_URL`
- `BRIDGE_WACP_CONTRACT`
- `BRIDGE_GATEWAY_CONTRACT`
- `BRIDGE_RESERVE_ACP_ADDRESS`
- `BRIDGE_OPERATOR_SECRET`
- `BRIDGE_BSC_PRIVATE_KEY`
- `BRIDGE_ACP_CONFIRMATIONS=1` for the current single-node ACP runtime

### 2. Docker/runtime
Confirm containers are healthy:
- `ancap-frontend-1`
- `ancap-api-1`
- `ancap-proxy-1`
- `ancap-postgres-1`

### 3. API health
Confirm:
- `GET /api/v1/system/health`
- `GET /api/v1/bridge/status`
- `GET /api/v1/bridge/reserve-summary`
- `POST /api/v1/system/jobs/tick`
- `POST /api/v1/bridge/admin/reconcile` (requires platform-admin bearer token + `X-Bridge-Operator-Secret`)

Expected bridge status:
- enabled = true
- paused = false
- dry_run = false
- confirmations_acp = 1 for the current single-node ACP runtime

### 4. UI health
Confirm page loads:
- `/bridge/acp-bsc`

Intent list should be able to show:
- status
- direction
- ACP tx hash
- BSC mint tx hash
- BSC burn tx hash when present
- deposit ref
- BSC log index
- version
- reverse remainder field for `BSC -> ACP`
- built-in ACP tx link
- BscScan link for BSC tx

Redeem preview should also work:
- `POST /api/v1/bridge/quote/bsc-to-acp`
- UI should show floor ACP payout and retained remainder before submit

### 5. Pilot transaction flow
For a fresh small pilot:
1. create intent
2. send exact ACP amount to reserve address
3. run or wait for tick
4. verify status transitions:
   - `PENDING_DEPOSIT`
   - `CONFIRMED_ON_ACP`
   - `MINT_REQUESTED`
   - `COMPLETED`

### 6. Reconciliation
After pilot completion, confirm:
- `ok=true`
- `delta_wacp_wei=0`

### 7. On-chain verification
Confirm at least one of:
- BscScan receipt success for mint tx
- `balanceOf(recipient)` increased
- `totalSupply()` changed as expected

## First successful pilot reference
- operation id: `9320ecb4-c407-4ad2-8a4c-5c634b2259d8`
- ACP tx: `6c38d15141424819700e043fbd664826d37b0e0de14179a5f18906c2b3b4838e`
- BSC tx: `a656c01758cd51f0fdd82627e6ac6ab5e7d24acbe4b694cd5e41cb1692ad8f8b`
- result: `COMPLETED`
- minted balance verified: `1 wACP`

## Known important fixes
- intent creation flush ordering fixed
- ACP watcher implemented for real reserve deposit pickup
- `BRIDGE_ACP_CONFIRMATIONS` passed into Docker runtime
- live BSC mint path implemented
- BSC watcher tx hash normalization fixed
- API exposes result tx fields
- frontend intent list updated to show result fields
- built-in ACP tx viewer added at `/acp/tx/{txid}`

## Safety reminders
- Keep all secrets only in `Sicret/`
- Never commit mnemonics/private keys
- Keep pilot caps conservative
- Bridge admin endpoints are dual-gated: they require both platform-admin bearer auth and `X-Bridge-Operator-Secret`
- If `PLATFORM_ADMIN_USER_IDS` is empty, bridge admin endpoints must fail closed with `503 Platform admin access is not configured`
- Reverse rail is now live, but do not assume that means it is fully hardened for replay/recovery edge-cases
- Public status for reverse must always reflect the real runtime state; do not reintroduce stale `pending-rollout` copy while payouts are actually live
- Reserve proof is public and live; keep improving snapshot/backing observability without lying about current availability
- For the current single-node ACP runtime, `BRIDGE_ACP_CONFIRMATIONS=1` is intentional and should not be changed casually
