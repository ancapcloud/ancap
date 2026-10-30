> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# ACP Economy Rails — Insurance + Arena

## Status

| Rail | Status | Settlement |
|------|--------|------------|
| Insurance desk | MVP | Premiums / claims denominated in **ACP** |
| Arena (prediction + house games) | MVP | Stakes / payouts in **ACP** |
| Real estate OTC + ownership certificates | **Already existed** | ACP desk + hashed contracts |
| Commodities (oil/gas/uranium/ores/…) | **Already existed** | OTC intake → ACP |

## Insurance

- Spec: RFC `economy/insurance` in `docs/rfc/service-catalog.md`
- API: `/v1/insurance/catalog`, `/quote`, `/policies`, `/policies/{id}/claims`, `/pools/{id}`
- UI: `/insurance`
- Coverage classes: wallet, bridge, cargo, real estate, commodities, health/travel stipend, NFC, cyber, fauna, space, **perimeter cleanup**, custom
- Migration: `067_insurance_arena`
- **Not a licensed insurer** — parametric desk prototype

## Arena (casino / bets)

- API: `/v1/arena/catalog`, `/arena/markets/{id}/bets`, `/arena/house/play`
- UI: `/arena`
- Prediction markets with YES/NO ACP pools
- House games: coinflip + dice with commit-reveal (`server_seed_hash` → reveal `server_seed`)
- House edge: 200 bps
- Compliance note on catalog — jurisdiction-restricted entertainment desk

## Already in platform (economics inventory)

See MASTER P5-XO / TITLE_OWNERSHIP_RAILS / EXCHANGE_OFFICE:

- Exchange office (ACP hub quotes/tickets)
- OTC metals, goods, antiques, **commodities**, **real estate**, space, IP
- Ownership certificates
- Bridge ACP↔wACP, Smart Pay, commerce/merchant, securities intake (partial)
- Auctions: Galaxy + FAUNA
- Marketplace AI workflows

## Next (recommended)

1. Wire insurance premiums/claims to real ACP ledger escrow (not hash-only)
2. Arena market resolve + payout distribution job
3. Ticket settle + auto rails for exchange office
4. Securities S2–S5 custody/haircut
5. Art auction vertical
