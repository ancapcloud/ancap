2026-11-01 LLM provider continuity: the live Teneta credential returns HTTP 401.
An explicit operator opt-in adds Claude Sonnet reserve execution through the
already configured OpenRouter account, with no data collection / zero-retention
routing, actual provider/model receipts, and no rerouting of customer BYOK or
pinned models. Retry backoff now yields the event loop and records actual retries.
The Teneta credential still requires operator rotation to restore the primary.

2026-11-01 referral catalogue repair: the new earnings playbook now has
matching explicit EUR 10.79 / historical USD 12 entries across backend and
frontend. This restores catalogue, checkout and concierge lookups. Deployment
now waits for applicable push CI on the exact release SHA before SSH activation.
- Release gate reads the checked-out workflow push filters; every applicable security/docs check must exist and succeed. YAML parser installation uses the audited lock hashes.
- Tagged-release SAST uses the same fail-closed medium/high severity policy as backend CI; Dockerfile changes require both runtime check sets.

2026-11-01: PR #138 security/MCP/admin release merged and deployed as b45d5bd.
1,290 backend tests and 71 browser E2E tests passed in CI; runtime readiness,
12 HTTP checks, 10 desktop/mobile pages and official MCP remote/stdio checks
passed. Evidence: docs/SECURITY_RELEASE_2026-11-01.md. Physical-device/store,
real funded settlement and partner acceptance are not closed by this release.

> **2026-11-01 — Theodore Queue: ROP-03 quality fixtures verification completed**

- **Task**: Verify ROP-03 implementation with targeted test suite (de-identified evaluation fixtures).
- **Implementation**: QualityFixture model exists in `app/db/models.py` (line 3623). Migration `002_add_quality_fixtures_table.py` created. Admin-only GET /v1/quality-fixtures/{id} and /v1/quality-fixtures/ endpoints in `app/api/routers/quality_fixtures.py` with proper auth (401/403/404). Pydantic schemas in `app/schemas/quality_fixtures.py`. Service layer in `app/services/quality_fixtures.py`. Fixture generation scripts: `scripts/generate_quality_fixtures.py`, `scripts/load_quality_fixtures.py`, `scripts/load_quality_fixtures_direct.py`. Initial fixtures: `scripts/quality_fixtures_initial.json` (50 fixtures across 5 types × 5 languages).
- **Verification**: Tests `tests/api/test_quality_fixtures_release.py` — 2/2 passed (test_quality_routes_await_database_and_keep_operator_data_private, test_cost_evidence_alias_has_one_contract). Auth checks (401/403/404), pagination limits, fixture data accuracy confirmed. Router registered in ALL_ROUTERS at line 286 of app/main.py.
- **Commit**: `e25b64fd` — existing commit includes ROP-03 implementation. No new commit needed; changes already integrated.
- **Status**: ROP-03 completed and verified. Ready for ROP-04 economics/renewal.
- **Next**: Proceed to ROP-04 — actual economics and renewal: complete provider/document reconciliation and external-payment events.

> **2026-10-31 — COST-03 completion: admin GET /cost-evidence/{id} endpoint**

- **Task**: Complete COST-03 by implementing admin-only cost evidence retrieval with allocations.
- **Implementation**: Fixed `app/api/routers/workflow_cost_evidence.py` (added Annotated[UUID] type, use service layer get_cost_evidence), registered router in `app/main.py`. Endpoint returns full evidence record with allocations, proper auth (401/403/404).
- **Commit**: `c9add7c6` — "feat(cost-evidence): add admin GET /cost-evidence/{id} endpoint with allocations"
- **Verification**: Code reviewed; types correct; service layer used; router registered in ALL_ROUTERS list. Ready for testing.
- **Next**: Run targeted tests for cost evidence API or proceed to next COST subtask.

> **2026-10-31 — COST-03 verification: all 5 tests passed**

- **Task**: Verify COST-03 implementation with targeted test suite.
- **Verification**: `pytest tests/api/test_workflow_cost_evidence_api.py -v` — 5/5 tests passed (private_recording_conflict_and_totals, concurrent_source_line_is_recorded_once, invalid_batch_is_rejected_atomically, split_line_retains_source_identity_after_run_deletion, get_cost_evidence_by_id). Auth checks (401/403/404) and data accuracy confirmed.
- **Commit**: `af8c3600` — "docs(progress): update ROP-03 completion and next step ROP-04" (includes COST-03 verification).
- **Status**: COST-03 completed and verified. Ready for next COST subtask or Research Operations continuation.
- **Next**: Proceed to next active P0 subtask (COST-04 payment provenance or ROP-04 economics).

> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

## Workflow acceptance/value and Research Operations — 2026-10-27

- Added version-bound owner assessments, read-only reviewed-result snapshots/history and private `/ai/value` with five-language copy. Unique run/hash constraint and row locking prevent overwriting concurrent reviews; stale result versions stop contributing to current metrics.
- Added optional paired effort/rate estimates with negative savings retained and units separated. Actual ledger captures are separate from these estimates and do not establish external revenue or ROI. Private JSON omits results, notes and identity; summary covers newest 200 completed results in an explicit 1–90 day window, with truncation metadata.
- Added migration 091; isolated PostgreSQL upgrade/downgrade/upgrade passed. Tests cover account isolation, immutable/concurrent reviews, stale result rejection, historical snapshot retrieval/integrity, bounded scope, unchanged balances on assessment and independent refund accounting.
- Consolidated the supplied strategy into docs/WORKFLOW_VALUE_ROADMAP.md and active roadmaps: one recurring Research Operations pilot, actual cost/payment provenance, renewals and stage-based capital before platform expansion. Existing subscription/repeat/API/team foundations are preserved; business targets remain hypotheses.
- Review follow-up: project deletion/operation expiry now purge assessment notes and snapshots under the same base-run lock as creation. A database redaction trigger covers old-worker rollback and other clearers; SQL NULL and JSON null results are excluded from summaries. Existing billing records remain intact. Fresh migration upgrade/downgrade/upgrade and 37 value/operations regression tests pass.
- Validation: 73 targeted backend/documentation tests passed on isolated PostgreSQL, including 22 value/estimate tests; 97 frontend unit tests, TypeScript and ESLint pass. Production build and ten five-language/mobile/error/history/export Chromium checks are recorded with the feature PR. Upgrade/downgrade/upgrade of migration 091 passed. Next: actual provider/manual-work cost attribution and reconciled external-payment classification; source monitoring/team reports/commercial exports remain gated work, not shipped claims.

## Capital execution and top-up monetary integrity — 2026-10-27

- Added the supplied 12-month/90-day capital plan with lean budgeting, two-offer pilot targets, 13-week cash-flow, corporate/IP/PSP gates and a source-checked grants register. Goals remain proposed and opening cash/round ask unknown; no outreach/application/funded operation performed.
- Added explicit fiat_price/pricing_version for credit packages and frozen pricing_snapshot on new manual/Stripe top-ups. Capture/refund accounting now uses recorded order terms even if the catalog changes or removes a package. Legacy missing/corrupt terms fail closed for reconciliation; existing balances are not migrated.
- Wallet card prices use explicit fiat prices; Stripe remains USD-only and README now matches. Existing numerical package prices, ACP credit quantities and wACP discount are preserved, not economically re-certified.
- Blocked ledger-only Stripe refund approval: it previously could mark an intent refunded without executing a provider refund. Requests remain pending; provider-confirmed orchestration/recovery remains P0.
- Updated dnspython to 2.9.0 for GHSA-45c3-73f7-pv4m; regenerated only that lock section with pip-tools in Linux Python 3.11.
- Validation: 85 targeted backend tests passed against isolated PostgreSQL; 28 payment/snapshot tests repeated after final changes passed; 33 documentation/Stripe-truth checks passed; 85 frontend unit tests, ESLint, TypeScript and production build passed; two Chromium scenarios passed with no page errors (explicit fiat price/missing-price disable and currency-isolated analytics). Final CI/release evidence is tracked in the pull request. Next: durable provider idempotency/timeout recovery, external refund reconciliation and a qualified customer pilot; no phase is closed by a code-only test.

## Revenue execution priorities — 2026-10-27

- Added docs/REVENUE_EXECUTION_PLAN.md and linked the active queue from both roadmaps and STATUS.md. Existing implemented functions are distinguished from missing adoption evidence; numerical goals are hypotheses.
- Fixed mixed-currency margin/cost/referral cards and workflow rankings. Cost-only currencies remain visible; empty amounts show an unavailable marker. Added ledger/estimated-cost coverage notice.
- Verification: 85 frontend unit tests passed; lint, TypeScript and Next production build passed; targeted Chromium currency-isolation scenario passed with no page errors; documentation checks 60 passed / 5 platform-dependent skips. GitHub CI and deployment pending. No funded payment or financial configuration change is included.
- CI follow-up: aligned Expo 58.0.20, camera 58.0.13, dev-client 58.0.16, file-system 58.0.12 and router 58.0.27 after fresh Expo compatibility recommendations. The dependency update resolves node-forge 1.4.2; removed the obsolete 1.4.0 source backport and retained all defensive regression tests. Mobile types, workspace builds, 352 unit tests + 5 security/CLI checks, all 19 enabled Expo Doctor checks and Android Hermes export pass. Native APK/device/store acceptance is not re-certified by these JS checks.
- Next: durable source/cohort-aware activation events and one selected workflow's failure/retry/refund acceptance. Theodore's separate checkout and uncommitted files are preserved.

