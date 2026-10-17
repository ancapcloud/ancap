# ACP Wallet — Device Verification Evidence — 2026-10-17

Filled from `docs/mobile/DEVICE_VERIFICATION_EVIDENCE_TEMPLATE.md`.

## Verification round metadata

- Date: 2026-10-17
- Operator: Cursor agent (local Windows host)
- Commit SHA: `23267af` (+ follow-up vault smoke / Smart Pay commits in same session)
- App version: `0.1.0` (Expo debug)
- Android build number: debug APK via `npx expo run:android`
- iOS build number: n/a (macOS host required)
- Backend/API target: `https://ancap.cloud` / `https://acp1.ancap.cloud/rpc`
- Native artifact source:
  - Android `.so`: UniFFI linked in `expo-acp-core` jniLibs (prior build)
  - iOS xcframework: **not run** this round

## Device / run entries

### Run 1 — Android emulator

- Platform: Android
- Device / emulator: AVD `Pixel_10_Pro` (`sdk_gphone16k_x86_64`)
- OS version: Android 17 (API reported by emulator image)
- Build type: Expo development client debug APK
- Native core status: create/import keystore path linked
- Install / launch result: **pass** (`BUILD SUCCESSFUL`, package `cloud.ancap.acpwallet`)
- Notes: Metro + embedded bundle both observed after `pm clear`

| Scenario | Result | Evidence | Notes |
|---|---|---|---|
| Create wallet via native FFI | pass | `vault-external-restore-smoke.ps1` → `CREATED=acp1qp0caf…` | |
| Copy keystore export file | pass | smoke pulled `files/acp-keystore-export.json` | |
| Import existing wallet (export file) | pass | `SMOKE_OK=True ADDR=acp1qp0cafp446yzxh7ex5s5h2vp9xljldkkyud0h65p` | keystore-only, no mnemonic |
| Restart persistence | pass | `HOME3=` same address | |
| Send / local sign UI | blocked | `sign-local-smoke.ps1` | UTXOs: 0 — funded sign needs operator test ACP; Alert dialog not captured reliably by uiautomator |
| PIN / biometric | n/a | — | Physical device required |
| MASVS L1 device closure | n/a | — | Physical / release build required |
| Play Internal / TestFlight | n/a | — | Operator credentials / store listing |

Failure classification:
- Repo bug: none for create/restore path
- Host/tooling blocker: none for Android emulator
- Distribution blocker: Play/TestFlight uploads
- Hardware/access blocker: physical PIN/biometrics + iOS macOS packaging + funded ACP for sign/broadcast

## Scripts used

- `ancap-mobile/scripts/start-android-test-env.ps1`
- `ancap-mobile/apps/acp-wallet-expo/scripts/vault-external-restore-smoke.ps1` → `SMOKE_OK=True`
- `ancap-mobile/apps/acp-wallet-expo/scripts/sign-local-smoke.ps1` (UI path; funded UTXO still open)
