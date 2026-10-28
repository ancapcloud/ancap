# Revenue execution plan — 2026-10-27

## Current product focus

[Workflow value and Research Operations](WORKFLOW_VALUE_ROADMAP.md) is the implementation and commercial sequence: one recurring process → external payments → version-bound accepted results → actual costs → renewals → repeatable sales → stage financing → platform expansion. This release supplies private acceptance/history/estimates; it does not claim verified ROI or paying demand. The latest strategy narrows earlier two-offer testing to one Research Operations core service and one entry/onboarding variant. Existing subscriptions, repeats, roles, API and webhooks remain foundations to validate, not missing systems to rebuild.

## Capital-plan extension

[Capital and commercial execution](investors/CAPITAL_EXECUTION_PLAN_2026-10-27.md) adds the 12-month calendar, 13-week cash-flow, corporate/IP/PSP gates and proposed 30-conversation / 5-pilot / 3-repeat-buyer 90-day experiment. Monetary semantics and provider-confirmed refund/reconciliation gates take P0 precedence. Existing percentage targets below are secondary hypotheses until cohort denominators and sample volume exist. Current code adds explicit USD prices and frozen top-up terms; full FX quote expiry, provider retry recovery and external refund orchestration remain open.

## Current priority

Validate repeatable paid workflow usage before expanding infrastructure. ACP-first commerce remains the product contract; ACP, wACP and sACP remain distinct. Existing subscriptions, creator earnings, API billing, checkout and admin revenue analytics are implemented foundations, not missing features to rebuild. No verified customer revenue dataset was supplied. Historical network heights/node counts are not current observations.

This board is the active order; the phase roadmaps remain the implementation inventory. Windows below are planning estimates from operator approval, not deadlines. Owners are proposed roles, not contracted specialists.

| Priority / window | Deliverable | Owner | Acceptance evidence / metric | Dependency | State |
| --- | --- | --- | --- | --- | --- |
| P0 / week 1 | Currency-isolated revenue cards and rankings | Coding agent | Unit tests, frontend build, release checks; never sum or rank different currencies | Standard release checks | Implemented and merged in PR #126; release evidence is tracked with that PR |
| P0 / weeks 1–2 | Durable registration → wallet → workflow → quote → capture → completed paid run → repeat events | Coding agent | Idempotent events, immutable timestamps, source/test tags, admin-only cohort aggregates, unknown/empty states | Existing browser events are local only; ledger captures do not establish external funding | Open |
| P0 / weeks 1–2 | One golden paid workflow | Product owner + coding agent | Select an existing SKU; preview, insufficient balance, duplicate submission, timeout, bounded retry and refund tests; dated pilot evidence separately | Owner selects customer/pilot; funded actions require explicit authorization | Open |
| P0 / weeks 1–3 | Payment integrity review | Coding agent + reviewer | Capture/webhook replay and ordering, currency, refunds and double-charge checks; ACP acceptance, Stripe sandbox separately | Live capture/saved-card validation requires operator authorization | Open |
| P1 / weeks 2–4 | Activation and retention dashboard | Coding agent | Defined denominators, unique cohort users, first completed captured run, repeat runs, D7/D30 retention, no public PII | Durable events and sufficient observation time | Open |
| P1 / weeks 2–4 | 24-month financial scenario model | Product owner | Editable prices, provider costs, CAC/LTV, gross margin and runway; pessimistic/base/upside; explicit exchange assumptions | Real quotes and customer data unavailable | Open |
| P1 / weeks 3–6 | Improve existing prepaid/subscription and creator journeys | Coding agent | Renewal/cancellation, limits, payout eligibility, analytics and refund tests; measure repeat use | Baseline and selected pilot; reuse shipped foundations | Open |
| P1 / weeks 3–6 | Mobile release acceptance | Mobile owner + operator | Physical recovery/signing/biometrics, guest preview, Android internal track and TestFlight evidence | Device, store accounts and macOS for iOS | Open |
| P2 / weeks 6–12 | B2B packaging of API/team features | Product owner + coding agent | Approved pilot, team permissions, spend caps, usage export and invoice reconciliation | Validated demand and accounting review | Open |
| P2 / before scale | Independent security/legal review | Operator + specialists | Findings tracked to closure; custody, jurisdiction, privacy and tax decisions documented | Quotes and approval for expenditure | Open |

## Evidence and measurement

Ledger captures may include synthetic/internal credits. Estimated provider costs are not actual reconciled costs. Show amounts per currency; never imply automatic ACP/USD conversion. GMV, net revenue and gross margin are different measures. A paid success needs a delivered completed result and a positive captured payment attributable to the same user; failed/refunded transactions must not count as retained success. Time to first paid run needs an immutable completion/capture timestamp, not mutable updated_at.

The suggested 90-day targets (40% activation, 8–12% paid conversion, 30% repeat, 40% subscription share, 55–70% gross margin, refunds below 3%, 25% mobile share, 30% creator GMV) are hypotheses, not achieved results. Define denominator, cohort, currency, observation period and minimum sample before adopting them. Missing evidence means unknown, not zero. Separate test/internal cohorts from actual customer cohorts.

## Deferred expansion

Orbital infrastructure, lunar land, longevity, speculative categories and full decentralization remain vision/research tracks. They do not outrank reliable payment, completed user scenarios and repeatable demand. Embedded/MPC wallets, auto-top-up and new custody require separate design/security/legal review. Do not change tokenomics or reserves under this plan.

## Theodore cycle

One bounded unblocked task per cycle: inspect AGENTS.md, actual project roadmaps, STATUS.md, PROGRESS.md and branch state; skip parallel development when another cycle owns the checkout. Preserve others' files or use a worktree. Implement real code, run relevant checks, then record evidence and next action. Do not run concurrent heavyweight builds/model jobs on this PC. Existing independent Telegram status delivery remains responsible for half-hour reports; this document creates no additional scheduler. Code-only checks do not close customer/legal/store gates. No funded payments, paid services or third-party outreach are authorized by this plan.
