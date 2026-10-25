# Product retail pricing — 2026-10-25

Status: implemented on a review branch; not merged or deployed.
Baseline: `d7a4ec26d77e875848b9bcef5dae367ce4a624c1`.
Integrated current master `0ec351b` into the review branch; retained the QR campaign roadmap entries.

## Product logic

Explicit USD prices replace the historical magnitude rule (10,000 → $10,000,
10,001 → $10). Simple AI outputs cost $9–19; detailed preparation and analysis
briefs generally cost $29–59; multi-product bundles cost $39–119. These are
operator-selected introductory prices, not independently verified market prices
or a claim of measured provider margins. On-site service catalog faces are
retained pending the separate desk quote. Materials, travel and partner services
remain subject to the service quote.

AETERNA, legal, space, weather and venue workflows sell preparation briefs and
intake outputs. The price does not purchase medical procedures, manufactured
equipment, goods, legal representation or a space mission. Specialist project
pages and partner intent tariffs outside the workflow-store remain separate;
this change covers the workflow-store product catalogue and its checkout.

`app/services/catalog_prices.json` is the backend schedule; the frontend offline
copy is `frontend-app/src/lib/catalogPrices.json`. A regression test requires
identical schedules and complete SKU coverage. Unknown keyed SKUs fail rather
than silently inheriting a historical token face. Subscription period faces use
the same schedule. Bundle discounts are calculated from their actual components,
including repeat runs, instead of a separately maintained marketing percentage.

## Payment and display

Cards show USD retail prices. Live responses still carry the exact ACP quote;
payment previews and saved payment records retain token units. Offline fallback
shows USD only and never multiplies USD by the wACP bridge ratio to invent a quote.

ACP amount = USD / (10 × wACP USD oracle price), rounded up to 0.01 ACP.
The existing 1 ACP ↔ 10 wACP ratio and 10% wACP rail discount are retained.
Token supply, contracts, balances and the market price are not changed.
Existing oracle fallback/staleness/pinning policies are not redesigned here.
The explicit emergency pinned desk applies the current SKU price at its existing
$1 accounting spot. Historical catalog token faces remain internal compatibility
metadata; new run receipts record the actual USD retail pricing basis.

Credit packages are balances denominated in ACP: their ACP face is not a USD
service sticker. A 95 ACP top-up still costs 95 ACP and credits 100 ACP; wACP uses
the existing bridge ratio/rail discount. Existing saved runs are not repriced.

## Validation

- Market-data, pricing and direct API/run-construction regressions: 19 passed.
- Frontend suite: 67 existing tests passed; 3 new catalogue regressions passed.
- TypeScript check and production Next.js build passed (193 pages).
- Database-backed workflow-store integration tests: 9 skipped, database unavailable.
  Funded purchase/settlement is not claimed as verified.

## Retail schedule

