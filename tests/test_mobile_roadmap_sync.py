import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MASTER = REPO_ROOT / "MASTER_ROADMAP.md"
MOBILE_ROADMAP = REPO_ROOT / "docs" / "mobile" / "ROADMAP.md"
STATUS_MATRIX = REPO_ROOT / "docs" / "STATUS_MATRIX.md"
DEVICE_MATRIX = REPO_ROOT / "docs" / "mobile" / "DEVICE_MATRIX.md"
RELEASE_CHECKLIST = REPO_ROOT / "docs" / "mobile" / "RELEASE_CHECKLIST.md"
RELEASE_RUNBOOK = REPO_ROOT / "docs" / "mobile" / "RELEASE_RUNBOOK.md"
DEVICE_EVIDENCE_TEMPLATE = REPO_ROOT / "docs" / "mobile" / "DEVICE_VERIFICATION_EVIDENCE_TEMPLATE.md"
RELEASE_EVIDENCE_TEMPLATE = REPO_ROOT / "docs" / "mobile" / "RELEASE_EVIDENCE_PACKET_TEMPLATE.md"
APP_CONFIG = REPO_ROOT / "ancap-mobile" / "apps" / "acp-wallet-expo" / "app.json"
LEGAL_PRIVACY_PAGE = REPO_ROOT / "frontend-app" / "src" / "app" / "legal" / "privacy" / "page.tsx"
LEGAL_TERMS_PAGE = REPO_ROOT / "frontend-app" / "src" / "app" / "legal" / "terms" / "page.tsx"
LEGAL_COOKIES_PAGE = REPO_ROOT / "frontend-app" / "src" / "app" / "legal" / "cookies" / "page.tsx"
MOBILE_README = REPO_ROOT / "ancap-mobile" / "README.md"


def test_master_mobile_i18n_status_matches_mobile_roadmap() -> None:
    master = MASTER.read_text(encoding="utf-8")
    mobile = MOBILE_ROADMAP.read_text(encoding="utf-8")

    assert "| P4-15 | i18n EN/RU/UK/DE | [x]" in master
    assert "react-i18next wired in the Expo app with persisted language selection" in master
    assert "| P4-15 | i18n EN/RU/UK/DE | [x]" in mobile


def test_master_execution_order_no_longer_lists_mobile_i18n_as_open() -> None:
    master = MASTER.read_text(encoding="utf-8")

    assert "5.1  i18n EN/RU/UK/DE (i18next)" not in master


def test_master_week9_queue_uses_current_mobile_verification_wording() -> None:
    master = MASTER.read_text(encoding="utf-8")

    assert "Week 9 (Priority 5 -- Mobile)" in master
    assert "5.1  PIN + biometrics (real device verification)" in master
    assert "5.1  SecureVault (real device verification)" in master
    assert "5.1  MASVS/device-release verification (real hardware)" in master
    assert "Week 9 (Priority 5 -- Mobile)\n  5.1  PIN + biometrics (real device verification)\n  5.1  SecureVault (real device verification)\n  5.1  MASVS L1 checklist" not in master


def test_status_matrix_mobile_remaining_work_matches_mobile_roadmap_truth() -> None:
    status_matrix = STATUS_MATRIX.read_text(encoding="utf-8")

    assert "- remaining MASVS/device-release verification (repo baseline is closed; real-device/native validation still remains)" in status_matrix
    assert "- MASVS L1 checklist closure" not in status_matrix
    assert "- MASVS L1 and logging-secret hygiene" not in status_matrix


def test_master_and_mobile_roadmaps_mark_masvs_as_in_progress_with_repo_baseline_closed() -> None:
    master = MASTER.read_text(encoding="utf-8")
    mobile = MOBILE_ROADMAP.read_text(encoding="utf-8")

    expected = "| P5-1 | MASVS L1 checklist | [~] repo-baseline closed in `docs/mobile/SECURITY_MODEL.md`"
    assert expected in master
    assert "| P5-1 | OWASP MASVS L1 checklist | [~] | repo-baseline closed in `docs/mobile/SECURITY_MODEL.md`" in mobile


