> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Public placement matrix — wACP / ANCAP

Living checklist of where Wrapped ACP can appear **without** paid gatekeepers.
Machine-readable twin: <https://ancap.cloud/listings.json> · UI: <https://ancap.cloud/markets>

## Official identity (paste this everywhere)

| Field | Value |
| --- | --- |
| Name | Wrapped ACP |
| Symbol | **wACP** (not ACP, not ANCAP) |
| Chain | BNB Smart Chain (56) |
| Contract | `0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402` |
| Pool wACP/USDT V2 | `0xF391ca2bcBaB93Afa23326ebF1e35DB950841601` |
| Gateway | `0x57c24FF77B23a82328cb88914D4FD4EEBd93321b` |
| Logo | <https://ancap.cloud/wacp-logo.png> |
| Token list | <https://ancap.cloud/tokenlist.json> |
| Website | <https://ancap.cloud> |
| Docs | <https://ancap.cloud/docs/wacp> |

**Naming trap:** CoinGecko already has ticker **ACP** = Arena Of Faith (unrelated). Always use **wACP**.

---

## Live now (verified)

| Surface | Fee | Link | Notes |
| --- | --- | --- | --- |
| PancakeSwap | Free | [swap](https://pancakeswap.finance/swap?inputCurrency=0x55d398326f99059fF775485246999027B3197955&outputCurrency=0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402) | Trade by CA |
| DexTools | Free index | [pair](https://www.dextools.io/app/en/bnb/pair-explorer/0xf391ca2bcbab93afa23326ebf1e35db950841601) | Use for “CoinGecko or DexTools” promo forms |
| GeckoTerminal | Free | [pool](https://www.geckoterminal.com/bsc/pools/0xf391ca2bcbab93afa23326ebf1e35db950841601) | CoinGecko DEX arm; `coingecko_coin_id` still null |
| BscScan | Free | [token](https://bscscan.com/token/0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402) | Explorer |
| GoPlus | Free | [security](https://gopluslabs.io/token-security/56/0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402) | `is_in_dex=1`, taxes 0 |
| ANCAP token list | Free | [/tokenlist.json](https://ancap.cloud/tokenlist.json) | Import in wallets |
| ANCAP markets | Free | [/markets](https://ancap.cloud/markets) | First-party hub |
| PooCoin / DexView | Free | open by CA | SPA charts; may need refresh |

---

## Blocked / pending (not solvable by form spam)

| Surface | Why blocked | Next action |
| --- | --- | --- |
| DexScreener | API `pairs:null` — dust / no recent volume | Seed liquidity + 2–3 swaps |
| CoinGecko Active | Dust pool (~$1) | Same + Partners form as **wACP** |
| DexTools Update Info | Paid (~$195) | Optional branding only |
| DexScreener Enhanced Info | Paid | Optional |
| PancakeSwap default list | Invite-only | Not open to cold PRs |
| Trust Wallet Assets | Maintainer merge | Pack ready: `docs/listings/trustwallet-smartchain-wacp/` |
| CoinMarketCap | Similar to CoinGecko | After real volume |
| CEX listings | Commercial | Out of scope |

---

## Operator recipe to unlock DexScreener + CoinGecko

1. Add meaningful `wACP/USDT` liquidity on PancakeSwap V2 (thousands USD, not $1).
2. Execute a few round-trip swaps.
3. Confirm DexScreener API returns the pair.
4. Submit CoinGecko Partners form using [COINGECKO_LISTING_PLAYBOOK.md](../COINGECKO_LISTING_PLAYBOOK.md).
5. Set `COINGECKO_WACP_COIN_ID` after approval.

There is **no** permissionless way to force CoinGecko/CMC/DexScreener visibility without on-chain activity.
