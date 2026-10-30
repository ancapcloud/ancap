> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Compliance On-Ramp Matrix

> Status: draft for partner ramp go-live | Updated: 2026-06-10

ACP is a **utility / accounting asset** for workflow fees, API spend, merchant checkout, and platform credits. ANCAP is **not** a VASP; fiat and stablecoin on-ramps are provided by licensed partners.

Future **physical spend card / Apple Pay** is a separate licensed-issuer track. WebID (or equivalent) may supply KYC/KYB only — see [WEBID_KYC_AND_CARD_ISSUING_PATH.md](./WEBID_KYC_AND_CARD_ISSUING_PATH.md). Public waitlist: `/cards`.

## Asset messaging (MiCA-safe)

| Rule | Implementation |
|------|----------------|
| No profit promises | No price targets, APY, or guaranteed returns in product copy |
| Utility positioning | ACP credits settle paid execution; not marketed as an investment |
| Risk disclosure | `/compliance`, bridge docs, refund/dispute policies linked from checkout |

## On-ramp tiers

| Method | Provider class | KYC tier | Geo | Fee band | Status |
|--------|----------------|----------|-----|----------|--------|
| Card → credits | Stripe | Partner KYC | EU + supported Stripe regions | 2–5% | Live E2E verify `[~]` |
| USDC/USDT widget | MoonPay / Transak / Ramp | Partner KYC | Per partner matrix | 1–3% markup | Waitlist / compliance review |
| MoonPay Commerce checkout | Helio / MoonPay Commerce | Partner KYC | Per partner matrix | Partner schedule | Live widget `[~]` desk settle |
| wACP bridge | On-chain + reserve dashboard | Wallet self-custody | Global (user responsibility) | Network gas | Live with trust stub `/reserves` |
| Physical card / Apple Pay | Licensed BaaS/EMI + WebID KYC slot | Future WebID (or equiv.) | EU-first (planned) | TBD | Waitlist `/cards` — **ANCAP does not issue cards** |
| P2P / OTC | **Not offered** | — | — | — | Avoid |

## Geo & sanctions

- Block sanctioned jurisdictions per partner + Stripe rules
- Creator / merchant terms require truthful business description
- Admin can freeze payout requests pending review (existing payouts router)

## Before ramp go-live

1. Legal review of landing + `/buy-acp` partner copy
2. Publish reserve addresses on `/reserves` with contract verification links
3. Webhook audit trail for `merchant.payment.*` and top-up events
4. Incident contact on `/status`