def test_mobile_release_closure_docs_exist_and_cover_current_truth() -> None:
    device_matrix = DEVICE_MATRIX.read_text(encoding="utf-8")
    release_checklist = RELEASE_CHECKLIST.read_text(encoding="utf-8")
    release_runbook = RELEASE_RUNBOOK.read_text(encoding="utf-8")
    device_evidence_template = DEVICE_EVIDENCE_TEMPLATE.read_text(encoding="utf-8")
    release_evidence_template = RELEASE_EVIDENCE_TEMPLATE.read_text(encoding="utf-8")

    assert DEVICE_MATRIX.exists()
    assert RELEASE_CHECKLIST.exists()
    assert RELEASE_RUNBOOK.exists()
    assert DEVICE_EVIDENCE_TEMPLATE.exists()
    assert RELEASE_EVIDENCE_TEMPLATE.exists()
    assert "Local Android test environment is available" in device_matrix
    assert "start-android-test-env.ps1" in device_matrix
    assert "build-android-native.ps1" in device_matrix or "`.so` artifacts" in device_matrix
    assert "macOS + Xcode" in device_matrix or "macOS/Xcode" in device_matrix
    assert "Device Verification Evidence Template" in device_evidence_template
    assert "This file is a **template**, not evidence." in device_evidence_template
    assert "Release Evidence Packet Template" in release_evidence_template
    assert "This file is a **template**, not a completed release packet." in release_evidence_template
    assert "TestFlight" in release_checklist
    assert "Play Console Internal testing" in release_checklist
    assert "/legal/terms" in release_checklist
    assert "/legal/privacy" in release_checklist
    assert "/legal/cookies" in release_checklist
    assert "v1.0.0 Release Runbook" in release_runbook
    assert "Release notes convention" in release_runbook
    assert "Rollback plan" in release_runbook


def test_release_closure_status_is_in_sync_across_master_mobile_and_status_matrix() -> None:
    master = MASTER.read_text(encoding="utf-8")
    mobile = MOBILE_ROADMAP.read_text(encoding="utf-8")
    status_matrix = STATUS_MATRIX.read_text(encoding="utf-8")

    assert "[~]" in next(row for row in master.splitlines() if row.startswith("| P6-3 |"))
    assert "[~]" in next(row for row in mobile.splitlines() if row.startswith("| P6-3 |"))
    assert "[~]" in (row := next(row for row in master.splitlines() if row.startswith("| P6-4 |"))) and "API 36+" in row
    assert "[~]" in (row := next(row for row in mobile.splitlines() if row.startswith("| P6-4 |"))) and "API 36+" in row
    assert "| P6-5 | Store listing + legal pages | [~] legal routes exist and release pack is outlined in `docs/mobile/RELEASE_CHECKLIST.md`; final operator/assets review still pending |" in master
    assert "| P6-5 | App Store / Play listing + legal pages | [~] | legal web routes exist and release pack is outlined in `docs/mobile/RELEASE_CHECKLIST.md`; final operator/assets review still pending |" in mobile
    assert "[~]" in (row := next(row for row in master.splitlines() if row.startswith("| P6-6 |"))) and "physical/MASVS" in row
    assert "[~]" in (row := next(row for row in mobile.splitlines() if row.startswith("| P6-6 |"))) and "physical/MASVS" in row
    assert "release-closure scaffolding now exists in `docs/mobile/DEVICE_MATRIX.md`, `docs/mobile/RELEASE_CHECKLIST.md`, and `docs/mobile/RELEASE_RUNBOOK.md`, and the remaining external evidence now has copy-ready templates in `docs/mobile/DEVICE_VERIFICATION_EVIDENCE_TEMPLATE.md` and `docs/mobile/RELEASE_EVIDENCE_PACKET_TEMPLATE.md`" in status_matrix
    assert "public legal page routes already exist for `/legal/terms`, `/legal/privacy`, and `/legal/cookies`" in status_matrix


def test_mobile_release_docs_match_current_expo_app_config() -> None:
    app_config = json.loads(APP_CONFIG.read_text(encoding="utf-8"))["expo"]
    release_checklist = RELEASE_CHECKLIST.read_text(encoding="utf-8")
    release_runbook = RELEASE_RUNBOOK.read_text(encoding="utf-8")
    release_evidence_template = RELEASE_EVIDENCE_TEMPLATE.read_text(encoding="utf-8")

    assert app_config["name"] == "ANCAP ACP Wallet"
    assert app_config["version"] == "1.0.0"
    assert app_config["scheme"] == "acpwallet"
    assert app_config["ios"]["bundleIdentifier"] == "cloud.ancap.acpwallet"
    assert app_config["android"]["package"] == "cloud.ancap.acpwallet"

    assert f"app version: `{app_config['version']}`" in release_checklist
    assert f"- iOS bundle ID: `{app_config['ios']['bundleIdentifier']}`" in release_checklist
    assert f"- Android package: `{app_config['android']['package']}`" in release_checklist
    assert f"- App name: `{app_config['name']}`" in release_evidence_template
    assert f"- iOS bundle ID: `{app_config['ios']['bundleIdentifier']}`" in release_evidence_template
    assert f"- Android package: `{app_config['android']['package']}`" in release_evidence_template
    assert f"- URL scheme: `{app_config['scheme']}`" in release_evidence_template
    assert f"- App name: `{app_config['name']}`" in release_runbook
    assert f"- Version: `{app_config['version']}`" in release_runbook
    assert f"- iOS bundle ID: `{app_config['ios']['bundleIdentifier']}`" in release_runbook
    assert f"- Android package: `{app_config['android']['package']}`" in release_runbook
    assert f"- URL scheme: `{app_config['scheme']}`" in release_runbook


