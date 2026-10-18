# ACP Wallet — Release Readiness Checklist

> Status: release-closure scaffold added on 2026-05-28
> Roadmap link: `docs/mobile/ROADMAP.md` → P6-4, P6-5, P6-6
> Companion templates: `docs/mobile/DEVICE_VERIFICATION_EVIDENCE_TEMPLATE.md`, `docs/mobile/RELEASE_EVIDENCE_PACKET_TEMPLATE.md`
> Scope: internal-distribution prep, listing/legal pack, and honest v1.0.0 release gates.

This file is intentionally practical: it records what the repo already has, what can be prepared inside the repo, and what still requires external execution.

## Repo-ready inputs already present

- Expo app config exists in `ancap-mobile/apps/acp-wallet-expo/app.json`.
- Current mobile app identifiers are already set:
  - iOS bundle ID: `cloud.ancap.acpwallet`
  - Android package: `cloud.ancap.acpwallet`
  - app version: `1.0.0`
- Mobile product/spec/security docs already exist in `docs/mobile/`.
- Public legal web pages already exist in the frontend codebase:
  - `/legal/terms`
  - `/legal/privacy`
  - `/legal/cookies`

## P6-4 — TestFlight + Play Internal

### Entry conditions

- [ ] Migrate and validate the Android dependency/toolchain stack for target API 36 or higher. The audited debug APK still targets API 34. Google Play requires API 36 for new phone apps/updates from 2026-08-31 ([official policy](https://support.google.com/googleplay/android-developer/answer/11926878?hl=en)); this is an engineering gate before submission.
- [ ] Verify 16 KB page-size compatibility for the complete release artifact, including React Native/Expo and every bundled native library, on a matching device/emulator ([Android guidance](https://developer.android.com/guide/practices/page-sizes)). A Rust NDK build alone is insufficient evidence.
  Debug APK audit found 12 arm64 dependencies with 4 KB ELF LOAD alignment, including RN/Hermes/barhopper; migrate these dependencies and validate ZIP/AAB packaging plus runtime. See ENGINEERING_AUDIT_2026-10-17.md.
- [ ] Configure operator-owned release signing and pass `:app:verifyReleaseSigning`. The checked-in debug signing configuration is deliberately rejected for release builds; do not bypass the guard.

- [x] Android native `.so` artifacts built via `ancap-mobile/scripts/build-android-native.ps1` on the current Windows host
- [~] Android Expo dev-build verification on Windows host (`npx expo run:android` against packaged `expo-acp-core`) — run before Play Internal upload
- [ ] iOS native artifacts packaged via `ancap-mobile/scripts/build-ios-native.ps1`
- [ ] Device matrix execution started from `docs/mobile/DEVICE_MATRIX.md`
- [ ] Native create/send/sign path verified in dev builds

### Internal-distribution checklist

- [ ] Produce Android release-candidate build for internal testing
- [ ] Produce iOS release-candidate build for internal testing
- [ ] Upload Android build to Play Console Internal testing
- [ ] Upload iOS build to TestFlight
- [ ] Record build numbers, artifact names, and tester notes
- [ ] Triage and fix any blocking crash, signing, storage, or biometric regressions

### Honest status rule

P6-4 can be treated as `[~]` once the checklist and build path are prepared in-repo, but it must stay `[~]` until at least one real TestFlight upload and one real Play Internal upload have been completed.

When those uploads happen, record the artifact/build ids and tester notes in a filled copy of `docs/mobile/RELEASE_EVIDENCE_PACKET_TEMPLATE.md` instead of leaving them only in operator memory.

To bootstrap a dated working copy without hand-editing the template header each time, run:
- `python scripts/generate_mobile_release_evidence_packet.py`
- optional Windows launcher-only equivalent: `py -3 scripts/generate_mobile_release_evidence_packet.py`
- optional custom output example: `python scripts/generate_mobile_release_evidence_packet.py --date-label 2026-06-02 --operator ARDO --tag-or-release-branch release/mobile-v1.0.0`

The generator writes a dated markdown packet (default: `docs/mobile/release-evidence-v1.0.0-YYYY-MM-DD.md`) from the checked-in template, pre-fills release metadata fields you provide on the command line, appends bootstrap metadata with app/repo provenance, and refreshes the stable alias `docs/mobile/release-evidence-v1.0.0-latest.md` by default so the newest release packet has a fixed handoff path. Pass `--no-write-latest-alias` if you intentionally want a dated packet without touching that stable alias.

## P6-5 — Store listing + legal pages

### Already true

- [x] Legal routes exist for Terms, Privacy, and Cookies in the web app.
- [x] Mobile wallet PRD / spec / security docs exist for release support material.
- [x] Finance/non-custodial positioning is already defined in `docs/mobile/ACP_WALLET_PRD.md`.

### Final listing/legal pack still required

- [ ] Final operator legal entity details inserted into legal pages/templates where still placeholder text remains
- [ ] Final support contact and escalation path confirmed for production
- [ ] App icon / screenshots / preview media prepared for iPhone and Android phone form factors
- [ ] Short description, long description, keywords, category copy, and risk disclosures finalized
- [ ] Store privacy questionnaire answered from the real deployed telemetry/logging posture
- [ ] Export/compliance declarations reviewed against final release scope and jurisdictions

### Reference copy baseline

- Category: **Finance**
- Positioning: **non-custodial ACP wallet**
- Core claims allowed: store, receive, send, local signing, bridge visibility, Smart Pay beta only if clearly labeled beta
- Claims not allowed: exchange, investment promises, autonomous sending, or shipped AI payment execution beyond current truth

## P6-6 — Production v1.0.0 release gate

The repo-side runbook for this final gate now lives in `docs/mobile/RELEASE_RUNBOOK.md`.

Do **not** mark P6-6 done until all of the following are true:

- [x] Android native build path verified on a host with Android NDK
- [ ] iOS native packaging verified on macOS/Xcode
- [ ] Device matrix complete on required physical devices
- [ ] PIN / biometrics / SecureVault migration verified on real devices
- [ ] Native create/send/sign/broadcast path verified end-to-end
- [ ] TestFlight and Play Internal runs completed and blocking issues resolved
- [ ] Listing/legal pack finalized with real operator/support details
- [ ] Release notes / versioning / rollback plan prepared per `docs/mobile/RELEASE_RUNBOOK.md`

## Current blockers snapshot

As of 2026-09-11:

- **Cleared:** no local test environment / no Android device access — use `ancap-mobile/scripts/start-android-test-env.ps1` (`Pixel_10_Pro`). Details: `docs/mobile/ANDROID_TEST_ENV.md`.
- **Still open (not a coding freeze):** Play Internal / TestFlight uploads, physical-phone biometrics/MASVS, iOS macOS packaging.

Evidence packets:

- per-device/runtime results in `docs/mobile/DEVICE_VERIFICATION_EVIDENCE_TEMPLATE.md`
- final release/build/upload evidence in `docs/mobile/RELEASE_EVIDENCE_PACKET_TEMPLATE.md`