| SKU | Deliverable | USD face |
| --- | --- | ---: |
| `token-listing-pack` | Token Listing Pack | $9 |
| `crypto-campaign-builder` | Crypto Campaign Builder | $19 |
| `telegram-growth-kit` | Telegram Growth Kit | $9 |
| `airdrop-bounty-builder` | Airdrop / Bounty Builder | $15 |
| `token-risk-report` | Token Risk Report | $15 |
| `token-launch-audit-pack` | Token Launch Audit Pack | $39 |
| `exchange-listing-submission-pack` | Exchange Listing Submission Pack | $49 |
| `kol-telegram-campaign-builder` | KOL / Telegram Campaign Builder | $39 |
| `token-risk-report-pro` | Token Risk Report Pro | $29 |
| `agent-api-readiness-pack` | Agent API Readiness Pack | $39 |
| `ai-iso-governance-readiness-pack` | AI / ISO Governance Readiness Pack | $59 |
| `aeterna-dna-wellness-report` | AETERNA DNA Wellness Report | $39 |
| `aeterna-longevity-panel-brief` | AETERNA Longevity Panel Brief | $29 |
| `aeterna-pigmentation-consult-brief` | AETERNA Pigmentation Consult Brief | $19 |
| `aeterna-telomere-panel-review` | AETERNA Telomere Panel Review | $29 |
| `aeterna-disease-risk-navigator` | AETERNA Disease Risk Navigator | $39 |
| `aeterna-molecular-aging-profile` | AETERNA Molecular Aging Profile (15 axes) | $49 |
| `aeterna-stem-cell-organ-print` | AETERNA Stem-Cell Organ Print | $49 |
| `aeterna-mrna-reprogramming-brief` | AETERNA Partial Reprogramming Consult (mRNA / LNP literacy) | $39 |
| `aeterna-vet-cat-cryo-restore` | AETERNA Feline Tissue Cryoconservator-Restorer | $29 |
| `aeterna-vet-regen-pod` | AETERNA Canine VET REGEN POD | $39 |
| `aeterna-vinci-light-chamber` | AETERNA Vinci Light Chamber | $19 |
| `aeterna-microwave-body-contouring` | AETERNA Microwave Body Contouring | $19 |
| `aeterna-biofusion-micromanipulation` | AETERNA BioFusion Micromanipulation Chamber | $49 |
| `aeterna-dpsc-biomaterial` | AETERNA Wisdom-Tooth DPSC Biomaterial | $29 |
| `aeterna-vascular-care-plus` | AETERNA Vascular Care+ | $19 |
| `aeterna-vascular-care` | AETERNA Vascular Care | $19 |
| `aeterna-transdermal-pistol` | AETERNA Needle-Free Transdermal Pistol | $19 |
| `aeterna-m-receptor-subscription` | AETERNA M-Receptor Delivery Subscription | $19 |
| `aeterna-oxygen-carrier` | AETERNA Artificial Oxygen Carrier | $39 |
| `aeterna-synthetic-blood-mamba` | AETERNA Synthetic Blood / Black Mamba Architecture | $49 |
| `aeterna-adhd-support` | AETERNA ADHD / СДВГ Support Brief | $19 |
| `aeterna-aurea-vita` | AUREA Vita — quality of life & longevity brief | $19 |
| `aeterna-down-syndrome-support` | AETERNA Down Syndrome Support Brief | $19 |
| `aeterna-substance-coding` | AETERNA Substance Coding Support Brief | $19 |
| `aeterna-pulmopure-subscription` | AETERNA PulmoPure Lung-Care Subscription | $19 |
| `aeterna-installation-project` | AETERNA Installation Project (Neonatal Nutrition + Hyperbaric) | $39 |
| `aeterna-dna-pheromone-perfume` | AETERNA DNA-Matched Pheromone Perfume (1 Bottle) | $29 |
| `counsel-jurisdiction-match` | Worldwide Legal Counsel — Jurisdiction Match | $19 |
| `counsel-entity-setup` | Worldwide Legal Counsel — Entity / Incorporation Brief | $39 |
| `counsel-contract-review` | Worldwide Legal Counsel — Contract Review Brief | $29 |
| `counsel-crypto-assets` | Worldwide Legal Counsel — Crypto / Digital Assets Match | $39 |
| `starlink-install-intake` | Starlink Installation — Standard Intake (NRW / DE) | $153 |
| `starlink-standard` | Starlink Installation — Standard | $153 |
| `starlink-roof` | Starlink Installation — Roof / Wall Mount | $203 |
| `starlink-business` | Starlink Installation — Business | $303 |
| `starlink-network` | Starlink Installation — Network / Wi-Fi | $53 |
| `starlink-mobile` | Starlink Installation — Mobile / RV | $183 |
| `starlink-relocate` | Starlink Installation — Relocation | $178 |
| `starlink-troubleshoot` | Starlink Installation — Troubleshooting | $83 |
| `it-pc-setup` | Field services — PC / laptop setup | $123 |
| `it-device-repair` | Field services — Device upgrade / repair visit | $93 |
| `it-network-home` | Field services — Home / small-office network | $83 |
| `it-maintenance-visit` | Field services — IT maintenance visit | $73 |
| `cam-cctv-install` | Field services — CCTV camera install | $183 |
| `cam-nvr-config` | Field services — NVR / recorder configuration | $103 |
| `cam-maintenance` | Field services — CCTV maintenance | $78 |
| `solar-balcony-install` | Field services — Balcony PV mount coordination | $253 |
| `solar-panel-service` | Field services — Solar panel service visit | $123 |
| `panel-other-mount` | Field services — Other panel mount coordination | $153 |
| `space-ai-orbit-intake` | Field services — Orbital AI data-center placement (LEO / MEO) | $49 |
| `space-ai-beyond-orbit` | Field services — Beyond-orbit AI data-center placement | $79 |
| `space-ai-superintel-architecture` | Field services — Orbital superintelligence architecture brief | $99 |
| `stardust-extreme-weather-monitor` | Stardust Extreme Weather Worldwide Monitor | $19 |
| `stardust-disaster-early-warning` | Stardust Disaster Early-Warning Coordination | $29 |
| `stardust-weather-control-global` | Stardust Global Weather-Control Partner Brief | $49 |
| `stardust-weather-control-subscription` | Stardust Worldwide Weather-Control Subscription | $29 |
| `market-direction-brief` | Market Direction Brief | $9 |
| `commodity-price-outlook` | Commodity Price Outlook | $9 |
| `crypto-quote-momentum-scan` | Crypto Quote Momentum Scan | $9 |
| `markets-ai-radar-pro` | Markets AI Radar Pro | $29 |
| `entertainment-tesla-coil-party` | Tesla Coil Party Desk Brief | $29 |
| `antique-fire-restore` | Antique Fire Restore Desk Brief | $29 |
| `launch-pack` | ANCAP Crypto Launch Pack | $49 |
| `growth-pack` | ANCAP Growth Pack | $59 |
| `concierge-pack` | ANCAP Concierge Pack | $59 |
| `pro-launch-pack` | ANCAP Pro Launch Pack | $119 |
| `agent-commerce-pack` | ANCAP Agent Commerce Pack | $79 |
| `compliance-pack` | MiCA Readiness Pack | $109 |
| `growth-pro-pack` | 7-Day Campaign Pack | $79 |
| `merchant-qr-pack` | Payment QR Setup Pack | $49 |
| `aeterna-longevity-pack` | AETERNA Longevity Pack | $89 |
| `markets-intel-pack` | Markets Intel Pack | $39 |
