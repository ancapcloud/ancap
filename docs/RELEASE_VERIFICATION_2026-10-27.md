# Verified web/API release — 2026-10-27

- Release commit: `e2e88edca121c0677fe1801859953ee5b56e02ee`.
- [Merged repair PR #125](https://github.com/ancapcloud/ancap/pull/125): all 18 checks passed at head `8dc743f9b3b94e16e164a2260809fab1f37f245c`; all triggered master workflows subsequently passed.
- [Successful production deployment](https://github.com/ancapcloud/ancap/actions/runs/40471722354).
- Public `/internal/frontend-build` reports `e2e88ed` from the actual Next build file, matching the deployed commit.
- `/api/v1/system/health`: `ok`; `/api/v1/system/ready`: `ready`, database and Redis true.
- `/`, `/ai/workflows`, `/pricing`, `/payment-scanner`, `/login`: HTTP 200 and HTML pages with titles. Homepage verified in the browser after reloading.

The repair addresses exact catalogue parity, locale regeneration/fallback/live domain bindings, prototype pollution, Android JNA/UniFFI consumer keep rules, unsupported x86 advertising and the pytest advisory. Local validation includes 83 frontend tests, lint/type checks/production build, 38 targeted Python tests, nine workflow-store API tests plus nine pricing tests on an isolated PostgreSQL, and Android release AAR consumer-rule packaging. Earlier native 16 KB device evidence remains in the mobile migration report.

Nine of ten previous GitHub dependency alerts closed after integration. GHSA-86w9-cpqp-85rv remains an upstream node-forge alert: the source-hash-checked backport is applied and tested; no patched npm release is claimed.

The standard recover workflow rebuilt API and frontend and ran migrations/readiness/provenance/RPC checks. It did not rebuild the existing ACP node image or publish mobile binaries. Physical NFC/BLE/biometric/ARM64 device checks, iOS and payment-grade OCR acceptance remain separate gates. No real funds were transferred.

Original local Theodore reports/checker were preserved in Git stash and `C:\Users\drago\.openclaw\repair-20261026\theodore-originals-20261027`. Read-only public smoke evidence is stored at `C:\Users\drago\.openclaw\repair-20261026\theodore-production-verification.json`. The working checkout is on a dedicated development branch based on the published release; this evidence-only follow-up does not require another production image rebuild.
