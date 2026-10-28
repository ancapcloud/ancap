# Workflow acceptance, private value and Research Operations

## Release scope

This release implements owner-only result assessment, archived reviewed versions and `/ai/value`. It supports the commercial validation order in [the active execution board](REVENUE_EXECUTION_PLAN.md) and [capital plan](investors/CAPITAL_EXECUTION_PLAN_2026-10-27.md). It does not establish paid demand, business ROI, external audit or increased company/token valuation.

- A completed result can be marked accepted, revision requested or rejected. Optional paired time estimates cover work without ANCAP and work with ANCAP including review; optional hourly rate has a distinct unit.
- Each assessment binds to the server's SHA-256 of the exact result JSON. The request must match the hash of the result displayed by the run API. A changed result or competing saved review returns 409; the client requires reload rather than silently retrying against unseen output.
- Assessments are append-only through this API, unique per run/result hash. A transaction row lock serializes competing submissions; a database unique constraint supplies a second invariant. No update/delete API exists. The UI discloses immutability before save.
- A server-owned snapshot preserves the reviewed result. Owner-only history shows up to 50 assessment records; archived result content loads only on request and its hash is verified. New versions can be assessed independently. This records reviewed workflow-run versions, not every intermediate source/agent edit, and is not tamper-proof external certification. The existing `/ai/studio` reviewer queue still controls operation delivery; this personal assessment records the run-detail result and does not replace that queue.
- `/ai/value` displays counts, self-reported effort/labor estimates and platform ledger captures separately. JSON export contains aggregates only, not result bodies, user identity or private notes. Assessment does not authorize payment, trigger a refund or modify balances.

## Data and limits

`091_workflow_value` creates `workflow_result_assessments`, with user/run ownership, result hash, snapshot, verdict, estimates, note and timestamp. Owner-only API reads use `Cache-Control: private, no-store`; foreign IDs return 404. User/run deletion cascades this data with the existing account/run lifecycle. Operation-project deletion and per-operation expiry purge assessments, notes and archived results while retaining the original billing records. A database redaction trigger also purges archives when any worker clears the base result to SQL NULL or JSON null, including an older application worker after rollback. Scrub and assessment creation share a base-run lock. No shared organization report or public investor export is introduced.

Summary scope is the newest **200 completed, non-null results created within the chosen 1–90 day window**; the UI offers 7/30/90 days. The API exposes window boundaries, limit and truncation. Metrics are explicitly for that selection, not lifetime totals. Only assessments matching the current result hash count. Old reviewed snapshots remain accessible in private history, but do not inflate current acceptance/time totals.

No time inputs means unknown, not zero savings. An explicit zero is retained. `minutes saved = baseline - assisted`; negative values remain negative. Labor estimates multiply this difference by the user-entered rate per hour and aggregate separately per unit. USD, EUR, ACP, wACP and sACP are not implicitly converted or combined. These estimates are neither reconciled costs nor cash savings, profit, revenue or ROI.

Ledger charge figures include positive captured workflow intents with capture-ledger evidence for the selected owned runs. Quotes, reserved/failed/refunded intents and credit top-ups are excluded. They may still include internal/test credits and unclassified payment origin; they are not verified external cash payments or recognized revenue. Export metadata explicitly records this unverified status and the run-creation window basis. An accepted result can later be refunded: acceptance remains a quality observation while the refunded charge stops counting. No repeat-customer/ARR claim is derived from this private panel.

## Technical release gate

- Upgrade/downgrade/upgrade of the additive migration on disposable PostgreSQL.
- Ownership isolation, guest rejection, immutable/conflicting requests, competing submissions, stale-hash exclusion and snapshot integrity checks.
- Retain negative estimates and currency separation; demonstrate assessment leaves balances unchanged and refund accounting remains separate.
- Verify summary window/truncation and existing workflow/payment regressions.
- TypeScript, lint, production build, five-language/mobile browser coverage, private JSON export, saved/stale/error/history paths.
- Merge reviewed commit only after CI; verify deployed build, health/readiness, migration head and unauthenticated denial on private endpoints. Never use real funds as an automated check.

Deployment enables the owner UI after `alembic upgrade head`. Rollback uses the previous application image while leaving this additive table intact; do not downgrade/drop assessment data in production as routine rollback. Export/backup and explicit data-loss approval precede any destructive downgrade. No wallet, token or existing balance migration is required.

## Next work, in execution order