def test_release_checklist_claimed_legal_routes_exist_in_frontend() -> None:
    assert LEGAL_PRIVACY_PAGE.exists()
    assert LEGAL_TERMS_PAGE.exists()
    assert LEGAL_COOKIES_PAGE.exists()


def test_mobile_readme_links_release_closure_docs() -> None:
    readme = MOBILE_README.read_text(encoding="utf-8")

    assert "../docs/mobile/DEVICE_MATRIX.md" in readme
    assert "../docs/mobile/DEVICE_VERIFICATION_EVIDENCE_TEMPLATE.md" in readme
    assert "../docs/mobile/RELEASE_CHECKLIST.md" in readme
    assert "../docs/mobile/RELEASE_EVIDENCE_PACKET_TEMPLATE.md" in readme
    assert "../docs/mobile/RELEASE_RUNBOOK.md" in readme


def test_mobile_readme_and_roadmap_use_current_expo_app_paths() -> None:
    readme = MOBILE_README.read_text(encoding="utf-8")
    mobile = MOBILE_ROADMAP.read_text(encoding="utf-8")

    assert "apps/acp-wallet-expo/" in readme
    assert "apps/acp-wallet/" not in readme
    assert "apps/acp-wallet-expo/.env" in readme
    assert "EXPO_PUBLIC_ANCAP_API_BASE" in readme
    assert "EXPO_PUBLIC_ANCAP_API_AUTH_HEADER" in readme
    assert "ANCAP_API_BASE_URL" not in readme
    assert "apps/acp-wallet-expo/" in mobile
    assert "apps/acp-wallet/" not in mobile


def test_android_native_build_truth_is_in_sync_across_docs() -> None:
    master = MASTER.read_text(encoding="utf-8")
    mobile = MOBILE_ROADMAP.read_text(encoding="utf-8")
    device_matrix = DEVICE_MATRIX.read_text(encoding="utf-8")
    release_checklist = RELEASE_CHECKLIST.read_text(encoding="utf-8")
    status_matrix = STATUS_MATRIX.read_text(encoding="utf-8")

    assert "| P1-6 | Android FFI `.so` build | [x] `ancap-mobile/scripts/build-android-native.ps1` now succeeds on the current Windows host" in master
    assert "| P1-6 | Link bindings in `expo-acp-core` Android | [x] | Kotlin + JNI wired; `ancap-mobile/scripts/build-android-native.ps1` now succeeds on the current Windows host" in mobile
    assert "[~]" in next(row for row in mobile.splitlines() if row.startswith("| P4-3 |"))
    assert "ENGINEERING_AUDIT_2026-10-17.md" in mobile
    signing_row = next(row for row in mobile.splitlines() if row.startswith("| P4-11 |"))
    assert "[~]" in signing_row and "operator test ACP" in signing_row
    assert "Local Android test environment is available" in device_matrix or "Pixel_10_Pro" in device_matrix
    assert "`libacp_mobile_ffi.so` artifacts" in device_matrix or "`.so` artifacts" in device_matrix
    assert "- [x] Android native `.so` artifacts built via `ancap-mobile/scripts/build-android-native.ps1` on the current Windows host" in release_checklist
    assert "- [x] Android native build path verified on a host with Android NDK" in release_checklist
    assert "Android native `.so` emission via `ancap-mobile/scripts/build-android-native.ps1` is now verified on the current Windows host" in status_matrix
    assert "- Android Expo dev-build/runtime verification using the emitted `.so` artifacts" in status_matrix


