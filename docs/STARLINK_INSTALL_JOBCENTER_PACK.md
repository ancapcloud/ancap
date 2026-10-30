> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Starlink Installation — Jobcenter presentation pack

Public URLs (after deploy):

| Surface | URL |
| --- | --- |
| Field services hub | https://ancap.cloud/field-services |
| Product (DE-first Starlink group) | https://ancap.cloud/field-services?group=starlink |
| Legacy Jobcenter URL (redirects) | https://ancap.cloud/starlink-install |
| Legal notice (Starlink) | https://ancap.cloud/legal/starlink-install |
| Legal notice (full hub) | https://ancap.cloud/legal/field-services |
| ACP / USDT ramp | https://ancap.cloud/buy-acp |
| Workflow checkout (standard) | https://ancap.cloud/ai/run/starlink-standard |
| Intake alias | https://ancap.cloud/ai/run/starlink-install-intake |

## What to show Jobcenter

1. Open `/starlink-install` (redirects to `/field-services?group=starlink`) — region chips **NRW / Deutschland / EU**, EUR price list, live ACP/wACP quote. Hub also lists IT / cameras / solar / **orbital AI** groups (`?group=space`, legal `/legal/space-ai-datacenter`).
2. Open `/legal/starlink-install` or `/legal/field-services` — honest framing: not Starlink Inc., not Telekom, not equipment reseller, not AVGS guarantee.
3. Optional: create a real ACP checkout on `starlink-standard` and keep the run receipt / proof center link.

## API smoke

```bash
curl -sS https://api.ancap.cloud/v1/starlink-install/catalog | head
curl -sS -X POST https://api.ancap.cloud/v1/starlink-install/quote \
  -H 'content-type: application/json' \
  -d '{"service_id":"starlink-standard","region":"de-nrw","payment_currency":"ACP"}'
```

## Honesty checklist

- [x] `official_reseller: false`
- [x] `jobcenter_guarantee: false`
- [x] Legal DE/EN/RU/UK copy states AVGS is agency-only
- [x] USDT is ramp via `/buy-acp`, not a fake parallel chain checkout
