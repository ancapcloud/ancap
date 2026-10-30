> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Bridge ratio cutover — 1 ACP ↔ 10 wACP (2026-10-04)

## What changed

- Code: `WACP_PER_ACP = 10` in `app/services/bridge_decimal.py` (scale `10^11`).
- New wraps: lock 1 ACP → mint **10 wACP**.
- Redeems: burn **10 wACP** → pay **1 ACP** (floor; wei dust remainder).
- Indicative ACP USD ≈ **10 ×** wACP DEX USD.
- Legacy completed forwards minted at 1:1 remain in DB; reconciliation accepts either ratio per op.

## Operator runbook (must human-sign)

Recipient for mint + treasury wACP (A+B):

`0x396351dF6420e6089dC67F4CBdDc717f34fFB2e4`

### Steps

1. **Pause bridge:** set `BRIDGE_RAIL_PAUSED=true` (or `bridge_rail_paused`) and restart API.
2. **Deploy** this code revision (API + frontend).
3. **Reserve check:**
   - `GET /api/v1/wacp/reserve-proof`
   - `python scripts/wacp/compute_mint_envelope.py --base-url https://api.ancap.cloud/v1`
4. Confirm Gate A / `reserve_health` acceptable under new liability (`ceil(wacp_supply / 10)` in ACP units).
5. **Unpause** only when healthy: `BRIDGE_RAIL_PAUSED=false`.
6. **Mint (A):** approved Gate A amount → mint wACP to treasury/gateway path per existing playbook — **never mint into a DEX pool**.
7. **Send (A+B):** transfer newly minted wACP **and** any existing treasury wACP balance to  
   `0x396351dF6420e6089dC67F4CBdDc717f34fFB2e4` (MetaMask / hardware).
8. Record tx hashes below.

### Live Gate A (post-deploy 2026-10-04 ~04:56Z UTC)

- `BRIDGE_RAIL_PAUSED=true` in `.env` + `Sicret/bridge-bsc/bridge.env`; API `bridge_rail_paused=true`
- `WACP_PER_ACP=10` in running API (`1 ACP → 10^19 wei wACP`)
- `reserve_health=paused`, `backing_ratio≈10.00028`, Gate A **pass**
- `max_additional_mint_acp_smallest=3211738770169793` (~**32,117,387.70 ACP** → up to ~**321,173,877 wACP** at 1:10)
- Recipient (A+B): `0x396351dF6420e6089dC67F4CBdDc717f34fFB2e4`
- Notes: stale reserve snapshot (~257 min); BSC totalSupply ≠ completed ops accounting — operator review before mint size
- **Agent does not sign.** Mint/transfer remain human-only.

### Inventory (2026-10-04 read-only)

| Address | Role | wACP |
|---------|------|------|
| `0x396351dF6420e6089dC67F4CBdDc717f34fFB2e4` | recipient = bridge_signer | **15,029,782.92** |
| `0x57c24FF77B23a82328cb88914D4FD4EEBd93321b` | gateway | 0 |
| `0xF391ca2…` / `0xe626…` | PCS V2 / V3 pools | LP only — not moved |
| — | totalSupply | ~35,685,986.34 |

Treasury consolidation target already holds the bridge-signer balance; no further ERC-20 transfer required for B. Mint A skipped (consolidation-only). LP inventory left in pools per policy.

### Tx log (fill after send)

| Step | Tx hash | Notes |
|------|---------|-------|
| Pause / deploy | n/a (env+compose) | paused=true; api+frontend recreated 2026-10-04 |
| Mint wACP | `67a66df8c07f5495598f4dcd12219b8cb4664a538cc90ea53deea8579e212416` | full Gate A ~321,173,877.02 wACP → 0x3963… |
| setCaps raise | `ae6a816d82937d722176de5f24cf84859404e60ff7c5d6824a04b10fb15b7149` | maxSingle/day = mint amount |
| setCaps restore | `7801157ed480115e15b8b33c4648eefef9549233cc6bfb12dff9b35aa3643dbf` | back to 30.24M wACP |
| Transfer to 0x3963…B2e4 | n/a (mint-to-self) | post-mint balance ~336,203,659.94 wACP |
| Unpause | env+compose recreate | after mint; Gate A headroom = 0 |

## Do not

- Sign txs from CI/agent without operator keys.
- Mint wACP into PancakeSwap pools.
- Set `WACP_ORACLE_USE_V3=true` as part of this cutover.
- Wash trade to inflate volume.

## Related

- [bridge-spec-v1.md](./bridge-spec-v1.md)
- [scripts/wacp/OPERATOR_SEND_CHECKLIST.md](../scripts/wacp/OPERATOR_SEND_CHECKLIST.md)
- Legal: `/legal/risk`, `/legal/market-data`, `/legal/welcome-grant`