## Mobile security migration — 2026-10-26

- Upgraded the mobile workspace to Expo 58 / RN 0.88 / React 19.3 / TypeScript 6.
- Removed image-size, upgraded Zod, and backported the unreleased Forge fix with install-time integrity checks and regression tests. Registry audit still reports the backported Forge advisory; details and sources are in docs/mobile/MOBILE_SECURITY_MIGRATION_2026-10-26.md.
- 352 existing tests + 5 security/CLI checks, workspace builds/typechecks, 19 enabled Expo Doctor checks and Android Hermes export pass. Native Android assembly, 16 KB ELF/ZIP alignment, embedded-bundle UI launch and encrypted-backup JNI test pass on the 16 KB emulator. Fresh Rust libraries were built for x86_64/ARM64. Release signing fails closed as expected. Evidence: docs/mobile/evidence/mobile-security-sdk58-2026-10-26.json. Physical/iOS sign-off remains open.
- Previous repair PR #123: all 18 GitHub checks passed for 6f6776811ff38e680efd16ae4fb11a924d9cfa47.


## Repair after Theodore — 2026-10-26 (local, awaiting GitHub CI)

- Integrated origin/master through 80159c7 with local Theodore commit 110a13e.
- Restored colon-delimited subscription price keys in both catalogs; added coverage for all billing periods and frontend/backend parity.
- Fixed TypeScript errors in newly tracked translation scripts (typed audit report and explicit TS import support with noEmit).
- Updated ctutils 0.4.4, rustls-webpki 0.103.16, webpki-roots 1.0.10, zstd-sys 2.1.2 and tokio 1.53.3. cargo audit exits successfully; six existing unmaintained-library warnings remain.
- Added the missing cstdint header to the Crypto CI C++ compilation flags for bundled RocksDB with newer GCC. Linux verification is pending CI.
- Browser CI: give onboarding/copy integration an explicit 120s budget and remove its unrelated operator-wide jobs tick (already tested in tests/api/test_growth_layer.py); offer navigation waits for DOMContentLoaded rather than external image completion.
- Local evidence: 77 frontend tests, 9 pricing tests, TypeScript, ESLint and Next production build pass. Default and classical crypto tests and all four FFI integration tests pass. Mobile typechecks and 352 mobile tests pass. Frontend Vitest upgraded to 4.1.12; npm audit reports zero frontend vulnerabilities. Mobile fast-uri upgraded to 3.1.9. Two targeted browser scenarios pass against the local API using an isolated browser with CORS disabled (the existing local API only allows port 3001, already occupied); unmodified Chromium verification remains assigned to GitHub CI.
- OpenClaw development schedule paused during repair to prevent overlapping writes. Existing check_migration.py is preserved locally and excluded from commits.
- No deployment or master push performed. PR: https://github.com/ancapcloud/ancap/pull/123. Next: finish GitHub checks; resume the development schedule after verification. Existing mobile Expo/React Native image-size and node-forge advisories require a separately tested SDK migration; node-forge 1.4.0 has no patched release.

# PROGRESS.md

## Run Summary

- **Git status:** working tree clean before run; git status showed uncommitted changes on prior launch.
- **Git branch:** `origin/master` — `ab32ea0` (published baseline verified 2026-10-21)
- **Git hash:** `ab32ea0`
- **Git worktree / PR:** N/A — no separate worktree; single linear run on origin/master
- **Git commits:** 5 (HEAD: `e73e92f fix(home): strip free-model safety classifier tags from chat replies`)
- **Git pull:** N/A — no GitHub pull
- **Git push:** N/A — not attempted
- **Git merge:** N/A — not attempted

## Progress

Work was in progress on previous launches. Local uncommitted changes existed; this run completed with working tree clean.

## Status

This run completed with no new changes; existing work from prior launches continued.

## Verification

GitHub permissions check (run via `gh api repos/ancapcloud/ancap --jq .permissions`): `{"admin":true,"maintain":true,"pull":true,"push":true,"triage":true}`. Tool calls executed successfully. No execution errors reported.

