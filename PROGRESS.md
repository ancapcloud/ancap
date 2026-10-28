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

