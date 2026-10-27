# ANCAP Status

> Updated: 2026-10-27
> Fast truth: this is the shortest current status entry point.

## Current truth

**Capital execution (2026-10-27):** [12-month operating plan](docs/investors/CAPITAL_EXECUTION_PLAN_2026-10-27.md) sets monetary integrity and corporate/IP/PSP gates ahead of paid pilots and lean fundraising. New top-ups separate explicit fiat price from ACP price/credited quantity and retain order-time terms. Legacy missing evidence requires reconciliation. Stripe ledger-only refund approval is blocked until provider-confirmed orchestration is implemented. Existing balances and token economics are unchanged. No verified funding ask, legal entity group or customer revenue is claimed.


**Execution priorities (2026-10-27):** [Revenue execution board](docs/REVENUE_EXECUTION_PLAN.md) is the active work order. This change separates currencies in margin/cost/referral cards and workflow rankings. Customer revenue remains unverified. Durable cohort measurement, a golden pilot and repeat-use validation remain open. Existing subscriptions, creator earnings and API billing are implemented foundations. PR #125 is merged; pre-change production baseline is `e2e88ed`. Older entries below are dated historical evidence.


**Homepage applications framing (2026-10-16):** Home hero reframed around people + AI applications and earning on paid workflow runs; featured **Smart Pay** (document/photo → AI decode → ACP quote → confirmed transfer) linking to `/payment-scanner`; People + AI section full; six areas as today’s map. `FF_PROJECT_ECONOMY` still false. Catalog `/economy` remains preview (3n3rgy demos).

**Payment Scanner photo upload (2026-10-16):** `/payment-scanner` accepts photo/image upload (client QR decode when available + `POST /v1/payment-scanner/parse-image` AI OCR); text paste/file import unchanged; manual confirm still required.

**Long-horizon infra roadmap (2026-10-16):** Master **R11** expanded to future **ANCAP datacenters in space** (X6–X7) · **R14 Full decentralization** added (D0–D5). Docs: `docs/SPACEX_SATELLITE_ENCRYPTED_SERVERS_ROADMAP.md`, `docs/FULL_DECENTRALIZATION_ROADMAP.md`. Does not block Phase 6.

**People + AI Project Economy (2026-10-16):** Showcase + catalog foundation — tables/API `/economy/*`, UI `/economy`, five demo cards owned by **3n3rgy**. Migrations `088_project_economy` + `089_economy_seed_owner`. Payout/acceptance not started.

Workflow discovery release deployed and live-verified (2026-10-14), build `426bc5c`: task matching, local shortlist, comparison of three workflows, exact run-cost planning and JSON export; investor page links immutable local-demo evidence. Frontend 46 unit tests, mobile 281 tests, full Linux backend 883 passed / 34 skipped, browser CI 25 passed / 1 skipped. Rust/contract CI and Docker build passed. Live API ready, catalog source live, browser runtime errors 0. Historical local presentation work below is included in this deployment. Scope/remaining audit items: `docs/WORKFLOW_DISCOVERY_RELEASE_2026-10-14.md`; durable production evidence: `docs/investors/evidence/2026-10-14-workflow-release/`.

Investor corporate-plan update (2026-10-14, local): Cyprus principal company + additional German GmbH are described as proposed, with separate quote requests. Introductory investor memos RU/EN and outreach drafts are in `docs/investors/`; no correspondence sent. Verification of this update: production frontend build passed, Vitest 6 passed, Playwright 9 passed including planned-entity copy on both investor/budget pages in five languages. This initially local update is included in verified web release `426bc5c`.

**Investor presentation (deployed, 2026-10-14):** homepage/navigation regrouped around AI workflow commerce, six-area project portfolio, and `/investors` overview. Portfolio pages expose buyer→task→inputs→AI result→limits→pay→receipt chains (`projectOffers`). Demo script + 12‑month budget assumptions published under `/docs/investors/*` (unverified cost scenarios). Planned entities described as **intent only**: Cyprus principal company + additional German GmbH — not registered group / not tax savings; separate RFQs in `docs/investors/quotes/`. Final ask pending quotes. No verified revenue/customer metrics supplied. Included in verified web release `426bc5c`; does not close mobile/security release checks. Tracker: `docs/CURSOR_INVESTOR_FINISH_RU.md`.

Presentation verification: portfolio/offer-chain vitest (incl. localized offers); Playwright investor checks (languages, filters, research heroes, budget/demo links); API smoke on disposable DB `ancap_investor_demo_20261014` (2 passed); live LLM staging demo `tmp/investor-live-llm-20261014/` (`fallback_used=false`, ollama/qwen2.5:3b, fee+credits — no Stripe/broadcast). Screenshots: `tmp/investor-preview-2026-10-14/`. Offer + budget/demo copy: EN/RU/UK/DE/zh-Hant.

ANCAP is **largely built**, but it is **not fully release-complete end-to-end**.

Earlier investor verification: production frontend build passed, portfolio/localization Vitest **6 passed**, Playwright **8 passed**, demo database guard checks **6 passed** without DB access. Stored local Ollama evidence reviewed and archived at `docs/investors/evidence/2026-10-14-local-ollama/`; this review did not rerun the live demo or API smoke. Production provider configuration remains unverified.

