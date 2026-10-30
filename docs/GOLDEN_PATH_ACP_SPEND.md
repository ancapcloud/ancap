> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Golden path — buy ACP → spend → treasury fee

Status: operator + product path (2026-10-03)  
Goal: prove **platform profit** from real ACP spend, not DEX APR.

## Path (web)

1. **Acquire ACP**
   - Bridge: [ancap.cloud/bridge](https://ancap.cloud/bridge) (1 ACP ↔ 10 wACP), or
   - Credits invoice / Stripe top-up: [/wallet/credits](https://ancap.cloud/wallet/credits), [/wallet/top-up](https://ancap.cloud/wallet/top-up), or
   - Mobile Exchange: USDT→ACP desk ticket (auth-settle).
2. **Spend on one paid surface** (pick one)
   - Workflows: [/ai/workflows](https://ancap.cloud/ai/workflows) — reserve → capture → `workflow_payment_capture`
   - Paid API: [/developers](https://ancap.cloud/developers) — `X-API-Key` usage charge
   - Marketplace order: [/marketplace](https://ancap.cloud/marketplace) — 5% `order_fee_percent`
   - Listing create: [/listings](https://ancap.cloud/listings) — 1% listing fee
3. **Verify fee landed**
   - Public: [GET /api/v1/treasury/status](https://ancap.cloud/api/v1/treasury/status) / UI [/treasury](https://ancap.cloud/treasury)
   - Expect `ledger.revenue_30d` (or breakdown) to move after the spend settles

## OTC / shallow pool rule

Bootstrap V3 pool: `0xe626bd3ef516c4f784e5d5fb46e297d9c0d7f5e1` (0.25%).  
If order size &gt; ~25% of active V3 depth → Exchange desk / OTC, not the public pool.  
Checkout oracle stays on **V2** until `WACP_ORACLE_USE_V3=true` after quote smoke.

## Success

- At least one non-grant spend produces a platform fee event
- Welcome grant (100 ACP) is **not** counted as revenue
- Next: weekly fee recycle check (`python scripts/wacp/fee_recycle_check.py`)

Related: [FINANCE_MODEL.md](./FINANCE_MODEL.md), [WACP_LIQUIDITY_V3_PLAYBOOK.md](./WACP_LIQUIDITY_V3_PLAYBOOK.md), [HELIO_MOONPAY_COMMERCE.md](./HELIO_MOONPAY_COMMERCE.md), [/buy-acp](https://ancap.cloud/buy-acp).
