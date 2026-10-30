> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Bridge next steps (current state)

## Current state as of 2026-05-23

ACP -> BSC pilot rail is already working end-to-end.
Reverse BSC -> ACP payout path is also live in runtime, but still needs operational hardening and clearer public UX metadata.

### Confirmed working
- BSC contracts deployed on mainnet:
  - `WACP`: `0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402`
  - `BridgeGateway`: `0x57c24FF77B23a82328cb88914D4FD4EEBd93321b`
- Runtime is live:
  - `BRIDGE_RAIL_ENABLED=true`
  - `BRIDGE_RAIL_PAUSED=false`
  - `BRIDGE_DRY_RUN=false`
  - current verified runtime check exposed `confirmations_acp=1`
  - current verified runtime check exposed `confirmations_bsc=18`
- Recent live bridge status checks (local + prod) showed:
  - bridge enabled
  - not paused
  - reconciliation `delta_wacp_wei=0`
  - reverse completed liability tracked in reconciliation payload
  - public status currently exposes `redeem_available=true` and `redeem_mode="live"` when reserve health is not critical
- First real pilot intent completed:
  - operation id: `9320ecb4-c407-4ad2-8a4c-5c634b2259d8`
  - ACP deposit tx: `6c38d15141424819700e043fbd664826d37b0e0de14179a5f18906c2b3b4838e`
  - BSC mint tx: `a656c01758cd51f0fdd82627e6ac6ab5e7d24acbe4b694cd5e41cb1692ad8f8b`
  - final status: `COMPLETED`
- Reconciliation is clean in current checks:
  - `delta_wacp_wei=0`
- On-chain/public runtime notes currently include:
  - built-in ACP tx viewer support via `/acp/tx/{txid}`
  - reserve proof endpoint live
  - reverse payout path described by runtime as live with funded reserve and automated payout processing

## Important fixes already applied
- Intent creation API no longer fails on audit-event FK ordering.
- ACP watcher now matches real deposits into reserve address and moves intents from `PENDING_DEPOSIT` to `CONFIRMED_ON_ACP`.
- Orchestrator now submits live BSC mint transactions.
- BSC watcher now normalizes tx hash with `0x` before receipt lookup.
- Reverse watcher ingests `ReleaseRequested` burns.
- Reverse orchestrator can submit ACP payout and record `ACP_PAYOUT_SENT`.
- ACP watcher can confirm payout tx and move reverse operations to `COMPLETED`.
- Bridge API now exposes:
  - `acp_tx_hash`
  - `bsc_tx_hash_mint`
  - `deposit_ref_hex`
  - `bsc_log_index`
  - `version`
- Bridge UI intent list was updated to show those fields and link mint tx to BscScan.

## What to do next

### 1. Run second controlled ACP -> BSC pilot
Goal: prove repeatability, not just one lucky pass.

Suggested flow:
1. Create new authenticated bridge intent for a small amount.
2. Send matching ACP amount to reserve address.
3. Trigger or wait for jobs tick.
4. Confirm status path:
   - `PENDING_DEPOSIT`
   - `CONFIRMED_ON_ACP`
   - `MINT_REQUESTED`
   - `COMPLETED`
5. Verify:
   - bridge status counts
   - reconciliation remains `delta_wacp_wei=0`
   - wallet `wACP` balance increases as expected

### 2. Reverse rail: keep docs honest, then harden operations
Current status for `BSC -> ACP`:
- runtime/public API currently exposes it as live when reserve health is acceptable
- backend path is live enough to process:
  - burn detection
  - payout submission
  - payout confirmation
  - reconciliation accounting
- however, this does **not** mean the reverse rail is “finished” operationally

What remains before calling it mature:
- hardened replay/idempotent burn-event confirmation across production recovery scenarios
- broader production validation of ACP payout confirmation behavior
- more operator recovery rehearsal and incident docs
- explicit review of whether public UX copy should keep saying “live” or should move to a more nuanced “beta/live-with-limits” posture