**Work-stop blockers: none.**

**Public GitHub:** source of truth is [`ancapcloud/ancap`](https://github.com/ancapcloud/ancap) (account rename from `dragoncattrx-hub`). Docs twin: [`ancapcloud/ancap-docs`](https://github.com/ancapcloud/ancap-docs). Live product: [ancap.cloud](https://ancap.cloud).

**Bridge doctrine:** **1 ACP ↔ 10 wACP** (cutover 2026-10-04). Fiction SKUs (teleport / Barsuk / dark-matter auction) retired from the public launch surface.

**ACP supply (2026-10-02):** wallet figures such as `1,532,370,736.69` / `2,538,291,192.32` ACP were not protocol issuance. **Regenesis v3 is live** on `ancap.cloud`: issued **210,000,000 ACP** hard cap. Details: `docs/ACP_SUPPLY_INCIDENT_2026-10-02.md`.

**ACP nodes (2026-10-13):** three peers on the same tip family (height **18**, tip `ab6bdd19…d018`): primary `https://acp1.ancap.cloud/rpc`, Oracle `http://152.67.79.206:8545/rpc`, local PC `:8545`. Plan: [`docs/ORACLE_CLOUD_ACP_NODE_PLAN.md`](docs/ORACLE_CLOUD_ACP_NODE_PLAN.md). DNS/TLS `acp2.ancap.cloud` still open.

**ACP “mining” clarification:** there is **no PoW mining pool**. The lean-chain miner is a fee-packed block assembler (see `docs/ACP_LEAN_CHAIN.md`).

**Safe-launch controls (2026-09-28):** auth cookie `SameSite=Lax` + prod CORS; free ACP 1M cap; anti-sybil; Terms §3 residency draft pending counsel.

Active remaining work (not blockers):
1. **ACP mobile wallet** — device-ready release (Play/TestFlight, physical sign-off, iOS native).
2. **Open-source follow-through** — `ancap-docs` Discussions pin/category UI. Root `README.md` is present — do not report it missing. Boundaries: `docs/OPEN_SOURCE_GITHUB_TRANSPARENCY.md`.
3. **Monetization depth** — optional conversion/LTV; Stripe 4.1 is operator live verification only. Do **not** report “monetization after the first ACP cycle” as a blocker.

Security / CI / prod-hardening baseline closed in the **2026-07-01** wave (`docs/SECURITY_CLOSURE_EVIDENCE_2026-07-01.md`); external upstream key revoke audit remains operator-open, not a freeze.

Theodore / progress bots: do **not** report missing `README.md`. Do **not** report monetization after the first ACP cycle as a work-stop blocker.

**2026-07-01 hardening:** see `MASTER_ROADMAP.md` § Hardening + deploy wave and `docs/SECURITY_CLOSURE_EVIDENCE_2026-07-01.md` for deploy/CI/security closure evidence.

Active trust/adoption track running alongside those priorities:
- **GitHub-first open-source transparency**, where public-safe components become easier to audit, integrate, and contribute to, while keys, bridge signer operations, deploy secrets, and sensitive infrastructure stay private.
- the public docs repo at `https://github.com/ancapcloud/ancap-docs` is now live with the exported seed bundle pushed, Docs CI green on `main`, checked-in repo settings / labels / milestones applied, and default-branch protection live.
- the repeatable live follow-up path is `python scripts/generate_ancap_docs_live_followup.py --repo ancapcloud/ancap-docs`; by default it writes the dated artifact pair plus the stable latest aliases `tmp/ancap-docs-live-follow-up-latest.md` and `tmp/ancap-docs-live-follow-up-latest.json`, treats custom `--basename` / `--date-label` values as filename components instead of path fragments so writes stay inside `--output-dir`, `--fail-on-not-ok` exits with code `2` when unresolved live drift remains, and the wrapper's default terminal summary now also surfaces per-scope drift counts plus grouped manual follow-up totals from `driftSummary` / `manualFollowUpSummary` so cron/CI logs can be triaged without reopening the saved JSON artifact.
- current honest live drift is still manual GitHub admin/auth follow-through: extra `General` / `Polls` categories still exist, the seeded `Announcements` / `Ideas` / `Q&A` / `Show and tell` category descriptions still need the checked-in ANCAP wording, the seeded bootstrap discussions still need pinning, project-board seeding/verification is still blocked until GitHub auth includes `read:project`, and the later org-ownership decision/migration is still pending.

## Read this next

1. **Execution source of truth:** [MASTER_ROADMAP.md](MASTER_ROADMAP.md)
2. **Compact status matrix:** [docs/STATUS_MATRIX.md](docs/STATUS_MATRIX.md)
3. **Supporting product snapshot:** [PRODUCTION_ROADMAP.md](PRODUCTION_ROADMAP.md)
4. **Detailed mobile tracker:** [docs/mobile/ROADMAP.md](docs/mobile/ROADMAP.md)
5. **Monetization strategy context:** [ROADMAP-MONETIZATION.md](ROADMAP-MONETIZATION.md)
6. **Historical architecture roadmap:** [ROADMAP.md](ROADMAP.md)

## Rule

If any document conflicts with `MASTER_ROADMAP.md`, trust `MASTER_ROADMAP.md`.
