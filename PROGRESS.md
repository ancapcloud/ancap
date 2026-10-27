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