def test_smart_pay_groundwork_truth_is_in_sync_with_mobile_repo_state() -> None:
    master = MASTER.read_text(encoding="utf-8")
    mobile = MOBILE_ROADMAP.read_text(encoding="utf-8")
    status_matrix = STATUS_MATRIX.read_text(encoding="utf-8")

    assert "| SQ-3 | Quote engine groundwork | [x] | backend `POST /v1/mobile/smart-pay/quote` slice exists with first-scope direct-send and ACP→wACP→USDT route quoting, fee/slippage checks, and API tests |" in mobile
    assert "| SQ-4 | Execution session groundwork | [x] | backend execute/status/recover endpoints exist with first execution-state lifecycle and API tests |" in mobile
    assert "| SQ-5 | Mobile SDK/client wiring | [x] | `@ancap/acp-api-client` has typed Smart Pay capabilities/parse/quote/execute/status/recover methods with client tests |" in mobile
    assert "| SQ-6 | Expo scan/import/pay UX | [~] | Smart Pay beta supports paste, gallery QR import, camera QR scan, OCR text fallback when gallery QR missing, explicit confirmation before execute, quote-expiry guards, refresh/recover, and persisted draft/session restore; polished UX/history and on-chain route broadcast still pending |" in mobile
    route_row = next(row for row in mobile.splitlines() if row.startswith("| SQ-7 |"))
    assert "[~]" in route_row and "disabled" in route_row and "Funded" in route_row
    assert "| SQ-9 | Receipt/history/recovery UX | [~] | Expo beta now persists recent device-local Smart Pay session snapshots" in mobile
    assert "now also summarizes per-history-entry action state (`Refresh status + recover available`, `Refresh status only`, or `Snapshot only`)" in mobile
    assert "now deduplicates recovered/history proof tx refs case-insensitively across backend receipts and local execution snapshots while preserving the richer explorer-linked copy" in mobile
    assert "and now also summarizes proof linkage quality as explicit route-step matches vs inferred role/network matches vs pending steps in both history cards and the active receipt snapshot, and the compact history overview now aggregates linked-vs-additional proof provenance (receipt-backed vs execution-only) across the visible timeline, while the history list plus active execution/receipt views now also label whether route progress comes from live execution telemetry, proof-derived quote/receipt linkage fallback, raw tx refs, or status-only snapshots so stale execution counters are easier to spot during recovery and receipt review; final route-execution-linked proof polish still pending |" in mobile
    assert "backend `capabilities` + deterministic `parse` + `quote` + execute/status/recover endpoints exist in repo code with API tests" in master
    assert "typed mobile client methods exist with client tests" in master
    assert "Expo beta flow already supports paste, QR import, camera scan, review, execute, refresh/recover, and session restore" in master
    assert "Expo beta now persists recent device-local Smart Pay session snapshots, keeps per-execution `sessionToken` resume access when locally available, supports tap-to-resume, merges authenticated backend payment-history listing with local history, fetches backend receipt snapshots, and now makes the authenticated-vs-device-token resume boundary explicit in both docs and UI while rendering a richer receipt summary from receipt/intent/quote/execution data; the history list now also surfaces route-progress and recovery-state hints so resumed sessions expose more than status text alone, now also labels whether each restored snapshot still supports refresh, refresh-only finalized inspection, or snapshot-only restore, now also labels snapshot freshness from the freshest saved execution/receipt evidence in both restored history cards and receipt snapshots so stale local/backend restores are easier to distinguish from recent proof updates, local-history clearing now preserves signed-in backend history instead of wiping the whole visible timeline, and the receipt view now maps quoted route steps to linked-vs-pending proof coverage while keeping unmatched additional tx refs visible instead of collapsing everything into one flat list" in master
    assert "route-proof matching no longer reuses the same tx ref across multiple quoted steps with identical role/network pairs; each observed tx is now consumed at most once while extra unmatched refs stay in the additional-proof bucket" in master
    assert "restored history cards and receipt snapshots now both surface pending-proof summaries for quoted route steps that still lack linked tx refs" in master
    assert "structured recovery refs now flow through the backend recover API so pasted explorer links can preserve network/explorer metadata in reconciled proof receipts instead of collapsing back to bare hashes" in master
    assert "overlapping authenticated-backend/local-history snapshots now preserve richer locally observed proof refs plus receipt context/device session continuity instead of flattening to whichever final-state snapshot sorted last" in master
    assert "and both restored history cards plus the active receipt snapshot now summarize how many route-proof links are explicit route-step matches vs inferred role/network matches vs still pending so users can judge proof quality at a glance; the compact history overview now also aggregates linked-vs-additional proof provenance (receipt-backed vs execution-only) across the visible timeline so users can quickly see whether proof refs are already persisted into receipt snapshots or still only preserved in execution history, and now also aggregates the route-progress source mix (live telemetry vs proof-link fallback vs raw tx refs vs status-only snapshots) so users can quickly spot whether a session list is driven by fresh execution counters or mostly by recovery-only evidence; final route-execution-linked proof polish still remains" in master
    assert "placeholder execution lifecycle is now hardened in repo code: recover maps known txs onto bridge/swap/payment route steps, emits explorer links, and marks placeholder sessions completed once all quoted route txs are known" in master
    assert "execute responses now include actionable `routePlan` signing steps for client-side non-custodial orchestration" in master
    assert "on-chain bridge/swap/transfer broadcast orchestration still remains" in master
    assert "real non-custodial route execution remain **not shipped**" in master or "real non-custodial route execution remain" in master or "photo/OCR invoice decode and real non-custodial route execution remain" in master
    smart_qr_api_spec = (REPO_ROOT / "docs" / "mobile" / "SMART_QR_API_SPEC.md").read_text(encoding="utf-8")

    assert "Smart Pay first-scope backend groundwork exists for capabilities, deterministic parse, quote, and execute/status/recover" in status_matrix
    assert "Smart Pay placeholder execution lifecycle now maps recovered txs onto quoted route steps, emits explorer links, reports route-progress metadata, and can close placeholder sessions once all quoted txs are known" in status_matrix
    assert "Smart Pay typed client wiring and Expo beta flow already exist for parse → quote → execute → refresh/recover, now including quote-expiry freshness hints plus expired-quote review/execute guards in the Expo beta surface" in status_matrix
    assert "Smart Pay Expo beta now also keeps recent device-local session/receipt snapshots for resume/history/recovery baseline UX, preserves locally available per-execution `sessionToken` access for resume/recover flows, can merge authenticated backend payment-history listing with local history, can fetch backend receipt snapshots for the active payment, now makes the authenticated-vs-device-token resume boundary explicit in UI/docs, surfaces route-progress/recovery-state hints directly inside the session history list, now also labels whether each restored snapshot still supports refresh, refresh-only finalized inspection, or snapshot-only restore, maps quoted route steps to linked-vs-pending proof coverage in the receipt view while keeping unmatched additional tx refs visible separately, avoids reusing one observed tx ref across multiple quoted steps with the same role/network pair, now surfaces pending-proof summaries for quoted route steps that still lack linked tx refs in both restored history cards and receipt snapshots, now keeps quoted-route proof coverage explicit even for receipt snapshots that still have 0 linked tx refs, now labels snapshot freshness from the freshest saved execution/receipt evidence in both restored history cards and receipt snapshots so stale local/backend restores are easier to distinguish from recent proof updates, now normalizes pasted recovery input from raw tx hashes or explorer links before recover requests, now rejects unparseable structured recovery-locator noise instead of forwarding fake tx ids while surfacing duplicate/invalid recovery tokens directly in the Expo UI, now blocks recover submission when the pasted field contains only invalid locator noise while still allowing an empty status-only recovery pass, now previews each parsed recovery ref in the Expo UI with preserved network/explorer-link context before submit, now deduplicates recovered/history proof tx refs case-insensitively across backend receipts and local execution snapshots while preserving the richer explorer-linked copy, now forwards structured recovery refs (including network/explorer metadata from pasted explorer links) through the backend recover API so restored proof coverage keeps richer explorer-linked route context instead of degrading to bare tx hashes, now allows the authenticated execution owner to refresh status/receipt and submit recovery without the original device-local session token while still blocking non-owners, now keeps explicit conflicting `routeStepIndex` refs in the additional-proof bucket instead of silently remapping them onto a different quoted step or inflating observed progress counts, and now preserves richer local proof refs plus receipt context/session continuity when authenticated backend history later overlaps the same execution instead of flattening to the later final-state snapshot only, while the active receipt snapshot now also renders from that merged history context so route summaries, fees, merchant labels, and completion metadata stay aligned with the richer overlap state instead of falling back to a thinner in-memory receipt copy, both restored history cards plus the active receipt snapshot now summarize proof-linkage quality as explicit route-step matches vs inferred role/network matches vs pending steps, the compact history overview now aggregates linked-vs-additional proof provenance (receipt-backed vs execution-only) across the visible timeline, and the history cards plus active execution/receipt views now also label whether route progress comes from live execution telemetry, proof-derived quote/receipt linkage fallback, raw tx refs, or status-only snapshots" in status_matrix
    assert "fetch per-execution status / receipt unless the caller presents either the per-execution `sessionToken` or the authenticated execution-owner session" in smart_qr_api_spec
    assert "authenticated execution owners may reopen the same execution without the original device-local token" in smart_qr_api_spec
    assert '"clientKnownRefs": [' in smart_qr_api_spec
    assert '"routeStepIndex": 1' in smart_qr_api_spec
    assert "backend reconciliation should prefer the richer structured ref instead of collapsing back to a bare hash" in smart_qr_api_spec
    assert "conflicting refs should stay visible as additional proof rather than being silently remapped" in smart_qr_api_spec
