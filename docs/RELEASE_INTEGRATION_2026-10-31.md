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
