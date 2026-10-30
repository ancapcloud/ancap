> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# wACP V3 deployment checklist (human-signed txs)

## Bootstrap (done 2026-10-03)

- [x] V3 pool live (shallow): `0xe626bd3ef516c4f784e5d5fb46e297d9c0d7f5e1` (0.25% wACP/USDT)
- [x] Publish V3 URL on `/docs/wacp/pancakeswap`, `/markets`, `listings.json`
- [x] **Oracle stays on V2** (`WACP_ORACLE_USE_V3=false`)

## Stage A–C deepen (only after sustained platform spend)

1. [ ] `python scripts/check_wacp_reserve_before_mint.py`
2. [ ] `python scripts/wacp/compute_mint_envelope.py` — Gate A pass
3. [ ] Approval YAML filled (`deploy/wacp-v3-stage-a.approval.yaml`)
4. [ ] Mint wACP → **treasury only** (not pool); record tx hash
5. [ ] Post-mint reserve proof + `totalSupply` verify
6. [ ] `python scripts/wacp/v3_onchain_read.py --pool 0xe626bd3ef516c4f784e5d5fb46e297d9c0d7f5e1`
7. [ ] `python scripts/wacp/v3_deploy_calculator.py ...` — Gates B/C (±20% range)
8. [ ] `bash scripts/wacp/v3_preflight.sh`
9. [ ] Approve USDT + wACP spend; mint/increase V3 NFT position (partial LP only)
10. [ ] Record position id via `POST /v1/internal/wacp-liquidity/stages/.../positions`
11. [ ] `python scripts/wacp/quote_smoke.py` — $100 / $250 / $500 quotes (record slippage)
12. [ ] Only if smoke acceptable: set `WACP_ORACLE_USE_V3=true` and restart API
13. [ ] Re-publish docs if oracle source changed; confirm `oracle_meta().oracle_use_v3`

## Weekly fee recycle (parallel track)

1. [ ] Golden path spend producing fees — [docs/GOLDEN_PATH_ACP_SPEND.md](../../docs/GOLDEN_PATH_ACP_SPEND.md)
2. [ ] `python scripts/wacp/fee_recycle_check.py` → `eligible: true`
3. [ ] Approve fee tranche → wrap → Add Liquidity on same V3 pool (human-signed)
4. [ ] Never mint to pool; never wash trade

## Bridge ratio cutover 1↔10 (2026-10-04)

1. [ ] Follow [docs/BRIDGE_RATIO_CUTOVER_2026-10-04.md](../../docs/BRIDGE_RATIO_CUTOVER_2026-10-04.md)
2. [ ] Mint + send to `0x396351dF6420e6089dC67F4CBdDc717f34fFB2e4` — [OPERATOR_SEND_CHECKLIST.md](./OPERATOR_SEND_CHECKLIST.md)
