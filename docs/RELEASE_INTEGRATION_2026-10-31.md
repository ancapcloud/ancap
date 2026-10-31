# Release integration — 2026-10-31

Merged the nine published commits with local history; retained the original
homepage design, first-screen AI onboarding, connect.md and account API keys.

ROP-03 fixture work is deferred: handlers omitted project authorization,
referenced a missing project_id field, and migrations were outside the Alembic
version directory with invalid revision references and incompatible columns.
Restored the published research implementation and model pending a dedicated
implementation with isolation tests and a valid migration. Original commits
remain in history and codex/backup-before-release-20261031. Uncommitted
research changes and diagnostics are preserved in the named Git stash and
C:/Users/drago/Desktop/ANCAP-release-backup-20261031.

Restored published PROGRESS.md to avoid losing existing completion evidence.
Wallet privacy receive aggregation and the independent UTXO refresh are retained
for targeted verification. Deployment verification will be recorded below.

## Local verification

- API imports successfully; Alembic has one head: 096_account_api_key.
- 51 targeted backend tests passed on isolated ancap_release_20261031.
- 115 frontend unit tests, TypeScript and production build passed.
- Browser: Russian public AI prompt copy succeeded and API setup CTA opened
  the authenticated setup page with the guest sign-in gate.
- Corrected privacy receive accounting: apply stake/ledger reservations to the
  combined native balance; show combined funds in the hero; fail closed for
  withdrawal when privacy balance is unavailable. Three regression cases pass.
- Removed unused duplicate AgentQuickStart; published CreatorAiConnect remains
  the single first-screen entry. connect.md remains canonical; the existing
  connect.txt compatibility resource is retained.

CI found fresh Expo compatibility requirements: expo 58.0.22,
expo-dev-client 58.0.18, expo-router 58.0.29 and react-native-screens 4.30.1.
Updated both manifests and regenerated the lockfile without bypassing doctor.

Mobile verification: 352 workspace tests and 13 security regressions passed;
SDK builds and workspace type checks passed; Expo Doctor passed 20/20.
Adapted the CLI validation regression to Expo's relocated JSON Schema validator;
valid plugin/output data and malformed data are still checked.

The initial Windows full regression run stalled on DNS inside the balance
breakdown tests' unmocked vesting RPC. Added a module fixture to isolate that
unrelated probe while preserving all accounting assertions. Restarted the full
run against the isolated database; the interrupted run is not counted as passed.

## Published release

PR: https://github.com/ancapcloud/ancap/pull/137
Release: c777417d5cd9c6ca4b27a67793feb49ac95c0841.
Deployment: https://github.com/ancapcloud/ancap/actions/runs/41203678588
completed successfully on 2026-10-31.

All PR checks passed, including browser e2e. Backend CI recorded 1251 passed,
40 skipped, plus 60 documentation regression tests passed and 5 skipped.
Backend CI: https://github.com/ancapcloud/ancap/actions/runs/41202980429
Frontend/mobile/e2e: https://github.com/ancapcloud/ancap/actions/runs/41202980343

Public verification after deployment:
- /internal/frontend-build reports c777417 from .next/BUILD_ID.
- /api/v1/system/health: ok; /api/v1/system/ready: ready, database/Redis true.
- /connect.md and /developers/connect return HTTP 200.
- All five home locales return HTTP 200 with one AI connection block,
  connect.md and the original design. Published Russian home inspected visually.

Merged the outstanding account-key release evidence from local branch
codex/publish-ai-connect (81a1517d); it contains documentation only.
This follow-up evidence commit changes no application/deployment code.
Incomplete ROP-03 work remains preserved, not deployed or represented as complete.
