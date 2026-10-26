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

## Validation so far

- All workspace SDK builds and typechecks pass on TypeScript 6.
- 352 existing mobile tests and 5 security/CLI compatibility checks pass.
- Expo Doctor: 19/19 enabled checks pass.
- Android Hermes export: 1,607 modules, successful.
- Local native Android assembly and isolated emulator smoke are in progress. The x86_64 Rust .so is staged from the existing local build; this migration does not rebuild Rust or claim fresh Rust artifact provenance.
- iOS/Xcode and physical NFC/Bluetooth/biometric validation remain separate release gates; Windows cannot establish those results.

No production deployment, store upload, funded transaction or wallet-data reset is part of this migration.
