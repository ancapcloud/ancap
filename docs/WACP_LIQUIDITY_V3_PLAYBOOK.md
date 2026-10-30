> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# wACP Liquidity Strategy — PancakeSwap V3 (Stage A/B/C)

Status: active deployment playbook  
Network: BNB Smart Chain (chain ID 56)  
Primary market: wACP / USDT  
Primary venue: **PancakeSwap V3** (concentrated liquidity)  
Canonical fallback: PancakeSwap V2 pair `0xF391ca2bcBaB93Afa23326ebF1e35DB950841601`  
Future venue: PancakeSwap Infinity — only after sustained V3 volume

Operator tooling: [`scripts/wacp/`](../scripts/wacp/), reserve proof [`GET /api/v1/wacp/reserve-proof`](https://ancap.cloud/api/v1/wacp/reserve-proof).

## Executive policy

Maximize **useful liquidity per unit of scarce treasury capital** while preserving the ACP reserve invariant and supporting real ANCAP utility.

| Venue | Role | Capital policy |
|-------|------|----------------|
| V2 | Canonical micro-market / reference | Keep thin; do not aggressively deepen |
| V3 | Primary price discovery + concentrated LP | Main destination for new liquidity |
| OTC | Large orders, strategic buyers | When pool depth is insufficient |
| Infinity | Later optimization | No initial deployment |

Core rules:

- Never mint wACP directly into a DEX pool.
- Every mint must satisfy `minted_wACP ≤ ACP_reserve − reserve_buffer`.
- Flow: **Mint → Treasury → allocate → LP / MM / OTC**.
- Do not manufacture volume or wash trade.
- Success metrics: slippage, reserve health, platform ACP fees — not headline TVL or LP APR alone.

## Token configuration (verify on-chain)

| Field | Default (verify on BSC) |
|-------|-------------------------|
| `CHAIN_ID` | 56 |
| `wACP` | `0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402` |
| `wACP decimals` | **18** ([WACP.sol](../contracts/bridge-bsc/src/WACP.sol)) |
| Native ACP decimals | 8 |
| Bridge conversion | `wacp_wei = acp_smallest × 10^10` |
| `USDT` (BSC) | `0x55d398326f99059fF775485246999027B3197955` |
| V2 canonical pair | `0xF391ca2bcBaB93Afa23326ebF1e35DB950841601` |
| V3 pool (bootstrap) | `0xe626bd3ef516c4f784e5d5fb46e297d9c0d7f5e1` (`WACP_V3_POOL`) |
| Oracle on V3 | Only when `WACP_ORACLE_USE_V3=true` after quote smoke |
| Primary fee tier | 2500 (0.25%) unless live pool differs |
| Default range | ±20% around approved P0 |

**Token ordering:** read `token0()` / `token1()` from the pool. If wACP is token0, human price P = USDT per wACP and  
`P_raw = P × 10^decimals1 / 10^decimals0`.

## Reserve invariant (Gate A)

`M_max = max(0, R_ACP − B_reserve − M_existing)` in ACP smallest units.

Stage A mint: `M_A = min(approved_stage_A_cap, M_max, treasury_operational_need)`.

Scripts: `python scripts/wacp/compute_mint_envelope.py`, `python scripts/check_wacp_reserve_before_mint.py`.

## Stage A — inventory envelope

1. Read reserve proof.
2. Approve `M_A` (YAML: [`deploy/wacp-v3-stage-a.approval.example.yaml`](../deploy/wacp-v3-stage-a.approval.example.yaml)).
3. Mint to treasury only (never to pool).
4. Post-mint: re-check supply, reserve, treasury balance.

Default allocation fractions (treasury policy):

- V3: 35%
- MM: 35%
- OTC / redeem buffer: 30%

## Stage B — price and range

- Approve starting price `P0` (USDT per wACP) from V2 reference, recent trades, OTC — not one dust print.
- Default range ±20%; ±15% if volume is frequent and MM can rebalance; ±25% if volatility is high.
- Calculator: `python scripts/wacp/v3_deploy_calculator.py --help`

Modes: wACP-limited (`--w-v3`), USDT-limited (`--usdt-budget`), or balanced value target.

## Stage C — deployment

Preflight (read-only): `bash scripts/wacp/v3_preflight.sh`  
Checklist: [`scripts/wacp/DEPLOY_CHECKLIST.md`](../scripts/wacp/DEPLOY_CHECKLIST.md)

Human signs all on-chain txs (MetaMask / hardware wallet). Repo scripts do not hold LP keys.

Smoke: legitimate small buy/sell; record slippage for $100 / $250 / $500 (`scripts/wacp/quote_smoke.py`).

## V2 policy

Keep [V2 pool](https://pancakeswap.finance/liquidity/pool/bsc/0xF391ca2bcBaB93Afa23326ebF1e35DB950841601) live as reference. Do not route scarce USDT into large V2 positions while V3 is the primary venue.

## OTC routing

When order size exceeds **~25%** of estimated active V3 depth at current price, route to OTC / exchange office instead of the public pool.

- Web: [`/buy-acp`](https://ancap.cloud/buy-acp) copy + mobile Exchange tab tickets
- Mobile foundation: [`docs/mobile/EXCHANGE_OFFICE_FOUNDATION.md`](./mobile/EXCHANGE_OFFICE_FOUNDATION.md)

Platform fee recycling: [`docs/FINANCE_MODEL.md`](./FINANCE_MODEL.md) — wrap approved tranche → V3 top-up on a weekly operator cadence.  
Eligibility check: `python scripts/wacp/fee_recycle_check.py` (or jobs tick `wacp_liquidity.fee_recycle`). Do not recycle until platform ledger revenue meets `WACP_FEE_RECYCLE_MIN_REVENUE_ACP` (default 50 ACP). Spend path: [GOLDEN_PATH_ACP_SPEND.md](./GOLDEN_PATH_ACP_SPEND.md).

## Infinity evaluation gate (monitoring only)

Do not deploy Infinity until V3 metrics show sustained organic volume (7d/30d), fees, rebalance count, and acceptable slippage. The API jobs tick exposes `wacp_liquidity.infinity_gate` as **not eligible** until operator review.

## Infinity gate

No Infinity deployment until V3 shows sustained organic volume (7d/30d), measurable fees, and rebalance history. Hooks do not replace inventory or demand.

## Hard stops

Stop if: reserve invariant fails; unexpected token order; tickSpacing unverified; budgets exceeded; live pool price diverges materially from approved P0 without a new approval record.

## Related docs

- [pancakeswap-listing-playbook.md](./pancakeswap-listing-playbook.md)
- [pancakeswap-wacp-liquidity.md](./pancakeswap-wacp-liquidity.md) (legacy V2 context)
- [OFFICIAL_CONTRACT_ADDRESSES.md](./OFFICIAL_CONTRACT_ADDRESSES.md)
- [COINGECKO_LISTING_PLAYBOOK.md](./COINGECKO_LISTING_PLAYBOOK.md)