2026-10-28 implementation slice: `app/services/workflow_costs.py` provides an
offline evidence-allocation reconciler with strict input schemas. It rejects
duplicate source-line/run allocations, conflicting currency/category/source
amounts and cross-run over-allocation; keeps currencies separate and missing
categories unknown; includes creator payout once and distinct retry evidence.
Explicit zero requires evidence. Decimal accumulation preserves database-scale
precision. Callers must supply the complete allocation set for each source line.
This is a calculation foundation, not a public ingestion endpoint or verified
actual-cost dashboard. Persistence, authenticated evidence review, provider
imports, completeness verification and SKU/client contribution remain open.
Local validation: `python -m pytest tests/unit/test_workflow_costs.py
tests/unit/test_workflow_value_estimates.py -q` — 29 passed. No database migration,
deployment or real payment was performed for this calculation-only slice.

2026-10-28 persistence slice: migration `092_workflow_cost_evidence` stores
operator-attested document source lines, SHA-256 references, review notes,
reviewer IDs/timestamps and per-run allocations. Admin-only
`POST /v1/workflow-store/admin/cost-evidence` accepts a complete immutable
distribution of one source line (at most 200 runs); duplicate source/document/line
keys return 409, including concurrent requests. Invalid distributions and missing
runs leave no partial records. There is no update/delete/reallocation API.
`GET /v1/workflow-store/admin/runs/{run_id}/costs` returns currency-separated
totals, evidenced/missing categories and an explicit independent-verification
false flag. Empty coverage is unknown; category coverage is not proof all costs
were captured. Both endpoints use platform-admin authentication and no-store.

Operators must use canonical supplier/document/line IDs and review the source
document before entry. A document hash is a reference, not proof of authenticity;
renamed sources/documents cannot be detected automatically. Raw documents are
not uploaded or fetched. Provider imports, evidence-file retention/access,
correction/reversal workflow, independent reconciliation, automated source
identity and SKU/client contribution remain open. Do not import a creator payout
again as an additional expense under another category. Run deletion cascades its
allocations; source evidence remains reserved and cannot be reused. Reviewer
deletion clears the user reference while retaining the record timestamp.

Deploy requires migration 092. Routine rollback leaves accounting tables intact;
destructive downgrade is only for a disposable test database, never routine
production rollback. This slice does not mutate balances or payment intents.

Local verification on a dedicated disposable PostgreSQL 16 database:
`pytest tests/api/test_workflow_cost_evidence_api.py tests/api/test_workflow_value.py
tests/unit/test_workflow_costs.py tests/unit/test_workflow_value_estimates.py -q`
— **44 passed**, including private access, conflicting/concurrent writes,
precision, invalid-batch rejection, split allocations, run deletion and prior
assessment regressions. Alembic `092 -> 091 -> 092` succeeded. These are local
checks; CI, deployment and real provider-document reconciliation are pending.

| Priority | Work | Owner | Acceptance / dependency | State |
| --- | --- | --- | --- | --- |
| P0 | Actual cost per execution: model/data/infrastructure/retries/review/support/payment fees | Engineer + finance | Provider billing and real manual-work evidence, separate estimates; contribution by SKU/client without double counting creator payouts | Open; existing margin snapshots are estimates |
| P0 | Classify external payments, bonuses, test/internal credits and refunds | Engineer + finance | Reconcile PSP/bank/order/ledger sources; unknown history stays unclassified until evidence exists; no arbitrary balance relabeling | Open |
| P0 | Reviewed-version history and acceptance | Engineer | Immutable owner-only result snapshots, concurrent/stale checks and private summary | Implemented in this release; CI/deployment evidence tracked in its PR |
| P1 | Repeat order from an accepted result | Engineer + product | Reuse existing repeat/edit-repeat foundation; new quote and explicit buyer confirmation; measure a real repeat external purchase | Existing repeat navigation retained; acceptance-specific commercial flow open |
| P1 | Recurring Research Operations pilot and source-change updates | Founder + product | One paid recurring process; bounded source collection, versioned changes, unsupported-claim flags, human review, cost cap and approved delivery channel | Existing published schedules and CoinGecko change snapshots retained; general research-source/document monitoring is a pilot hypothesis |
| P1 | Multiple client projects and team value report | Product + engineer | Agreed organization/project ownership and visibility; consent-based role checks and isolation tests | Existing project/member workspaces retained; shared value aggregation remains open |
| P1 | Bounded recurring service package | Founder + finance | Paid pilot, clear included work, metered overage, separately priced expert review and positive full contribution | Reuse implemented subscriptions; validate the offer before expansion |
| P1 | Predictable spending and risky-action approval | Engineer + operator | Reuse spend-cap foundations, enforce per-process budgets/retry limits; explicit approval for high-impact actions | Existing Studio ACP budgets, versioned hourly schedules and delivery review retained; Research Operations extensions need validation; no autonomous trading/fund management |
| P2 | Procurement/investor evidence export | Product + finance | Owner opt-in, de-identification, reconciled payments/costs and audit trail | Private aggregate JSON exists; public diligence export remains open |
| P2 | API/webhooks/roles for demonstrated customer processes | Engineer + sales | Reuse existing API/team/webhook foundations; buyer demand and observed integration usage | Expansion after renewals, not a new platform-first project |

