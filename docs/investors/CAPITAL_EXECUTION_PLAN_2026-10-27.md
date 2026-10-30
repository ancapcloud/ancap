> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Capital and commercial execution — 2026-10-27

## Current product sequencing

The [Research Operations/value roadmap](../WORKFLOW_VALUE_ROADMAP.md) now narrows commercial testing to one recurring research process for one agency/team segment, with an entry/onboarding offer rather than unrelated product expansion. It adds reviewed-version acceptance/history and personal value estimates as a technical baseline, not confirmed business outcomes. Test a 15–18 month post-close runway scenario using actual cash/quotes; keep the 12-month operating plan and rolling 13-week cash-flow. No additional round size, valuation or investor interest is established.

## Decision and evidence boundary

12-month planning horizon, first operating gate at 90 days. Choose a lean team, two offers for one customer segment, reliable payment/delivery and repeat B2B purchases. Raise money for the next evidenced milestone rather than the entire exploratory portfolio. This is a planning decision, not a committed round, valuation, guaranteed return or legal classification.

The supplied analysis examined `e2e88ed`, not current production or bank records. The preceding revenue release is [PR #126](https://github.com/ancapcloud/ancap/pull/126), merged as `da90feb`. Source review does not establish production losses. No verified bank balances, customer financial statements, registered Cyprus/German group, investment terms or grant eligibility were supplied. The Cyprus principal company and German GmbH remain proposed structures pending evidence and professional review.

This plan extends [the active execution board](../REVENUE_EXECUTION_PLAN.md); it does not reset shipped subscription, API billing or creator features to “not implemented”. Financial safety and accepted customer obligations remain ahead of new categories.

## Operating order and owners

Windows are relative to operator approval, not promises or evidence of an existing team. An unfilled owner role remains with the founder.

| Window / priority | Owner | Deliverable and acceptance gate | Current state |
| --- | --- | --- | --- |
| Days 1–7 / P0 | Founder + engineer | Reconcile cash, customer obligations and release baseline; classify fiat/service credits/ACP/wACP/sACP; identify seller and IP owner | Bank/PSP/legal evidence not supplied |
| Days 1–7 / P0 | Engineer | Explicit fiat price separate from ACP price and credited quantity; freeze order terms for later capture/refund; no catalog-based repricing | Implemented in this change; validation in PROGRESS.md |
| Days 8–14 / P0 | Engineer + accountant + counsel | Payment retry/refund/reconciliation matrix, written PSP position, professional quotes and cash-based funding ask | Provider refund orchestration and timeout recovery remain open |
| Days 15–30 / P1 | Founder | Two bounded offers, paid pilot process and investor data room; real order or documented refusal | Commercial validation open; no messages sent by this task |
| Days 31–60 / P1 | Founder + delivery owner | Independent paid delivery, full variable-cost contribution by SKU, repeat demand; suitable stage financing | No fabricated traction or grants in base liquidity |
| Days 61–90 / P1 | Founder | Repeat sales, team plan only when demanded, one capped acquisition channel | Scale only after positive contribution and repeat use |
| Months 4–6 / P2 | Product + sales | Scale one demonstrated channel; reduce manual effort without reducing quality | Requires several healthy cohorts |
| Months 7–12 / P2 | Founder + finance | Distribution, justified features and next capital/grant gate | Requires funded execution and demand evidence |

## Monetary terms and acceptance

Keep fiat payment amount, catalog token price and credited ACP quantity in distinct named fields. The current release introduces `fiat_price` and `pricing_version` for credit packages and a versioned `pricing_snapshot` on each new top-up intent. Capture and refund accounting use the order's recorded terms even if the package is changed or removed. Old intents with usable recorded price/credit metadata remain readable; missing/corrupt evidence requires manual reconciliation. Do not recalculate existing balances or reinterpret ACP as a newly issued service-credit currency.

Current card support is USD only; EUR remains unavailable. Existing numerical package prices/credited quantities and wACP discount are preserved, not economically endorsed. This change does not prove alignment of top-up purchasing power with USD-derived workflow quotes. Review that relationship and actual FX/liquidity before advertising scale. Never use reserve estimates as guaranteed executable prices.

Remaining schema/design work: explicit classification of non-transferable service credits versus tokens, `token_amount`, service-credit quantity, executable `fx_rate`, quote identity, expiry and exposure limits. Require reviewed migration rules before changing old orders/balances. A fixed cash package snapshot is not a market FX quote.

| Scenario | Acceptance evidence | Release scope |
| --- | --- | --- |
| Purchase then delivery | Checkout, PSP amount/currency, credited unit and charge reconciled | Explicit units and frozen top-up terms added; full paid pilot still open |
| Tariff changed/removed after order | Capture and refund use archived amount/quantity | Regression tests included |
| Repeated requests/webhooks | One external charge, one credit and one capture under concurrency | Existing duplicate-webhook tests retained; durable provider-side retry recovery remains open |
| Network timeout | Recover same provider operation, no blind second charge | Open; application response caching alone is insufficient |
| Refund | Provider refund identity/status plus matching ledger reversal | Stripe ledger-only admin approval now fails closed; coordinated provider/refund flow still open |
| Forged/mismatched event | Signature, owner, expected amount/currency verified | Existing checks retained; operator provider verification still required |
| Reconciliation | PSP, bank, orders and ledger show no unexplained differences | Accountant/operator evidence required |
| Contribution | LLM, retries, human review, support, creator share, fees and refunds included | Actual cost collection remains open |

Staging acceptance precedes any explicitly authorized funded payment/refund. A test capture is not customer revenue. The Stripe refund guard is deliberately not a claim that external refunds are implemented: user requests stay pending and no ledger clawback is performed through the blocked approval route. Complete provider-confirmed orchestration/recovery before marking this gate done. [Stripe idempotency](https://docs.stripe.com/api/idempotent_requests) and [refunds](https://docs.stripe.com/refunds) describe distinct provider operations.

## Commercial experiment

Hypothesis: agencies/operators repeatedly preparing materials for crypto projects. Start with a listing-materials pack and recurring campaign/content work with human review. Each offer needs inputs, an example, turnaround, scope, price, revisions and acceptance criteria. Do not promise exchange listing, returns, token price growth, fabricated engagement or an AI-generated security certification. An execution receipt records delivery; it does not prove every conclusion true.

Targets for 90 days, not current results: 30 qualified conversations, 5 paid pilots and at least 3 independent repeat buyers. Founder records price, variable costs and reasons to buy/refuse. If 10 qualified conversations show no willingness to pay, revisit buyer/offer/price. If six weeks produce only free runs, pause advertising expansion. LOIs, registrations and self-funded tests are not sales.

Sequence: own bounded workflows with review → team plan plus metered use after repeats → scoped API/white-label onboarding after a repeatable channel → wider third-party marketplace after payout/dispute/PSP acceptance. Do not sell unbounded inference without cost controls.

## Finance, budget and capital

Track customer payments/advances, recognized revenue, GMV, creator payouts, platform income and investment separately. Accountant decides principal/agent presentation and recognition policy; do not double subtract creator payouts from net commission income. Keep full order contribution separately. One-off pilots are not ARR multiplied by twelve. Show costs both during cloud subsidies and at normal prices.

Founder/accountant review unrestricted cash and a rolling 13-week cash-flow weekly, plus accepted paid orders, SKU contribution, repeat rate, CAC and customer concentration. Keep the 12-month operating budget and optional 24-month scenarios connected to actual quotes. Do not spend customer obligations or bridge reserves as operating funds, subsidize token price from operating reserve, pay self-referrals/refunded purchases, scale negative contribution or hire permanent staff against unsigned financing.

[Existing budget assumptions](BUDGET_12M_ASSUMPTIONS.md) give lean EUR 129,950–247,920 and standard EUR 277,265–539,760 including 15–20% reserve. These are unverified scenario bounds, not quotes, company valuation or a final ask. Lean is the planning baseline; standard needs evidence. EUR ~248k is only a discussion reference and may omit obligations. Do not add another reserve to figures already including it.

Within the first 14 days the founder should obtain company/accounting/cross-border/payroll/security quotes. Derive funding from the maximum cash deficit, required closing reserve and transaction costs, less available unrestricted cash and contractually secured funding. Exclude unsigned pipeline, hoped-for grants, token balances and cloud credits. No numerical ask can be certified without actual opening cash and obligations. Secure the minimum viable next-stage runway if waiting for an optional tranche would threaten delivery.

Funding priority: paid pilots/onboarding (with delivery obligations) → relevant angels/pre-seed → strategic distribution without unbounded exclusivity/IP transfer → grants as upside → cloud credits as cost reduction, not cash. Debt needs a credible repayment source. Counsel selects a locally valid equity/convertible instrument; a generic foreign template is not a Cyprus opinion. Model fully diluted ownership, options, conversions, next round, preferences and control before signing. ACP holdings are not corporate equity.

## Corporate, provider and IP gates

Founder + counsel/accountant identify investment recipient, service seller, IP owner and employer. A second jurisdiction needs operational justification and cross-border advice; no claimed tax saving. Obtain the PSP's written approval for actual products, token/credit treatment and creator payouts before expansion. Separately classify custody, bridge, exchange, MiCA applicability, privacy and consumer obligations; this plan makes no legal determination.

Retain the existing Apache-2.0 license and already granted rights; no retroactive withdrawal. Build commercial distinction through service, quality, integration and distribution. Accounting capitalization of development and research treatment needs the accountant's documented policy; written code is not an arbitrary equity increase.

## Funding opportunities register — checked 2026-10-27

No grant is included in base cash-flow until contractually confirmed. One owner must verify applicant entity, TRL/deep-tech/IP grounds, co-financing and double-funding restrictions before submission.

- Cyprus PRE-SEED/0526: official submission deadline was 11 September 2026, maximum project support EUR 119,999. Closed to a new late application; no timely ANCAP submission supplied. [RIF call](https://www.research.org.cy/en/new-call-for-proposals-for-the-creation-and-initial-development-of-startups-with-international-orientation-pre-seed-programme-pre-seed-0526/).
- EIC Pre-Accelerator 2027: official page lists EUR 0.5–1m, 70% eligible costs, widening-country SMEs and a 5 May 2027 opening. Cyprus is in the country list; ANCAP entity/technology eligibility is unverified. Reconfirm the call's exact closing date and terms before planning an application. [Official programme](https://eic.ec.europa.eu/eic-funding-opportunities/eic-pre-accelerator_en).
- EIC Accelerator: official programme targets TRL 6–8 with a grant below EUR 2.5m and investment EUR 1–10m. The 4 November 2026 full-proposal batch requires a prior short-proposal GO; no ANCAP GO supplied. Do not plan a from-zero last-minute submission. [Official programme and dates](https://eic.ec.europa.eu/eic-funding-opportunities/eic-accelerator_en).

## Day-30 investor packet

Founder owns: buyer/problem/two offers/alternatives/distribution/team/factual results/risks/use of funds; demo on a fixed release with test funds labeled; monthly budget, 13-week cash-flow and no-grant case; contract/delivery/refund register and PSP/bank/ledger reconciliation; corporate documents, fully diluted cap table and developer/IP agreements; security review scope and remediation evidence; ACP explanation separate from shares/revenue/valuation.

Proposed activity targets: 30 suitable investors, 10 substantive meetings, 3 due-diligence processes. These are not forecasts or achieved traction. Outreach remains an operator action; this task sends no messages or applications. Monthly updates report changed facts and next measurable gate, not invented progress.

Exploratory verticals, banking services and large infrastructure remain deferred behind this commercial loop. Security and existing obligations are not deferred. No fictitious turnover, token-price manipulation, guaranteed returns or participant-recruitment payouts.
