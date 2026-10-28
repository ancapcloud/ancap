# ANCAP Card roadmap — 2026-10-28

Status: concept / waitlist, not a launched card. Germany/EEA is the proposed first market. This track stays behind paid-workflow revenue validation.

The [complete supplied brief](ANCAP_CARD_SOURCE_BRIEF_2026-10-28.md) contains all research, calculations, product copy and implementation requirements. It is retained verbatim. Market prices, legal statements and provider permissions are supplied research, not independently verified or approved ANCAP terms; revalidate before decisions.

## Local implementation

- [x] Replace home/projects sales calculator with ANCAP Card information in EN/RU/UK/DE/zh-Hant using the existing language provider.
- [x] Show card concept, unavailable status, partner/Apple Pay uncertainty, bounded pilot, reward distinctions, risks and links to existing waitlist. No financial functionality added.
- [ ] Full /cards page and form localisation, FAQ and expanded approved content from the source brief.
- [ ] Browser acceptance at 360px and desktop; production publication remains separately authorised.

## Partner and product gates

- [ ] Validate demand through free waitlist/interviews without taking money or promising issuance/date.
- [ ] Request current offers from Striga, Monavate/managed programme and Rain; none is a confirmed partner. Verify issuer/legal entity, Germany/EEA coverage, current MiCA/CASP permissions, responsibilities and privacy/tax requirements. Historical VASP wording is insufficient evidence.
- [ ] Confirm successful/failed authorisation fees, card/wallet charges, refunds/disputes, minimums, prefunding, collateral, liquidity, interchange share, conversion/FX margin, Apple Pay/tokenisation, termination and customer portability.
- [ ] Approve EUR settlement, virtual card first, phone payment after tokenisation approval, physical card later; no compulsory ACP staking, lending or crypto collateral.
- [ ] Approve supported assets in writing. ACP/wACP/sACP/workflow credits stay distinct; direct ACP spending requires liquidity, slippage/execution rules and partner consent. No fixed ACP/EUR rate or stablecoin interest promise.

## Rewards and economics — research assumptions only

- [ ] Fund and approve welcome concept: 1% on first €500 eligible purchases, maximum €5 in 30 days after activation. Promotion inactive; no current rewards.
- [ ] Review referrals: €5 service bonuses per party after €100 settled eligible purchases, unique verified users, no self-referrals, refund checks.
- [ ] Review activity bonus: €5 after €300 monthly purchases, maximum three pilot months. Proposed service discounts: up to 50% of eligible order, 90-day expiry, no withdrawal/transfer/cash or ACP exchange; reserve 100% face value.
- [ ] Contract merchant offers before publishing; illustrative 5% funding / 4% customer / 1% ANCAP split is not a quote or universal reward. No stacking by default.
- [ ] Keep Start €0, Plus €9.90/0.5%/€5 cap and Pro €19.90/1%/€15 cap as internal research, not public subscriptions. Permanent cashback requires confirmed funding and full costs.
- [ ] Revalidate supplied €6.95 known monthly cost at €1,000 spend/26 POS authorisations; support, fraud, disputes, liquidity, tokenisation, engineering, acquisition and platform minimums excluded. Interchange/conversion revenue remains zero until contracted.
- [ ] Recheck VAT treatment: 19% is a modelling assumption. At €1,000 spend, supplied Plus/Pro residuals are −€3.63/−€0.23 before other costs; €5.63/€2.23 extra net revenue is needed to leave €2. These are not actual results.
- [ ] Reprice 500-person/three-month pilot: supplied subtotal €33,225 = setup €10,000 + KYC/issuance €1,800 + servicing €10,425 + welcome €2,500 + referrals €1,000 + service bonuses €7,500. This excludes unknown minimums, integration, legal, tokenisation, support and liquidity; CaaS minimums cannot be substituted for a full card programme.

## Waitlist and release acceptance

- [ ] Preserve getApiUrl() POST /commerce/ramp-waitlist, interest physical_card_apple_pay and supported schema/region/notes limits. Handle registered/already_registered, validation/API/network failures and repeat submission; success only after server response.
- [ ] No email localStorage or personal data in analytics. Explain processing purpose, link privacy notice; no mandatory marketing consent or hidden schema extension.
- [ ] Keep issuing/rewards/partner/Apple Pay flags false and supported asset/country lists empty until confirmed. Client flags cannot enable money movement.
- [ ] Verify keyboard focus, labels/field errors, aria-live, headings, reduced motion, responsive layout, direct navigation and build. No ordering/payment, reward balance, ACP conversion, unconfirmed logos, invented metrics or testimonials.

Full specifications, competitor comparisons and source assumptions remain in the linked source brief. No production deployment or external submission without separate authorisation, as requested there.