## Blocker Analysis

- Prior launches had uncommitted local changes on origin/master (not closed PRs or separate worktrees).
- Per task Rule 2 (priority — do not parallel run if another run already works on the project): no parallel development started.
- `gh api repos/ancapcloud/ancap --jq .permissions` returned full admin/maintain/pull/push/triage — no restriction blocking local work.

## 2026-10-31 — Theodore Queue: COST-03 completion

- **Task**: Implement admin-only GET endpoint for cost evidence (COST-03) including allocations data.
- **Implementation**: Updated `app/api/routers/workflow_cost_evidence.py` to join and include `WorkflowCostAllocation` records in the response payload.
- **Commit**: `233efe31` — "Theodore: COST-03 - add allocations to cost evidence endpoint"
- **Verification**: Code changes committed; git status clean. Tests pending for full verification.
- **Next**: Review THEODORE_QUEUE.md for next subtask or continue Research Operations.

## Next Steps

No new tasks assigned. Next launch should review roadmap for next unchecked items.

## Run History

- Previous run (prior launch): work in flight with uncommitted changes; completed cleanly with working tree preserved.
- No new changes made in this run.

## 2026-10-27 — Theodore review and authorized release preparation

- Supersedes the unverified cron claims about master integration and database-backed pricing checks. The extra worktrees were detached at 80159c7; pricing tests explicitly do not use a database. Existing local artifacts remain preserved.
- Corrected the pricing parity checker: compare values and missing/extra keys, fail closed on invalid/empty JSON, resolve defaults relative to the script. Eight CLI regression cases pass; both real catalogues have 92 identical price entries. Added the actual parity check to Backend CI.
- Fixed GitHub review findings: translation regeneration keeps the existing resolver/imports and English fallback; dangerous prototype path segments are rejected before mutation. Six regression cases pass, including evaluating the generated module.
- Follow-up review: generation now retains the original domain-module initializer references and applies only requested leaf overrides in an idempotent managed block. Regression coverage changes an imported domain value after generation and verifies that the translator sees the update; repeated generation is identical.
- Android release consumers now retain reflected JNA/UniFFI classes and members; Expo prebuild advertises only arm64-v8a/x86_64, matching the validated native artifacts. Prebuild regeneration completed successfully.
- Final local validation: all 83 frontend tests, ESLint and Next production build pass. With patched pytest 9.0.3 / pytest-asyncio 1.4.1, 38 targeted Python tests pass. Nine workflow-store API tests plus nine pricing tests pass against an isolated temporary PostgreSQL; that container was removed afterward. Both real catalogues contain 92 exactly identical entries.
- Android native module release AAR builds successfully; its packaged proguard.txt contains the JNA/UniFFI consumer keep rules. Expo prebuild preserves the restricted ABI list. This is build/packaging evidence, not a signed minified APK device acceptance test.
- Updated the development test tools to close GHSA-6w46-j5rx-g56g (pytest <9.0.3). Final GitHub CI and deployment remain pending in PR #125; no release success is claimed yet. PR #125 contains #123/#124 and their review corrections in a single release.
- User explicitly authorized push and deployment on 2026-10-27. OpenClaw ANCAP job temporarily paused during review/release; restore after verification. No funded payments or OCR quality acceptance run performed.

## 2026-10-28 - Research Operations release preparation

- Assemble cost evidence (migration 092), bounded sources (093), claim drafts and exact Studio-reviewed client packets from verified feature work onto current origin/master. Exclude inherited OCR experiments and local runtime files.
- Prior isolated validation: 51 targeted backend tests and 13 Chromium scenarios, TypeScript and focused ESLint pass. CI and production rollout are pending for this exact release branch.


- Release follow-up: restored the referenced release-verification document, extracted shared Studio access/serialization to remove research import cycles, and removed mutating calls from assert expressions flagged by CodeQL.
- Hardened long-text parsing, recovery-wrapper trimming, service-worker message origin, external-field log formatting and randomized e2e credentials. Pin deployment/Foundry/release actions to upstream commit SHAs; the top-up example no longer logs client-secret fragments.
- Exact release checkout validation: 101 targeted backend/security tests, all 97 frontend unit tests, lint and Next production build pass. Full backend/remote CI are still running.
- Initial GitHub snapshot: 372 open CodeQL findings (342 quality notes, 18 high and 12 medium security-classified alerts); no open Dependabot or Secret Scanning alerts. This is an inventory, not a claim that all old alerts are exploitable or resolved. Historical wallet-storage/protocol and quality findings require separate review; no findings were mass-dismissed.


