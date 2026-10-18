# ACP Wallet — local Android test environment

> Updated: 2026-09-11
> Clears the previous hard blocker: “no test environment / no device access”.

## Ready now

| Item | Status |
|------|--------|
| Android SDK | `C:\Users\drago\AppData\Local\Android\Sdk` |
| AVD | `Pixel_10_Pro` |
| Start script | `ancap-mobile/scripts/start-android-test-env.ps1` |
| Native `.so` | already emitted via `build-android-native.ps1` |

```powershell
powershell -NoProfile -File ancap-mobile/scripts/start-android-test-env.ps1
# hung / high-CPU qemu: soft restart
powershell -NoProfile -File ancap-mobile/scripts/start-android-test-env.ps1 -Restart
# factory reset AVD data if still broken
powershell -NoProfile -File ancap-mobile/scripts/start-android-test-env.ps1 -WipeData
cd ancap-mobile/apps/acp-wallet-expo
npx expo run:android
```

## What is NOT a work-stop blocker anymore

- Missing local device / emulator access — **cleared** (AVD + script).
- “No test environment” — **cleared**.

## Still open (operator / release gates, do not freeze coding)

- Play Internal / TestFlight upload credentials and listing assets
- Physical-phone biometrics / MASVS on-device sign-off
- iOS packaging (macOS/Xcode, P1-7)

Theodore / progress bots: **do not** report device/test-env as a blocker. **Do not** report missing `README.md` (root file exists). **Do not** report “monetization after the first ACP cycle” as a blocker. Report store/physical/iOS only as follow-ups.

## Audit follow-up: native encryption build (2026-10-17)

This follow-up supersedes the earlier blanket "store/physical/iOS only"
statement above. Target API 34 in the debug artifact requires a validated API
36+ stack migration before Play submission, plus full-artifact 16 KB evidence
and release signing. These are engineering gates; see RELEASE_CHECKLIST.md.

Encrypted backup adds UniFFI exports and two Expo modules. Regenerate Kotlin and
Swift bindings from the current host library, stage Kotlin in expo-acp-core,
run build-android-native.ps1, then rebuild/install the native app. An OTA/Metro
refresh alone cannot add the new native methods. Older clients fail closed on
backup operations rather than copying plaintext keys.

Gradle's org.gradle.java.installations.paths uses a comma-separated list. Use an
installed JDK 17 for the RN settings plugin; a JBR 21 launcher alone does not
satisfy that toolchain requirement. On this host C:/jdk-17 exists. If needed,
pass explicit -Dorg.gradle.java.home and -Dorg.gradle.java.installations.paths
when invoking gradlew; do not treat failed toolchain auto-provisioning as a code
or device failure. Never reuse an older .so after a failed cargo build.

Recovery smoke requires a disposable emulator wallet:
`vault-external-restore-smoke.ps1 -AllowTestWalletReset`.
The flag authorizes resetting that test wallet, and the script additionally
requires exactly Pixel_10_Pro. It copies an encrypted envelope outside the app,
clears test-app state, and restores with a test-only password. It does not prove
system-picker/SAF behavior, a release variant or funded signing. Preserve those
as separate evidence rows. `vault-gen-smoke.ps1` delegates to the same scenario.

UniFFI 0.28 also generates an error-payload field named message that conflicts
with Kotlin Exception.message. `ACP-crypto/scripts/uniffi-generate.ps1` now
applies `fix-uniffi-kotlin.ps1` deterministically and stages the Android source.
The fix only renames the Kotlin payload property to details and updates its
converter; Rust/Swift API names, serialization order and wire bytes stay intact.
Do not copy freshly generated raw Kotlin into the module without that fix.

Native RPC uses bundled WebPKI roots with TLS validation enabled. Chain ID is
read through public getbestblockhash/getblock; getnetworkinfo is operator-only.
Never put ACP_RPC_TOKEN into an Expo public variable or the mobile binary.
