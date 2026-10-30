> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Exchange Office Foundation (iPhone / mobile)

ACP-hub multi-asset exchange desk for the ACP Wallet on iPhone (Expo).

## Model

**ACP is the accounting hub.** Every supported asset quotes:

1. **Into ACP** — sell asset → ACP (`usdt_trc20`, metals, goods, wACP redeem, fiat planned)
2. **From ACP** — ACP → asset (`wacp_bsc` mint, USDT indicative, fiat planned)
3. **Cross (all ↔ all)** — `FROM → ACP → TO` as a two-leg ticket (`rail=hub_cross`)

Settlement still uses existing rails; this layer unifies catalog, quotes, and tickets for the phone UX.

## Rails

| Rail | Assets | Status |
|------|--------|--------|
| `ledger` | ACP | live |
| `swap_desk` | USDT TRC-20 → ACP | live (manual desk) |
| `otc_metal` | Au/Ag/Pt/Pd → ACP | live (supervised) |
| `otc_goods` | physical goods → ACP | live (RFQ) |
| `otc_commodity` | oil, gas, uranium, timber, sand, stone, ore… → ACP | live (indicative unit rates) |
| GC/XRF assay proto | metal & gas purity peaks → indicative ACP | `/assay/gc/*` educational prototype |
| Title / intangibles | real estate, antiques, space, patents, recipes → ACP; ownership certificates | see `docs/mobile/TITLE_OWNERSHIP_RAILS.md` |
| `bridge` | ACP ↔ wACP BSC | live/beta by bridge flags |
| `dex_deep_link` | USDT BSC via Pancake / smart-pay | beta |
| OTC vs DEX | orders &gt; ~25% active V3 depth → ticket desk | see `docs/WACP_LIQUIDITY_V3_PLAYBOOK.md` |
| `fiat_onramp` | USD/EUR | planned placeholders |
| `hub_cross` | any listed cross pair | synthetic quote |

## API (`/v1`)

| Method | Path | Auth |
|--------|------|------|
| GET | `/mobile/exchange/catalog` | public |
| POST | `/mobile/exchange/quote` | public |
| GET | `/mobile/exchange/quotes/{quote_id}` | public (TTL cache) |
| POST | `/mobile/exchange/tickets` | user |
| GET | `/mobile/exchange/tickets` | user |
| GET | `/mobile/exchange/tickets/{id}` | user |
| POST | `/mobile/exchange/tickets/{id}/cancel` | user |
| POST | `/mobile/exchange/tickets/{id}/auth-settle` | user — opens/links swap desk / OTC / bridge handoff |
| POST | `/mobile/exchange/tickets/{id}/sync` | user — pull linked rail status |
| POST | `/mobile/exchange/tickets/{id}/complete` | platform admin — desk mark settled |

Creating an OTC metal/goods ticket also opens an `acp_otc_intake_orders` row and links `rail_ref_*`.

## Config

- `EXCHANGE_OFFICE_ENABLED` (default true)
- `EXCHANGE_QUOTE_TTL_SECONDS` (default 120)
- `EXCHANGE_ACP_TO_USDT_RATE` (optional; else `1/USDT_TRC20_TO_ACP_RATE`)
- `EXCHANGE_FIAT_ACP_RATES` (placeholder map)
- existing: `USDT_TRC20_TO_ACP_RATE`, `OTC_METAL_ACP_PER_GRAM`, bridge flags

## Mobile (Expo)

- Tab **Exchange** (`app/(tabs)/exchange.tsx`) — catalog chips, amount, purity/goods estimate, quote, **open ticket + auth-settle**, sync
- Client: `@ancap/acp-api-client` catalog/quote/ticket + `authSettleExchangeTicket` / `syncExchangeTicket`
- USDT TRC-20 → ACP auth-settle opens a linked `acp_swap_orders` row (`rail_ref_type=swap_order`); swap completion auto-closes the ticket

## Out of this foundation

- ACP payout hot-wallet automation (still desk-assisted / user-signed after deposit)
- Live metal market feed / DEX router signing
- Full operator UI beyond admin `POST .../complete`
- Fiat partner on-ramp execute
- Full in-app bridge intent create from Exchange tab (handoff text + sync only)

## Deposit watcher (shadow-first)

- Service: `app/services/swap_tron_deposit_watcher.py`
- Jobs tick key: `swap_deposit_watcher` (behind `FF_SWAP_DEPOSIT_WATCHER`, default off)
- Modes: `shadow` (audit only) · `pending_review (disabled by engineering audit until durable claim reconciliation)` (sets `tron_txid` + status; **no ACP transfer**)
- Checkpoint: `bridge_watcher_checkpoints.chain_key=tron_usdt_swap`
- Replay/idempotency: duplicate `tron_txid` / audit payload skipped; ambiguous same-amount orders logged, not claimed

## Files

- `app/schemas/exchange_office.py`
- `app/services/exchange_office.py`
- `app/services/exchange_ticket_settle.py`
- `app/api/routers/exchange_office.py`
- `app/db/models.py` → `AcpExchangeTicket`
- `alembic/versions/062_exchange_office.py`
- `ancap-mobile/apps/acp-wallet-expo/app/(tabs)/exchange.tsx`

Audit follow-up: watcher matching is observation-only. All non-shadow modes fail
closed. Queries paginate confirmed USDT with fixed filters, replay a 24-hour
overlap and leave the cursor unchanged on failed/incomplete fetches. This is not
exactly-once crediting: durable per-transfer identity, DB uniqueness/locking,
network-specific reconciliation and shared-address attribution remain gates.
Provider contract: https://developers.tron.network/reference/get-trc20-transaction-info-by-account-address