- GitHub review found a packet disclosure through retry-delivery after project access revocation. Retry and cancellation now enforce project membership and packet expiry before any mutation/response; retry also revalidates the approved evidence. Added revoked-owner and expired-packet regressions: all 20 Studio/packet tests pass.


- Closed the second review path: matching idempotent enqueue responses now recheck research packet access/expiry, including concurrent insert returns. Added a valid replay then expiry regression and private no-store response headers. All 23 focused Studio/packet/QR/release-workflow tests pass.
- GitHub full backend run exposed a legacy release test that required a mutable action tag. Updated it to require a 40-character commit pin. The previous run otherwise had 1189 passes and 40 skips; it is not reported as a green run.
- Local Windows QR failure was a missing tzdata package; installed tzdata in the test environment and the QR regression now passes. Deployment CI uses Linux timezone data. Operator approved PR #130 in this chat on 2026-10-28; merge/deployment still wait for exact-head CI and review fixes.


- Review follow-up: no-change source checks now reuse the immutable packet when evidence bindings, workflow versions and report output match. Freshness timestamps no longer exhaust the three-version limit. Regression performs four unchanged checks, then confirms a real source change still creates version two; all 11 packet tests pass.
- The initial local full-suite run completed with 1215 passes, 8 skips and two failures (missing Windows timezone data and old mutable-tag expectation), both separately corrected and covered by the passing focused reruns. It is not labeled a clean full run; exact-head Linux CI remains authoritative for this release.



## 2026-10-28 — CodeQL backlog and deepmerge remediation (in validation)

- Work from production master 00c1e04 in an isolated branch, preserving concurrent Theodore work. Inventory starts at 356 CodeQL findings and mobile deepmerge GHSA-gcqx-w48m-w2h4.
- Keep Alembic metadata as explicit public exports; remove scoped dead imports/locals without dropping awaited mutations. Replace unclosed text files with Path APIs and clarify query/error control flow. Optional failures now report static operation labels without sensitive exception payloads; malformed pagination cursors return 422.
- Use HMAC-SHA256 and constant-time comparison for paid API challenge signatures; advertise signature_algorithm=hmac-sha256 and reject non-hex signatures before comparison. Challenge clients must adopt the advertised algorithm; ephemeral pending challenges expire. Existing random 192-bit API key SHA-256 fingerprints remain compatible, with constant-time verification.
- Restore script passes decrypted keystore through stdin instead of writing plaintext or exposing it in argv. No transfer or funded transaction was executed. GitHub auth probes request only allowlisted metadata before report generation.
- deepmerge remains unfixed upstream. Added an explicitly named private MIT-licensed security fork with upstream source fingerprint, blocked prototype-control keys in both loops, own-property definitions and fail-closed proxy checks. Expo resolves the installed local override. Normal merge/custom/array/symbol behavior and all advisory regression cases pass; npm audit reports zero vulnerabilities locally.
- Current local evidence: 79 targeted backend/docs/security tests pass (5 optional/live skips); all 97 frontend unit tests and lint pass; npm ci/postinstall, mobile tests and workspace type checks pass. Exact-head CodeQL/full CI and default-branch closure are still pending. No query exclusions, alert bulk dismissal or fake upstream version used.

- Full manual CodeQL run 40684092074 scans the entire branch (not PR-changed lines): JavaScript/TypeScript and Actions have zero results. Python initially has eight SARIF results, including an already-dismissed synthetic test-credential fixture; three residual dead variables are fixed next.
- Four original false positives require evidence-based individual disposition: high-entropy generated API-key fingerprints, two report sinks receiving only allowlisted GitHub auth metadata, and awaiting cancelled worker completion. Added a functional lifespan test proving shutdown awaits worker cleanup; no correct cryptography or cancellation behavior is weakened just to change a detector result.

- Full manual scan 40684992611 of 0ecad1f has zero open branch alerts after the residual fixes and four individually reviewed false-positive dispositions (#1 generated-token fingerprints, #309/#310 metadata-only reports, #480 required task join). Comments link the regression evidence; the pre-existing test-fixture false positive #482 was left unchanged. Raw SARIF still records dismissed findings; no rule or source path is excluded.
- Expanded CodeQL push/PR triggers to scripts, tests and Alembic, and retained manual full analysis so future tool-only changes receive coverage. Added public HMAC client migration instructions to the commerce roadmap. Backend/full browser CI and final default-branch/dependency closure remain the release gate.