Already available for reverse rail:
- `POST /api/v1/bridge/intents/bsc-to-acp`
- `POST /api/v1/bridge/quote/bsc-to-acp`
- public bridge status currently returns live redeem metadata
- reverse admin listing: `GET /api/v1/bridge/admin/reverse/operations`
- reverse liability summary: `GET /api/v1/bridge/admin/reverse/liability`
- manual confirmed-burn attachment: `POST /api/v1/bridge/admin/reverse/bind-burn`
- manual ACP payout attachment: `POST /api/v1/bridge/admin/reverse/bind-payout`
- payout resend preparation: `POST /api/v1/bridge/admin/reverse/requeue-payout`
- dispute escalation: `POST /api/v1/bridge/admin/reverse/mark-disputed`

Quote response exposes:
- `amount_wacp_wei`
- `acp_smallest_floor`
- `acp_amount_floor`
- `remainder_wacp_wei`
- `remainder_wacp`
- floor-rounding policy text

All bridge admin recovery endpoints require both platform-admin bearer auth and `X-Bridge-Operator-Secret`.

### 3. Keep docs aligned with runtime truth
Recommended:
- update `bridge-operator-runbook.md`
- update `bridge-pilot-mainnet.md`
- update `bridge-launch-checklist.md`
- update public wACP docs whenever status changes

Main thing: docs must not claim `pending-rollout` for reverse public status if runtime already exposes `redeem_mode="live"`.
If product wants a softer public story, runtime/API/UI should be changed to match that deliberately.

### 4. ACP explorer link support is wired
ACP deposit tx links no longer depend on a third-party explorer.
ANCAP now provides a built-in tx viewer at:
- `/acp/tx/{txid}`

Runtime/config default:
- `ACP_EXPLORER_TX_BASE=https://ancap.cloud/acp/tx`

That means bridge UI can link ACP deposit txs immediately, while still allowing override to an external ACP explorer later if one appears.

### 5. Finish reserve-proof maturity
Current public reserve proof endpoint is live.

**Shipped (2026-09-10, QOBLIB-style scorecard pass):**
- [x] Snapshot-backed backing ratio when latest snapshot is fresh (≤ 60 min)
- [x] Stale-data detection surfaced on public reserve-proof notes
- [x] Reconciliation mismatch transparency on public reserve-proof + scorecard
- [x] Public benchmark library: `docs/CRYPTO_BENCHMARK_LIBRARY.md` · `GET /v1/crypto/benchmark` · `/reserves`

Still needed:
- operator alerting on mismatch (beyond public notes)
- monthly transparency report export from scorecard history

### 6. Runtime balance helper is available
A small helper script now exists:
- `scripts/check_wacp_balance.py`

Example:
```bash
python scripts/check_wacp_balance.py --env-file Sicret/bridge-bsc/bridge.env --address 0x396351dF6420e6089dC67F4CBdDc717f34fFB2e4
```

It reads:
- `balanceOf(address)`
- `totalSupply()`
- `symbol()`
- `decimals()`

without depending on contract ABI files inside the API container.

### 7. Reverse path status: live in runtime, still needs hardening
Current success is no longer only ACP -> BSC mint rail.
Reverse direction is live in backend/runtime truth:
- BSC watcher ingests `ReleaseRequested`
- orchestrator submits ACP payout and moves ops to `ACP_PAYOUT_SENT`
- ACP watcher confirms payout tx and moves ops to `COMPLETED`
- reconciliation reflects completed reverse payouts without outstanding liability in the latest verified check

Remaining work after public/runtime enablement:
- production replay/idempotency hardening
- broader reconciliation and operational validation
- at least one additional controlled end-to-end reverse pilot for repeatability
- explicit finality-policy decision around current ACP confirmation settings
- possible refinement of public UX/status wording if “live” is too strong for the desired operator posture

## Recommended operator checks before any next pilot
- `GET /api/v1/bridge/status`
- `POST /api/v1/system/jobs/tick`
- `POST /api/v1/bridge/admin/reconcile`
- `GET /bridge/acp-bsc`
- confirm Docker containers are healthy
- confirm BSC gas wallet still has BNB

## Do not forget
- Keep secrets only in `Sicret/`
- Do not commit mnemonics/private keys
- Keep pilot caps conservative until at least one more successful run
- Do not silently let docs and runtime disagree about reverse-rail public status
