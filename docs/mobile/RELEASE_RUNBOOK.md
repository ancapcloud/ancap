# ACP Wallet — v1.0.0 Release Runbook

> Status: release-gate scaffold added on 2026-05-28
> Roadmap link: `docs/mobile/ROADMAP.md` → P6-6
> Companion docs: `docs/mobile/DEVICE_MATRIX.md`, `docs/mobile/RELEASE_CHECKLIST.md`, `docs/mobile/DEVICE_VERIFICATION_EVIDENCE_TEMPLATE.md`, `docs/mobile/RELEASE_EVIDENCE_PACKET_TEMPLATE.md`, `docs/mobile/SECURITY_MODEL.md`, `.github/RELEASE_PROCESS.md`
> Purpose: define the operator steps, evidence, release notes, versioning, and rollback artifacts required before marking mobile `P6-6` done.

Current truth:

- Audit follow-up (2026-10-17): the debug APK builds, but target API 34 requires a validated API 36+ stack migration before Play submission; see the linked policy and acceptance gates in `RELEASE_CHECKLIST.md`. Release signing must pass `:app:verifyReleaseSigning`, and full-artifact 16 KB compatibility remains unverified.

- The repo already has a generic release workflow and release-process doc for the wider ANCAP stack.
- The mobile wallet now also has an explicit release runbook, but that does **not** mean the wallet is release-ready yet.
- The final mobile `v1.0.0` cut is still blocked by Android NDK-backed native artifacts, macOS/Xcode iOS packaging, real device verification, internal store uploads, and final operator/legal assets.

## Version truth and identifiers

Use the current app config as the source of truth unless a deliberate version bump is committed first:

- App name: `ANCAP ACP Wallet`
- Version: `1.0.0`
- iOS bundle ID: `cloud.ancap.acpwallet`
- Android package: `cloud.ancap.acpwallet`
- URL scheme: `acpwallet`

If the release candidate needs a version change, update `ancap-mobile/apps/acp-wallet-expo/app.json` first and make the release notes reflect the same version.

## P6-6 entry gate

Do **not** start the final cut until all upstream release-closure inputs are already satisfied or actively evidenced:

1. `docs/mobile/DEVICE_MATRIX.md` has real execution results for the required Android and iOS rows.
2. `docs/mobile/RELEASE_CHECKLIST.md` has real TestFlight / Play Internal upload evidence instead of placeholders.
3. Native create / send / sign / broadcast flows are verified on real hardware.
4. PIN / biometrics / SecureVault migration have passed on physical devices.
5. Final operator/support/legal details are ready for store metadata and legal pages.

## Release evidence packet

Start from `docs/mobile/RELEASE_EVIDENCE_PACKET_TEMPLATE.md` so the final gate is recorded in one repeatable format instead of being reconstructed from scattered checklist edits.

To bootstrap a dated working copy without hand-editing the template header each time, run:
- `python scripts/generate_mobile_release_evidence_packet.py`
- optional Windows launcher-only equivalent: `py -3 scripts/generate_mobile_release_evidence_packet.py`
- optional custom output example: `python scripts/generate_mobile_release_evidence_packet.py --date-label 2026-06-02 --operator ARDO --tag-or-release-branch release/mobile-v1.0.0`

By default the generator writes `docs/mobile/release-evidence-v1.0.0-YYYY-MM-DD.md`, appends bootstrap metadata with app/repo provenance, and refreshes the stable alias `docs/mobile/release-evidence-v1.0.0-latest.md` so release handoff can reference a fixed latest path without replacing the dated evidence-of-record. Pass `--no-write-latest-alias` if you intentionally want only the dated packet.

Prepare a release packet for the final mobile cut. At minimum it should include:

- target commit SHA
- app version and build numbers
- device matrix results
- TestFlight build identifier + tester notes
- Play Console Internal testing artifact + tester notes
- final store-listing text/assets location
- release-notes artifact path
- rollback contact/owner and previous known-good build references

Keep this packet in-repo or in the release notes attachment path referenced by the release PR/tag notes.

## Release notes convention

Use the repo's existing release-notes convention from `.github/RELEASE_PROCESS.md`:

- artifact path: `docs/RELEASE_<VERSION>.md`
- include a dedicated **Mobile wallet** section covering:
  - supported scope: non-custodial ACP wallet, local signing, bridge visibility, Smart Pay beta only if still beta
  - required warnings: no investment promises, no autonomous sending, no false claim that AI payment execution is fully shipped
  - native/device verification summary
  - known limitations and any beta-labeled surfaces

Minimum mobile release-notes sections:

1. build/version summary
2. verified devices/platforms
3. native-signing verification summary
4. security controls verified on device
5. store-distribution status
6. known limitations / deferred items
7. rollback owner + rollback path

## Rollback plan

Before the final cut, record a rollback plan that is specific to the mobile release:

- keep the previous known-good Android artifact/build number
- keep the previous known-good iOS/TestFlight build number
- preserve the commit SHA and dependency lock state for the prior good candidate
- define who pauses rollout and where the decision is recorded
- if a blocker appears after internal/store rollout, stop promotion, document the issue, and either:
  - resubmit a hotfix build from a new tagged commit, or
  - fall back to the prior known-good candidate where the store/distribution path allows it

The rollback plan must reference both the mobile artifact identifiers and the repo commit/tag that produced them.

## Final operator sequence

1. Confirm `DEVICE_MATRIX.md` and `RELEASE_CHECKLIST.md` are filled with real evidence.
2. Fill or update `docs/mobile/DEVICE_VERIFICATION_EVIDENCE_TEMPLATE.md` for the current verification round (optionally bootstrap the dated copy first via `python scripts/generate_mobile_device_verification_packet.py`, or `py -3 ...` on launcher-only Windows hosts).
3. Prepare/update `docs/RELEASE_<VERSION>.md` with the mobile wallet section.
4. Record Android and iOS build identifiers in the release packet created from `docs/mobile/RELEASE_EVIDENCE_PACKET_TEMPLATE.md`.
5. Verify store metadata/legal/support details match the shipped build.
6. Cut/push the final release tag only after the mobile evidence packet is complete.
7. Mark `P6-6` done in roadmap docs only after the real cut is complete.

## Honest status rule

This runbook is only the repo-side scaffold for the final release gate. `P6-6` must remain in progress until the external execution steps above are actually completed.