## Research Operations product hypothesis

Primary buyer hypothesis: agencies/operations teams maintaining research and client materials for several crypto projects. Secondary research-team hypothesis follows only if the first fails or an actual paid contract changes priorities. One launch/listing report may remain an entry product; it is not evidence of recurring demand. Two initial offer variants in the capital plan should now test one core recurring process plus one entry/onboarding path, not two unrelated businesses.

Proposed core process: approved public sources → structured baseline document → source-change detection → update changed sections → flag unsupported claims → responsible human review → version/assessment history → agreed customer delivery → actual cost/manual-work accounting. Source fetching needs bounded access, SSRF protections, licensing/attribution and cost/retention rules before automation. The current release supplies reviewed-result acceptance/history, not this entire source-monitoring pipeline.

Sell bounded onboarding, a clearly scoped base service, metered extra execution/data and separately priced expert review. No unlimited inference, guaranteed listing, investment outcome, token appreciation or autonomous custody/trading. Track manual operations openly; one-off bespoke work is a separately priced service. Productize repeated requirements rather than adding every customer request to the common roadmap. Similar customers should become cheaper to onboard and serve.

Proposed guiding metric: recurring gross profit from external paying customers with evidenced delivery quality. It is not computed by this personal estimate panel. Required observations: independent paying organizations; subscription versus one-off revenue; renewals/churn/expansion by cohort; CAC and sales cycle; customer concentration; model/data/infra/fees/review/support/refund costs; time to useful result; accepted/revised/rejected results; factual/source errors; repeated use without founder intervention. Do not count top-ups, free credits, token turnover, one-off reports or internal captures as ARR.

## Commercial and capital gates

Use the existing 90-day plan with more specific checkpoints: days 1–14 establish entity/IP/cash/product facts and one buyer/process; around 20 qualified interviews by day 30; 3–5 paid pilots in days 31–60 only if demand exists; seek renewals and standardized delivery by day 90. Earlier 30-conversation / 5-pilot / 3-independent-repeat targets remain proposed 90-day hypotheses, not results. No user contacts or investor messages are sent by this release.

Raise in stages: commercial validation → repeatable onboarding/renewals → one scalable channel → external platform only after developer-created customer value is observed. Budget the next evidence milestone, including payroll/founder compensation, model/data/infra, security, sales/delivery, legal/accounting and delay reserve. Test 15–18 months of post-close runway as a scenario alongside the 12-month operating budget and 13-week cash-flow; no runway or round ask is certified without actual cash and commitments. Avoid double-counting reserve, opening cash or secured receipts in funding calculations.

Company equity/contracts/IP, product service-credit obligations and ACP/wACP/sACP utility/risks are separate analyses. Keep the ACP-first core and test familiar B2B payment adapters only where technically supported and PSP/counsel approved. Confirm investment recipient, signatory authority and asset ownership; two jurisdictions or popular convertible templates are not substitutes for evidence or local advice.

Data room: company/bank/ownership; IP/license/contractor rights; fixed release/demo/limits; security/access/backup/incidents; contracts/invoices/external payments/renewals/refusals; actual costs/manual work/refunds/cash-flow; data access/retention/deletion/provider rules; token issuance/distribution/related wallets/obligations/legal review. Customer data is not reused for training or a public evidence pack without rights and consent.

Stop/pivot when no recurring budgeted task appears, useful pilots do not renew, manual work erases contribution, every customer needs custom code, token payment obstructs a lawful purchase path, GMV fails to create platform income or customer concentration masks demand. Do not react by funding more unrelated verticals. No new token incentives, artificial turnover, universal agent ecosystem or foundation-model project is part of this queue.
