# Android wallet stack — inventory and migration — 2026-10-21

This is the release gate after `ab32ea0`. It does not close Play Internal,
a physical-device PIN/biometric run, or an iOS/TestFlight build. iOS stays on
macOS. A `targetSdk` number change by itself is not this migration.

## What is in the tree now

| Piece | Current | Source |
| --- | --- | --- |
| Expo | `~52.0.28` | `ancap-mobile/apps/acp-wallet-expo/package.json` |
| React Native | `0.76.6` | same, and the workspace override |
| React | `18.3.1` | same |
| Metro | `0.81.5` | `ancap-mobile/package-lock.json` |
| Gradle wrapper | `8.10.2` | `android/gradle/wrapper/gradle-wrapper.properties` |
| Android Gradle Plugin | `8.8.2` | `android/build.gradle` |
| Kotlin | `1.9.24` | `android/build.gradle` and `gradle/libs.versions.toml` |
| compileSdk | `35` | `android/build.gradle` |
| targetSdk | `34` | `android/build.gradle` (`libs.versions.toml` agrees) |
| minSdk | `24` | same |
| NDK used by the app Gradle | `27.1.12297006` | `android/build.gradle` |
| NDK in the version catalog | `26.1.10909125` | `android/gradle/libs.versions.toml` |
| UniFFI | `0.28` | `ACP-crypto/acp-mobile-ffi/Cargo.toml` |
| App id | `cloud.ancap.acpwallet` | `android/app/build.gradle` |
| version | name `1.0.0`, code `1` | same |

The app Gradle file wins over the catalog for NDK. Both numbers stay recorded
so a later edit does not silently follow the catalog.

Native modules wired by the Expo app:

- `expo-acp-core` (UniFFI Kotlin + `libacp_mobile_ffi.so`)
- `expo-dev-client`, `expo-dev-launcher`, `expo-dev-menu`
- `expo-camera`, `expo-document-picker`, `expo-file-system`, `expo-image-picker`, `expo-sharing`
- `expo-local-authentication`, `expo-secure-store`, `expo-crypto`, `expo-screen-capture`
- `expo-router`, `expo-linking`, `expo-clipboard`, `expo-asset`, `expo-status-bar`
- `react-native-ble-plx`, `react-native-nfc-manager`, `react-native-svg`, `react-native-qrcode-svg`
- `react-native-safe-area-context`, `react-native-screens`

Release signing already fails closed: `:app:verifyReleaseSigning` rejects the
template debug key. An operator upload key is required and must not be committed.

## Play and 16 KB requirements checked 2026-10-21

- New apps and updates submitted to Google Play must target Android 16 (API 36) from 31 August 2026. Wear OS and Android Automotive are API 35; Android TV and Android XR are API 34. An extension to 1 November 2026 can be requested in Play Console. Sources: [Play Console Help](https://support.google.com/googleplay/android-developer/answer/11926878) and [Android target API guidance](https://developer.android.com/google/play/requirements/target-sdk).
- Apps targeting API 35 or higher must support 16 KB pages on 64-bit devices. From 1 February 2027, Play blocks updates that do not. Source: [Android 16 KB page sizes](https://developer.android.com/guide/practices/page-sizes).
- Expo SDK 52 compiles with SDK 35 and targets 34. The selected migration target is Expo SDK 54, which targets API 36 by default (React Native 0.81, React 19.1.0, compileSdk 36, targetSdk 36, iOS 15.1, Xcode 16.1, Node 20.19.4 minimum). Sources: [Expo SDK 54 changelog](https://expo.dev/changelog/sdk-54) and [Expo SDK reference](https://docs.expo.dev/versions/v54.0.0).
- SDK 54 turns edge-to-edge on for every Android app. Predictive back stays opt-in.

The audited debug APK still targets API 34 and has native libraries aligned to 4 KB. That artifact cannot be the Play upload.

## Migration order

Do this as one reviewed stack, not a lone `targetSdk` edit.

1. Inventory lock: record Expo, RN, React, Gradle, AGP, Kotlin, NDK, and every native module above. This document is that inventory.
2. Upgrade the JS toolchain to Expo SDK 54 with `npx expo install --fix`, then regenerate `package-lock.json`. Keep the workspace on one React and React Native version.
3. Let Expo prebuild refresh Gradle, AGP, Kotlin, compileSdk and targetSdk together. Resolve the NDK catalog/app mismatch in that same change. Do not leave `libs.versions.toml` on NDK 26 while the app file forces 27, or the reverse, without saying which file wins.
4. Rebuild `libacp_mobile_ffi.so` with `--locked` for `arm64-v8a`, `armeabi-v7a` and `x86_64`. Regenerate UniFFI 0.28 Kotlin and review the diff, including the existing message-field workaround. Drop unexpected ABIs that dependencies still package.
5. Re-test, in this order: unit and typecheck; native keystore roundtrip; create wallet; encrypted export; cancel the system picker; fresh-state import through the system file picker; restart; crash before and after the vault pointer commit; sign-only. Funded broadcast stays a separate operator ACP test.
6. Build a release AAB with the operator upload key. `:app:verifyReleaseSigning` must pass. Record versionCode, ABI list and the SHA-256 of the AAB.
7. Check every bundled `.so` for 16 KB `PT_LOAD` alignment, then install a 16 KB system image and confirm `adb shell getconf PAGE_SIZE` is `16384`. ELF alignment is not that runtime check.
8. On a physical Android device: PIN success, wrong PIN, biometric success, biometric cancel, lockout, background lock, process death, and restore. Play Internal is closed only after the store artifact is uploaded and that same artifact is installed.

## What this pass did not run

- No release AAB. The signing guard is still in place and no upload key is in git.
- No Play Console upload or install.
- No physical PIN or biometric run.
- No iOS/TestFlight build. That remains a macOS job.
- No Expo SDK upgrade in this change. PR #96 showed an unfinished 52-to-58 jump and was closed. The next code change starts at step 2 above and keeps the wallet tests green at each step.

Prior emulator evidence remains in `docs/mobile/ENGINEERING_AUDIT_2026-10-17.md`: encrypted restore on `Pixel_10_Pro` through a host pull, not the system picker, and sign-only stopped at `funding_required`.
