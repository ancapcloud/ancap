# Physical MASVS / store handoff — 2026-10-17

Engineering closed what it can without a physical device, Apple Developer / Play Console credentials, or macOS.

## Done in-repo

- SecureVault chunking + export wipe + honest Copy messaging (commit `b9a3fb2`)
- Android emulator create → keystore export → restore (`SMOKE_OK`) — `docs/mobile/device-evidence-2026-10-17.md`
- MASVS L1 **repo baseline** remains closed in `docs/mobile/SECURITY_MODEL.md`
- Release checklists: `docs/mobile/RELEASE_CHECKLIST.md`, `RELEASE_RUNBOOK.md`

## Operator-only remaining

| Item | Blocker |
|------|---------|
| Physical PIN + biometrics + SecureVault biometric gate | Hardware device |
| MASVS L1 device-closure rows (M3/M5/M11 as listed) | Physical + release build |
| Play Internal upload | Play Console listing/credentials |
| TestFlight + iOS native (`build-ios-native.ps1`) | macOS/Xcode + Apple account |
| Funded local-sign + broadcast | Operator test ACP (UTXOs > 0) |

Do **not** mark P5-1 / P6-4 / P6-6 `[x]` until the evidence packet above is filled for a physical device and store uploads land.
