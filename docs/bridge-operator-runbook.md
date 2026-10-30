> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Bridge operator runbook

## Scope

This runbook is for the live ACP -> BSC custodial rail and the live-but-still-hardening `BSC -> ACP` reverse rail.

It describes the operator reality after the first successful mainnet pilot on 2026-05-04.

## Current live deployment

### Contracts
- `WACP`: `0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402`
- `BridgeGateway`: `0x57c24FF77B23a82328cb88914D4FD4EEBd93321b`

### Runtime state
- `BRIDGE_RAIL_ENABLED=true`
- `BRIDGE_RAIL_PAUSED=false`
- `BRIDGE_DRY_RUN=false`
- `BRIDGE_ACP_CONFIRMATIONS=1` in the current single-node ACP runtime

### Pilot proof
First real pilot already completed successfully:
- operation id: `9320ecb4-c407-4ad2-8a4c-5c634b2259d8`
- ACP tx: `6c38d15141424819700e043fbd664826d37b0e0de14179a5f18906c2b3b4838e`
- BSC mint tx: `a656c01758cd51f0fdd82627e6ac6ab5e7d24acbe4b694cd5e41cb1692ad8f8b`
- final status: `COMPLETED`

## Secrets and files

Keep secrets only in:
- `Sicret/bridge-bsc/bridge.env`
- `Sicret/bridge-bsc/bsc-operator-private-key.txt`
- `Sicret/bridge-bsc/acp-reserve-mnemonic.txt`
- `Sicret/bridge-bsc/acp-release-hot-mnemonic.txt`

Do not commit any of the above.

## Bridge admin auth model

All `/api/v1/bridge/admin/*` endpoints are now dual-gated.
They require both:
- authenticated platform-admin user access (`PLATFORM_ADMIN_USER_IDS` allowlist)
- `X-Bridge-Operator-Secret`

Fail-closed behavior:
- if platform-admin allowlist is unset/empty -> `503 Platform admin access is not configured`
- if authenticated user is not allowlisted -> `403 Platform admin required`
- if bridge operator secret is missing/wrong -> `403 Invalid bridge operator secret`

This includes:
- `POST /api/v1/bridge/admin/reconcile`
- `POST /api/v1/bridge/admin/allowlist`
- `GET /api/v1/bridge/admin/reverse/operations`
- `GET /api/v1/bridge/admin/reverse/liability`
- `POST /api/v1/bridge/admin/reverse/bind-burn`
- `POST /api/v1/bridge/admin/reverse/bind-payout`
- `POST /api/v1/bridge/admin/reverse/requeue-payout`
- `POST /api/v1/bridge/admin/reverse/mark-disputed`

## Standard health check

Before any new pilot or after any redeploy, verify all of this.

### Docker
- `ancap-frontend-1` up
- `ancap-api-1` healthy
- `ancap-proxy-1` up
- `ancap-postgres-1` healthy

### API
- `GET /api/v1/system/health`
- `GET /api/v1/bridge/status`
- `GET /api/v1/bridge/reserve-summary`
- `POST /api/v1/system/jobs/tick`
- `POST /api/v1/bridge/admin/reconcile` (requires platform-admin bearer token + `X-Bridge-Operator-Secret`)

Expected:
- bridge enabled
- not paused
- `dry_run=false`
- `confirmations_acp=1` in the current single-node ACP runtime
- reconciliation `ok=true`

### UI
- open `/bridge/acp-bsc`
- authenticated user should be able to see intent rows
- result rows may include:
  - `direction`
  - `acp_tx_hash`
  - `bsc_tx_hash_mint`
  - `bsc_tx_hash_burn`
  - `remainder_wacp_wei`
  - `deposit_ref_hex`
  - `bsc_log_index`
  - `version`
  - built-in ACP tx link
  - BscScan tx link
- reverse preview should work via:
  - `POST /api/v1/bridge/quote/bsc-to-acp`

## Normal ACP -> BSC operator flow

### 1. Create intent
User creates an authenticated intent via UI/API.
Expected initial state:
- `PENDING_DEPOSIT`

### 2. Wait for exact ACP deposit
User sends exact ACP amount to reserve address.
Watcher matches incoming reserve deposit.
Expected transition:
- `PENDING_DEPOSIT -> CONFIRMED_ON_ACP`

### 3. Mint submission on BSC
Orchestrator submits live BSC mint transaction via `BridgeGateway.mintWrapped(...)`.
Expected transition:
- `CONFIRMED_ON_ACP -> MINT_REQUESTED`

Recorded fields should include:
- `bsc_tx_hash_mint`
- `deposit_ref_hex`

### 4. BSC confirmation
BSC watcher fetches receipt/logs and finalizes operation.
Expected transitions:
- `MINT_REQUESTED -> MINTED_ON_BSC`
- `MINTED_ON_BSC -> COMPLETED`

## Verification after completion

Confirm all of:
1. operation shows `COMPLETED`
2. BSC mint tx exists and has receipt success
3. reconciliation still returns `delta_wacp_wei=0`
4. recipient wallet `wACP` balance increased
5. audit trail contains submit + confirm + completion events

## Known important implementation details

### ACP confirmations
Runtime target for the currently deployed single-node ACP environment is:
- `BRIDGE_ACP_CONFIRMATIONS=1`

This must be set both in env and actually passed through Docker compose. Do not raise it blindly unless block progression and multi-node finality policy are verified.

### BSC tx hash normalization
`bsc_tx_hash_mint` may be stored without `0x`.
Watcher must normalize hash before `eth_getTransactionReceipt`.
This bug already happened once and was fixed.

