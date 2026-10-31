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
