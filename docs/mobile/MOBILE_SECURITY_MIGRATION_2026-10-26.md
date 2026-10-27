> Update 2026-10-27: the revenue-execution release aligns the latest Expo 58 patch recommendations and locks node-forge 1.4.2. The obsolete 1.4.0 source backport is removed; the RSA malformed-DigestAlgorithm regression tests remain and pass against upstream code. npm audit reports zero mobile dependency vulnerabilities at this check. [Upstream release](https://github.com/digitalbazaar/forge/releases/tag/v1.4.2). Native APK/16 KB/device evidence below applies to the dated 2026-10-26 dependency set; it is not a new native/store sign-off for these patches.

# Mobile security migration — 2026-10-26

## Scope

Upgrade the mobile workspace from Expo 52 / React Native 0.76.6 / React 18.3.1 to Expo 58.0.19 / React Native 0.88.0 / React 19.3.0. Use TypeScript 6.0.3 and Node 24 in CI (supported Node engine ranges are declared in package.json).

The npm workspace uses Expo's normal Metro/autolinking resolution. Remove the old React/React Native overrides and direct installation of Expo's internal dev-launcher/menu/interface packages. Update NFC manager to 4.1 and BLE to 3.5. Navigation focus hooks come from expo-router; the backup implementation explicitly imports the supported expo-file-system/legacy compatibility API, including Android SAF.

## Security evidence

- image-size is absent from the new dependency graph.
- Zod is overridden only for @expo/cli to ^4.6.7. Tests exercise the CLI's actual plugin and MCP schema validators with accepted/rejected inputs to verify compatibility across this major dependency change.
- node-forge 1.4.0 still has no fixed npm release for GHSA-86w9-cpqp-85rv / CVE-2026-85393. Even Expo 58 depends on it through @expo/code-signing-certificates.
- scripts/apply-security-patches.cjs backports the nested DigestAlgorithm element-count check from digitalbazaar/forge PR 1152. It accepts only the known original/patched SHA-256 of lib/rsa.js and fails installation on another source/version. It runs before the workspace build in postinstall.
- scripts/node-forge-security.test.cjs reproduces both malformed nested encodings on the original release (2 failing checks before the fix), rejects both after the fix, and preserves normal/optional-NULL SHA-256 signatures.
- Package versions and advisory metadata are not rewritten. Raw npm audit still exits 1 with four high entries: node-forge and its three Expo parent packages, all caused by that one backported advisory. There are no other advisory entries in the current audit. Do not describe this as zero registry advisories.

Sources: https://github.com/advisories/GHSA-86w9-cpqp-85rv ; https://github.com/digitalbazaar/forge/pull/1152 ; https://github.com/advisories/GHSA-mrhx-c7xc-m3w5 ; https://expo.dev/changelog/sdk-58

## Native build and configuration

Android is regenerated from the SDK 58 template with New Architecture, compile API 37 and target API 36. expo-acp-core uses expo-module-gradle-plugin, retaining UniFFI and the staged Rust library. JNA is upgraded from 5.14.0 to 5.19.1, including the Android 16 KB page-size fixes (https://github.com/java-native-access/jna/blob/master/CHANGES.md). No wallet serialization or chain protocol change is made.

expo-dev-client enables its supported embeddedBundle option (the launcher offers Load embedded bundle). plugins/with-wallet-android.js reapplies embedded debug bundles and fail-closed release signing. A release must have a distinct operator upload key; the generated template's debug key is cleared. The optional Gradle property ancap.testApplicationIdSuffix is debug-only and allows an emulator smoke under .securitycheck without replacing an existing wallet.

The project commits generated Android files. npm run android invokes prebuild:android before the native build, and the config plugin preserves wallet constraints when regenerating. Expo Doctor's appConfigFieldsNotSyncedCheck is explicitly disabled for this managed, committed native tree; all 19 remaining checks pass. This is a configuration-workflow warning, not a disabled dependency/security check.

## Validation

- All workspace SDK builds and typechecks pass on TypeScript 6.
- 352 existing mobile tests and 5 security/CLI compatibility checks pass.
- Expo Doctor: 19/19 enabled checks pass.
- Android Hermes export: 1,607 modules, successful.
- Native Android assembly passes. All 31 x86_64 APK libraries have LOAD alignment >=16,384 bytes; SDK zipalign -c -P 16 also passes.
- Rust FFI rebuilt from the current locked dependencies with NDK 28.0.13004108 for x86_64 and ARM64. Both fresh libraries have 16 KB alignment. APK merge/strip outputs match the freshly built x86_64 library, excluding reuse of the older local binary.
- NativeKeystoreCompatibilityTest passes on the Pixel_10_Pro emulator: pageSize=16,384, JNA=5.19.1, disposable wallet creation, encrypted backup/address recovery and wrong-password rejection. It uses no RPC or real vault.
- The isolated .securitycheck app launches its embedded JS bundle through the supported dev launcher, reaching the Create new wallet / Import wallet welcome screen after Nearby Devices permission is denied. The real wallet package is preserved.
- preReleaseBuild fails closed when no operator upload key is configured. Two prebuild runs produce an identical root Gradle policy.
- Windows CMake object staging uses C:\.ancap-cxx/<project-path hash>/<module> and CMAKE_OBJECT_PATH_MAX=240, registered before React's root plugin evaluates child projects. This avoids Ninja MAX_PATH errors without changing Windows registry or disabling New Architecture. Override the cache root with -Pancap.nativeBuildRoot if needed. See https://docs.swmansion.com/react-native-reanimated/docs/guides/building-on-windows/.
- Machine-readable evidence: evidence/mobile-security-sdk58-2026-10-26.json (code revision 0682b2f12fc86862197f16ab57c77623117c87f5).
- iOS/Xcode and physical NFC/Bluetooth/biometric validation remain separate release gates; Windows cannot establish those results.

No production deployment, store upload, funded transaction or wallet-data reset is part of this migration.

### Re-run the native check

Stage current Rust libraries with scripts/build-android-native.ps1 first. In apps/acp-wallet-expo/android run `gradlew :app:assembleDebug :expo-acp-core:assembleDebugAndroidTest -PreactNativeArchitectures=x86_64 -Pancap.testApplicationIdSuffix=.securitycheck`. Install the module's debug androidTest APK with `adb -s <test-emulator> install -t <test-apk>`, then run `adb -s <test-emulator> shell am instrument -w -e class expo.modules.acpcore.NativeKeystoreCompatibilityTest expo.modules.acpcore.test/androidx.test.runner.AndroidJUnitRunner`. Check that the target test packages are absent before installing; do not reset or replace a real wallet. The test creates keys only in memory and never funds them.