### API visibility
Operation API now exposes:
- `acp_tx_hash`
- `bsc_tx_hash_mint`
- `deposit_ref_hex`
- `bsc_log_index`
- `version`

Built-in ACP explorer path is:
- `/acp/tx/{txid}`

Runtime default is:
- `ACP_EXPLORER_TX_BASE=https://ancap.cloud/acp/tx`

This means most operator checks no longer require raw SQL.

### Balance helper
A lightweight runtime helper is available:
- `scripts/check_wacp_balance.py`

Example:
```bash
python scripts/check_wacp_balance.py --env-file Sicret/bridge-bsc/bridge.env --address 0x396351dF6420e6089dC67F4CBdDc717f34fFB2e4
```

Use it when you want a direct check of:
- wallet `wACP` balance
- token `totalSupply`

without depending on ABI files inside the API container.

## Failure playbook

### If intent stays in `PENDING_DEPOSIT`
Check:
- ACP tx really went to reserve address
- exact amount matches intent (watcher matches `received_units` to `amount_acp_smallest`)
- confirmations reached the currently deployed ACP policy (`1` in this single-node runtime)
- ACP watcher tick ran successfully (incremental `acp_deposit` scan; after deploy catch-up is ~400 blocks/tick from height 1)
- ACP RPC reachable from API container
- if deposit txid is known: `POST /v1/bridge/admin/forward/bind-deposit` with operator secret

Intent alone does nothing — user must send the exact ACP amount to the reserve address after creating the intent.

### If intent stays in `CONFIRMED_ON_ACP`
Check:
- live signer key present
- `BRIDGE_DRY_RUN=false`
- BSC RPC reachable
- gateway/wACP contract addresses correct
- orchestrator tick actually ran

### If reverse rail fails at `BURN_CONFIRMED`
Check in this exact order:
- `BRIDGE_RAIL_ENABLED=true`
- `BRIDGE_DRY_RUN=false`
- `ACP_HOT_MNEMONIC_FILE` inside the API runtime points to the bridge-scoped secret, not a generic project wallet path
- derived signer address from current ACP hot mnemonic exactly matches `BRIDGE_RESERVE_ACP_ADDRESS`
- reserve address actually has spendable ACP for the payout amount + fee
- ACP RPC and `walletd` are both healthy from inside the API container

Operator rule:
- if derived signer != configured reserve address, reverse rail is NO-GO even if reserve-proof and public status look healthy
- do not flip `BSC -> ACP` live until signer/address identity is proven in the running container

### If intent stays in `MINT_REQUESTED`
Check:
- `bsc_tx_hash_mint` exists
- tx exists on-chain
- receipt status is success
- watcher receipt lookup is using normalized `0x` hash
- BSC confirmations threshold reached

### If reconciliation fails
Check:
- minted total on BSC
- locked ACP sum in operations
- whether a tx succeeded on-chain but watcher/API state is lagging

## Reverse rail current state

What is already real:
- reverse intent registration
- floor/remainder quantization according to spec
- mixed-direction ops listing
- UI redeem request form
- UI/API quote preview for floor payout and remainder transparency

What is not fully matured yet:
- production-proven replay/idempotency handling for reverse recovery cases
- broader production ops validation
- multi-node / higher-finality ACP confirmation policy beyond the current single-node runtime

What now exists in backend code:
- burn-event watcher confirmation via `ReleaseRequested`
- ACP payout submission worker path
- reverse completion through ACP watcher confirmation
- operator-safe reverse recovery endpoints protected by dual-gate access:
  - platform-admin bearer auth
  - `X-Bridge-Operator-Secret`

Current reverse admin endpoints:
- `GET /api/v1/bridge/admin/reverse/operations`
- `GET /api/v1/bridge/admin/reverse/liability`
- `POST /api/v1/bridge/admin/reverse/bind-burn`
- `POST /api/v1/bridge/admin/reverse/bind-payout`
- `POST /api/v1/bridge/admin/reverse/requeue-payout`
- `POST /api/v1/bridge/admin/reverse/mark-disputed`

All of the above require both platform-admin bearer auth and `X-Bridge-Operator-Secret`.

Operator rule:
- reverse rail may be presented as live only when signer identity, payout execution, watcher confirmation, and reconciliation are all proven in the running container
- current production state satisfies that requirement
- for this current ACP runtime (`https://acp1.ancap.cloud/rpc`), `BRIDGE_ACP_CONFIRMATIONS=1` is the truthful policy because chain height is effectively static/single-node in this environment; do not raise it blindly without real block progression

### Recovery usage notes
- Use `bind-burn` only when a real `ReleaseRequested` event exists but watcher matching needs manual repair.
- Use `bind-payout` only when a real ACP payout tx was sent outside the normal orchestrator path and must be attached back to the operation.
- Use `requeue-payout` when an operation is stuck in `ACP_PAYOUT_SENT` but the recorded ACP tx should be abandoned and resent.
- Use `mark-disputed` when amounts, destination, or chain evidence conflict and human review is required.
- Do not mark reverse ops `COMPLETED` manually here; final completion still belongs to ACP watcher confirmation.

## Next recommended step

Run one more small controlled round-trip to prove repeatability in both directions.
In parallel, harden reverse replay/idempotency handling and decide whether ACP should remain a single-node runtime policy (`BRIDGE_ACP_CONFIRMATIONS=1`) or move to a higher-confirmation multi-node setup.

## Non-goals

This runbook does not mean reverse bridge direction is production-ready.
`BSC -> ACP` burn/release path still needs its own operational validation.
