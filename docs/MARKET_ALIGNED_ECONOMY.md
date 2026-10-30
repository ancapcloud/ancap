> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Market-aligned ACP / wACP economy

Status: **live on ancap.cloud** after deploy of this doc's companion code.

## Doctrine

- Bridge (cutover 2026-10-04): **1 ACP ↔ 10 wACP**.
- wACP USD spot: official PancakeSwap V2 pool via GeckoTerminal  
  `0xf391ca2bcbab93afa23326ebf1e35db950841601`  
  https://www.geckoterminal.com/bsc/pools/0xf391ca2bcbab93afa23326ebf1e35db950841601
- ACP USD spot ≈ **10 × wACP USD** (bridge ratio).
- Catalog sells **pleasant USD stickers**; checkout charges **ACP = ceil(usd_sticker / (10 × wacp_usd))**.
- High historical ACP faces (&gt; 10_000) scale to USD by `/1000` (e.g. 1_000_000 → $1000).

## Oracle

- Service: `app/services/market_economy.py`
- Endpoint preference: official pool `base_token_price_usd`, then token price, then stale cache, then soft fallback.
- Clamp: `WACP_ORACLE_MIN_USD` / `WACP_ORACLE_MAX_USD`
- Desk USDT→ACP: `1 / (10 × wacp_usd)` unless `WACP_ORACLE_PIN_DESK=true` (then `USDT_TRC20_TO_ACP_RATE`)

## Earnings

| Rail | Take |
|------|------|
| Marketplace orders | `ORDER_FEE_PERCENT` default **10%** |
| Agent runs | `RUN_FEE_PERCENT` default **10%** |
| Workflow capture | `WORKFLOW_PLATFORM_FEE_PERCENT` default **10%** (stamped on receipt) |
| Listings | `LISTING_FEE_PERCENT` default **1%** |

Platform ledger + project treasury see captured fees. Thin DEX liquidity (~tens of USD) makes the spot noisy — deepen LP for stable retail UX.

## UI

- Sitewide `MarketRateBar` in `Navigation` (60s poll)
- Home ticker uses micro USD formatting (up to 8 decimals)
- Pricing / workflow catalog prefer `$sticker` with `≈ ACP` secondary

## Legal

See `/legal/market-data`. Spots are indicative; not investment advice.
