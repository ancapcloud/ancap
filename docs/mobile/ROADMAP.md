# ANCAP ACP Wallet — Roadmap

> Status: supporting mobile roadmap | Updated: 2026-10-14
> Last verified: 2026-10-14
> Source of truth for cross-project execution priority: `MASTER_ROADMAP.md`
> Current reality: Android emulator create→save address match verified (`Pixel_10_Pro` + UniFFI `.so`). Keystore must be chunked in SecureStore (Android 2048-byte limit). Stable restore path is **keystore JSON**, not mnemonic alone (Dilithium RNG). Local sign UI added (no broadcast); funded sign still needs operator test ACP. iOS packaging + physical PIN/biometrics still open.
> Fast status index: `docs/STATUS_MATRIX.md`

Official **non-custodial** mobile wallet for ACP (native) and wACP (BSC).
One codebase: **React Native + TypeScript** → iOS + Android builds.

**Status legend:** `[ ]` todo · `[~]` in progress · `[x]` done

---

## Phase 0 — Program setup

| ID | Task | Status | Owner |
|----|------|--------|-------|
| P0-1 | `docs/mobile/ROADMAP.md` (this file) | [x] | — |
| P0-2 | `docs/mobile/ACP_WALLET_PRD.md` | [x] | — |
| P0-3 | `docs/mobile/WALLET_SPEC.md` | [x] | — |
| P0-4 | `docs/mobile/API_MOBILE.md` | [x] | — |
| P0-5 | `docs/mobile/SECURITY_MODEL.md` | [x] | — |
| P0-6 | `docs/mobile/BRIDGE_MOBILE_SPEC.md` | [x] | — |
| P0-7 | `ancap-mobile/` monorepo skeleton | [x] | — |
| P0-8 | Backend `GET /api/v1/mobile/config` + public ACP read API | [x] | — |

---

## Phase 1 — ACP crypto core (Rust FFI)

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P1-1 | Crate `acp-mobile-ffi` wrapping `acp-crypto` | [x] | `ACP-crypto/acp-mobile-ffi/` |
| P1-2 | `create_wallet` / `import` / `validate_address` | [x] | keystore_json required for stable address |
| P1-3 | `acp_sign_transfer` (local sign, no broadcast) | [x] | uses keystore_json |
| P1-4 | walletd `sign-transfer` + `submit` | [x] | CLI for dev / bridge testing |
| P1-5 | Kotlin/Swift bindgen (`scripts/uniffi-generate.ps1`) | [x] | `acp-mobile-ffi/bindings/` |
| P1-6 | Link bindings in `expo-acp-core` Android | [x] | Kotlin + JNI wired; `ancap-mobile/scripts/build-android-native.ps1` now succeeds on the current Windows host, auto-detects SDK/NDK, and emits `arm64-v8a`, `armeabi-v7a`, and `x86_64` `libacp_mobile_ffi.so` artifacts into `modules/expo-acp-core/android/src/main/jniLibs` |
| P1-7 | iOS Swift UniFFI link | [~] | Expo iOS podspec now stages generated Swift/modulemap artifacts and can vend `acp_mobile_ffiFFI.xcframework`; `ancap-mobile/scripts/build-ios-native.ps1` added for macOS packaging, but runtime build verification still needs a macOS/iOS run |
| P1-7 | Golden-vector tests | [x] | `wallet_smoke.rs` |

---

## Phase 2 — TypeScript SDK

| ID | Task | Status | Package |
|----|------|--------|---------|
| P2-1 | `@ancap/acp-wallet-sdk` types + interface | [x] | `ancap-mobile/packages/acp-wallet-sdk` |
| P2-2 | `parseUnits` / `formatUnits` (8 decimals) | [x] | pure TS |
| P2-3 | Native bridge stub → FFI | [~] | `createWallet`, `signTransfer`, `estimateFeeDefault`, `addressFromKeystore` wired; Android emulator create/save verified 2026-10-14; funded local-sign + physical-device still pending |
| P2-4 | `@ancap/acp-api-client` | [x] | config, network status, balance/history/detail, device registration/listing, broadcast + fee flows; build clean, 12 tests passing |
| P2-5 | `@ancap/acp-bridge-client` | [x] | status, reserve proof, redeem quote, and authenticated intent create/list helpers; build clean, 9 tests passing |
| P2-6 | `@ancap/acp-bsc-client` | [x] | read-only wACP balance helpers; build clean, 13 tests passing |

---

## Phase 3 — Backend (mobile gateway)

| ID | Task | Status | Endpoint |
|----|------|--------|----------|
| P3-1 | Mobile config | [x] | `GET /v1/mobile/config` |
| P3-2 | Public balance | [x] | `GET /v1/acp/address/{address}/balance` |
| P3-3 | Public tx history | [x] | `GET /v1/acp/address/{address}/transactions` |
| P3-4 | Public tx detail | [x] | `GET /v1/acp/transactions/{txid}` |
| P3-5 | Fee estimate | [x] | `POST /v1/acp/tx/estimate-fee` |
| P3-6 | Broadcast signed tx | [x] | `POST /v1/acp/tx/broadcast` |
| P3-7 | Network status | [x] | `GET /v1/acp/network/status` |
| P3-8 | ACP indexer (DB-backed history) | [x] | `mobile_acp_indexer_tick` + `MobileAcpTx` model |
| P3-9 | Push device registration | [x] | `POST /v1/mobile/devices/register` + `unregister` + `GET` |
| P3-10 | Rate limits on broadcast | [x] | 10 req/min per IP |

---

## Phase 4 — React Native app

| ID | Task | Status | Screen |
|----|------|--------|--------|
| P4-1 | Expo app (`apps/acp-wallet-expo`) | [x] | expo-router |
| P4-2 | Navigation (onboarding + home) | [x] | |
| P4-3 | Welcome / Create / Import | [~] | Android emulator: create + save address match verified 2026-10-14 (`acp1…` roundtrip on home). Create Copy → document export file + clipboard; Import paste / Load export file with `v:3` validation. Keystore-first restore; mnemonic-only non-stable. iOS still depends on P1-7 |
| P4-4 | Tabs: Wallet / Exchange / Activity / Send / Bridge / Settings | [x] | Exchange tab = ACP-hub multi-asset desk foundation |
| P4-5 | Receive + QR | [x] | |
| P4-6 | Send UI + broadcast API | [x] | sign needs native module |
| P4-7 | Backup + confirm seed | [x] | Explicit clipboard + optional document export file on Copy only (no SecureStore stash); wipe deletes export file; mnemonic optional; paste / load-export-file import |
| P4-8 | PIN + biometrics | [~] | PIN lock + biometric unlock preference wired in Expo app; still needs real device verification |
| P4-9 | SecureVault (Keychain / Keystore) | [~] | Chunked SecureStore (1800B) + generation commit-after-verify; wipeVault clears active/incomplete/legacy/stash **and** document-dir `acp-keystore-export.json`; Copy reports clipboard-only when file write unavailable; regenerate deletes stale export; unit tests vault/chunk/export. Physical biometric sign-off still pending |
| P4-10 | Dashboard (ACP + wACP) | [x] | wACP via BSC RPC (fetchWacpBalanceWei); ACP via ACP API |
| P4-11 | Send + preview + sign | [~] | Send UI has **Sign locally (no broadcast)**; native `signTransfer` linked on Android. Emulator restore smoke green 2026-10-17; funded local-sign/broadcast still need operator test ACP (UTXOs:0 on smoke wallet); iOS still depends on P1-7 |
| P4-12 | Transaction history | [x] | |
| P4-13 | Bridge flows | [~] | status tab now uses real bridge client for live status, reserve proof, redeem quote, and market links; authenticated intents still v1.1 |
| P4-14 | Settings + legal links | [x] | Terms, privacy, bridge docs, reserve proof, support |
| P4-15 | i18n EN/RU/UK/DE | [x] | `react-i18next` wired in Expo app with persisted language selection and translated core wallet flows/screens |
| P4-XO | Exchange office (ACP hub all↔all) | [x] | `docs/mobile/EXCHANGE_OFFICE_FOUNDATION.md` — catalog/quote/tickets + Exchange tab; open ticket UX + auto settlement next |

---

## Phase 5 — Security hardening

| ID | Task | Status |
|----|------|--------|
| P5-1 | OWASP MASVS L1 checklist | [~] | repo-baseline closed in `docs/mobile/SECURITY_MODEL.md` (hashed PIN verifier, secure-store device-only persistence, biometric-gated vault migration, error redaction, screenshot/clipboard/auto-lock controls); remaining closure is real-device/native release verification |
| P5-2 | Screenshot block on seed screens | [x] | expo-screen-capture, active on seed visibility screen |
| P5-3 | Clipboard auto-clear | [x] | 30s auto-clear after copy |
| P5-4 | Root/jailbreak warning | [x] | dev-build warning on settings screen |
| P5-5 | No secrets in Sentry/logs | [x] | wallet error surfaces now route thrown messages through a shared secret-redacting helper; mnemonic/keystore/rawTx/bearer-token shaped values are scrubbed before UI/log propagation |
| P5-6 | App auto-lock timer | [x] | 5-min inactivity auto-lock |

---

## Phase 5.5 — Biohax NFC + org identity

| ID | Task | Status |
|----|------|--------|
| P5.5-1 | Backend models + migration `057_org_nfc_identity` | [~] | `OrganizationMember` verification fields, `UserNfcCredential`, `OrganizationNfcPolicy` |
| P5.5-2 | Org identity API (`/organizations/{org_id}/identity/...`) | [~] | NFC register/list/revoke, member verify/status, policy GET/PUT |
| P5.5-3 | Mobile dep `react-native-nfc-manager` + Expo NFC permissions | [~] | package + `app.config.js` Android/iOS NFC strings |
| P5.5-4 | i18n NFC unlock/settings strings (EN/RU/UK/DE) | [~] | `lib/i18n.ts` |
| P5.5-5 | NFC unlock UI + local hash enrollment | [x] | `unlock.tsx`, `settings.tsx`, `lib/nfc.ts` |
| P5.5-5b | Digital passport BSC soulbound + API | [x] | `contracts/digital-passport/`, `066_digital_passport`, `/v1/passports/*` — `docs/DIGITAL_PASSPORT.md` |
| P5.5-5c | Mobile Passport tab + NFC backend register | [x] | `app/(tabs)/passport.tsx`, `lib/identity.ts`, `EXPO_PUBLIC_ORG_ID` |
| P5.5-6 | Org admin verification UI (web or mobile) | [ ] | consume identity API |
| P5.5-7 | Policy enforcement (`require_nfc_for_admins/payments`) | [~] | `require_nfc_for_admins` on admin identity + org API key delete; payments gate next |
| P5.5-8 | DESFire / challenge–response implants | [ ] | post-MVP secure element path |

Spec: `docs/mobile/BIOHAX_NFC.md`

---

## Phase 5.6 — Apple Watch employee HR fleet

> Spec: `docs/mobile/APPLE_WATCH_EMPLOYEE_FLEET.md` · Master priority **R10**

Each employee receives **3 Apple Watches** with distinct bands. One is active on shift; the other two charge. The phone/org stack syncs **heart rate** and enforces a **swap schedule** tied to battery/charging.

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P5.6-1 | Domain + migration (watch assets, assignments, rotation policy, HR samples, consent) | [ ] | org-gated inventory; exactly one `active` watch per member |
| P5.6-2 | Fleet + rotation + vitals ingest APIs | [ ] | register 3 devices, rotate A/B/C, batch HR upload, gap/missed-swap alerts |
| P5.6-3 | Consent + org policy (who can view HR, retention TTL) | [ ] | explicit opt-in; revoke stops ingest |
| P5.6-4 | iPhone HealthKit sync in Expo/org module | [ ] | read HR after permission; background flush; rotation coach UI |
| P5.6-5 | Default charge rotation UX (3 bands, countdown, charger checklist) | [ ] | default swap every 4–6h or SOC floor (e.g. 25%) |
| P5.6-6 | watchOS companion (native) | [ ] | sampling + haptic “swap due”; complication by band slot |
| P5.6-7 | Org safety dashboard (web) | [ ] | on-shift HR tiles, gaps, rotation compliance % |
| P5.6-8 | Fleet ops (lost/maintenance, battery analytics) | [ ] | post-MVP hardening |

**Depends on:** org membership/roles; pairs well with Phase 5.5 NFC step-up.  
**Does not block:** wallet FFI / MASVS device closure — ship behind `apple_watch_vitals` flag.

---

## Phase 6 — QA & release

| ID | Task | Status |
|----|------|--------|
| P6-1 | Unit tests (SDK decimals, API client) | [x] | `vitest` across the mobile packages; latest consolidated snapshot: 56 tests across 5 packages |
| P6-2 | API integration tests | [x] | `tests/api/test_mobile_acp.py` |
| P6-3 | Device matrix (iOS + Android) | [~] | Android emulator create→export→restore smoke `SMOKE_OK` 2026-10-17 (`docs/mobile/device-evidence-2026-10-17.md`); physical PIN/biometrics + iOS matrix rows still open |
| P6-4 | TestFlight + Play Internal | [~] | local device/test-env blocker **cleared**; Play/TestFlight uploads remain operator credentials/listing follow-up (`docs/mobile/RELEASE_CHECKLIST.md`) |
| P6-5 | App Store / Play listing + legal pages | [~] | legal web routes exist and release pack is outlined in `docs/mobile/RELEASE_CHECKLIST.md`; final operator/assets review still pending |
| P6-6 | Production v1.0.0 | [~] | Android emulator runtime path unblocked; production cut still needs store evidence + physical/MASVS sign-off (`docs/mobile/RELEASE_RUNBOOK.md`) |

---

## Smart QR Pay / AI Payment Scanner / Claim Codes track (v1.1 / v2)

> Status: execution started, but not shipped. Source plan/specs: `SMART_QR_AUTO_SWAP_PLAN.md`, `SMART_QR_PAYMENT_INTENT_SCHEMA.md`, `SMART_QR_API_SPEC.md`, `SMART_QR_SECURITY.md`

| ID | Task | Status | Notes |
|----|------|--------|-------|
| SQ-1 | Capability discovery | [x] | `GET /v1/mobile/smart-pay/capabilities` |
| SQ-2 | Deterministic parse | [x] | `POST /v1/mobile/smart-pay/parse` for ACP, raw EVM, EIP-681 first scope |
| SQ-3 | Quote engine groundwork | [x] | backend `POST /v1/mobile/smart-pay/quote` slice exists with first-scope direct-send and ACP→wACP→USDT route quoting, fee/slippage checks, and API tests |
| SQ-4 | Execution session groundwork | [x] | backend execute/status/recover endpoints exist with first execution-state lifecycle and API tests |
| SQ-5 | Mobile SDK/client wiring | [x] | `@ancap/acp-api-client` has typed Smart Pay capabilities/parse/quote/execute/status/recover methods with client tests |
| SQ-6 | Expo scan/import/pay UX | [~] | Smart Pay beta supports paste, gallery QR import, camera QR scan, OCR text fallback when gallery QR missing, explicit confirmation before execute, quote-expiry guards, refresh/recover, and persisted draft/session restore; polished UX/history and on-chain route broadcast still pending |
| SQ-7 | Real route execution integration | [~] | recover maps txs onto route steps with explorer links; execute returns `routePlan`; Expo now runs ACP legs via `executeRoutePlanLocally` + API broadcast after execute; bridge/swap legs still skipped pending chain clients |
| SQ-8 | AI fallback classifier | [ ] | only after deterministic path is stable |
| SQ-9 | Receipt/history/recovery UX | [~] | Expo beta now persists recent device-local Smart Pay session snapshots, keeps per-execution `sessionToken` resume access when locally available, supports tap-to-resume, merges authenticated backend payment-history listing with local history, fetches backend receipt snapshots, explicitly explains the authenticated-vs-device-token resume boundary in UI/docs, renders a richer receipt summary from receipt/intent/quote/execution data, now surfaces route-progress/history-state hints inside the session history list, now also summarizes per-history-entry action state (`Refresh status + recover available`, `Refresh status only`, or `Snapshot only`) so signed-in/backend-restored snapshots are less ambiguous, maps quoted route steps to linked-vs-pending proof coverage in the receipt view, keeps unmatched additional tx refs visible instead of collapsing everything into one flat tx list, avoids reusing one observed tx ref across multiple quoted steps with the same role/network pair, makes local-history clearing preserve signed-in backend history instead of wiping the whole visible timeline, now also surfaces pending-proof summaries for quoted route steps that still lack linked tx refs in restored history cards and receipt snapshots, now keeps quoted-route proof coverage explicit even for receipt snapshots that still have 0 linked tx refs, now labels snapshot freshness from the freshest saved execution/receipt evidence in both restored history cards and receipt snapshots so stale local/backend restores are easier to distinguish from recent proof updates, now normalizes pasted recovery input from raw tx hashes or explorer links before recover requests, now rejects unparseable structured recovery-locator noise instead of forwarding it as fake tx ids while surfacing duplicate/invalid recovery tokens directly in the Expo UI, now blocks recover submission when the pasted field contains only invalid locator noise while still allowing an empty status-only recovery pass, now previews each parsed recovery ref in the Expo UI with preserved network/explorer-link context before submit, now deduplicates recovered/history proof tx refs case-insensitively across backend receipts and local execution snapshots while preserving the richer explorer-linked copy, now forwards structured recovery refs (network/explorer metadata from pasted explorer links) through the backend recover API so proof receipts can keep richer route-linked explorer coverage instead of collapsing every recovered tx back to a bare hash, now allows the authenticated execution owner to refresh status/receipt and submit recovery without the original device-local session token while still blocking non-owners, now keeps explicit conflicting `routeStepIndex` refs in the additional-proof bucket instead of silently remapping them onto a different quoted step or inflating route progress, and now preserves richer local proof refs plus receipt context/session continuity when authenticated backend history later overlaps the same execution instead of flattening to the last final snapshot only, while the active receipt snapshot now also renders from that merged history context so route summaries, fees, merchant labels, and completion metadata stay aligned with the richer overlap state instead of falling back to a thinner in-memory receipt copy, and now also summarizes proof linkage quality as explicit route-step matches vs inferred role/network matches vs pending steps in both history cards and the active receipt snapshot, and the compact history overview now aggregates linked-vs-additional proof provenance (receipt-backed vs execution-only) across the visible timeline, while the history list plus active execution/receipt views now also label whether route progress comes from live execution telemetry, proof-derived quote/receipt linkage fallback, raw tx refs, or status-only snapshots so stale execution counters are easier to spot during recovery and receipt review; final route-execution-linked proof polish still pending |
| SQ-10 | AI Payment Scanner MVP | [ ] | camera/photo upload, QR recognition, OCR for invoices/receipts/payment screens, and payment-intent preview with manual correction |
| SQ-11 | Smart Payment Flow expansion | [ ] | auto asset matching, smart swap before payment, multi-chain routing, duplicate payment detection, merchant mode |
| SQ-12 | ANCAP Claim Codes / Crypto Voucher MVP | [ ] | lock balance, generate redeemable claim code, redeem from wallet/site, expiry/cancel/refund, ACP fees |
| SQ-13 | Secure escrow + claim verification layer | [ ] | hash-based code storage, status lifecycle, rate limits, anti-fraud, optional PIN/password |
| SQ-14 | Merchant / growth distribution layer | [ ] | gift codes, promo claim codes, airdrop claim links, QR vouchers for Telegram/X/web |

Scanner target formula:
- `Photo / QR -> AI Decode -> Payment Intent -> Smart Swap -> Pay`

Claim-code target formula:
- `Lock crypto -> Generate claim code -> Share code -> Redeem -> Receive crypto`

Claim-code storage model target:
- `claim_code` = public code shown to user
- `secret_hash` = only stored hash of redeem secret
- `locked_balance` = reserved amount
- `status` = `active | redeemed | expired | cancelled | locked`

Scope truth:
- this is a **post-v1.0** flagship track, not release-closure work
- first supported scope stays narrow: **ACP + BSC/EVM** only
- deterministic parser first, AI second
- AI/OCR may prepare a payment, but must never auto-send without explicit user confirmation
- final user confirmation remains mandatory
- claim-code storage must be hash-based and abuse-resistant, not plain-text voucher storage

## Post-MVP (v1.1+)

- Address book, multi-wallet, dark mode
- Push notifications (FCM)
- WalletConnect
- Full reverse bridge in-app (when rail is public-live)
- Merchant QR, staking, governance

---

## Timeline note

The original 8–12 week estimate is no longer the right way to read this document. The project is now in the late-stage completion zone, where the remaining duration depends mostly on host/tooling blockers and release verification:

- Android physical-device PIN/biometrics/MASVS sign-off (emulator create/save + UniFFI link verified 2026-10-14; funded local-sign still needs test ACP)
- Android 16 KB page-size ELF alignment warning on API 36 emulator (compat mode; follow-up for store builds)
- macOS/Xcode packaging for iOS native artifacts
- real device verification of create/send/lock/unlock/biometric flows
- MASVS/security checklist closure
- TestFlight / Play Internal / store listing work

Treat this roadmap as a task tracker, not as a reliable remaining-weeks estimate.

Release-closure execution docs now live in `docs/mobile/DEVICE_MATRIX.md`, `docs/mobile/RELEASE_CHECKLIST.md`, and `docs/mobile/RELEASE_RUNBOOK.md`, with copy-ready evidence artifacts in `docs/mobile/DEVICE_VERIFICATION_EVIDENCE_TEMPLATE.md` and `docs/mobile/RELEASE_EVIDENCE_PACKET_TEMPLATE.md`, so the remaining P6 work is explicit instead of hand-wavy.

---

## Repository map

```
ANCAP/                          # this repo
  docs/mobile/                  # specs + roadmap
  app/api/routers/mobile_acp.py # mobile gateway API
  ACP-crypto/                   # Rust chain + wallet (source of truth)

ancap-mobile/                   # mobile monorepo (sibling or submodule)
  apps/acp-wallet-expo/         # Expo app
  packages/acp-wallet-sdk/
  packages/acp-api-client/
  packages/acp-bridge-client/
  packages/acp-bsc-client/
```

---

## Phase D — ANCAP Dating Mesh (proximity + bitchat-inspired)

| ID | Task | Status | Notes |
|----|------|--------|-------|
| D-1 | Spec `docs/mobile/ANCAP_DATING_MESH.md` | [x] | BLE UUID + 18+ + access points |
| D-2 | Cloud API `/v1/dating/*` + migration `085` | [x] | profiles, APs, matches, messages |
| D-3 | Web `/dating` + `/legal/dating` | [x] | catalog + legal + news card |
| D-4 | Expo Dating tab (BLE advertise/scan as ANCAP Dating) | [x] | age gate + mesh UI |
| D-5 | Offline multi-hop relay MVP | [x] | hop limit 5 + sim/BLE adapter |

---

## Critical difference: web vs mobile

| | Web `/wallet/acp` | Mobile ACP Wallet |
|--|-------------------|-------------------|
| Keys | Server (encrypted) | **Device only** |
| Signing | `walletd` on backend | **Local FFI** |
| API | `/v1/wallet/acp/*` (auth) | `/v1/mobile/*`, `/v1/acp/*` (public read + broadcast) |

---

## Current next gates

1. Run an Android Expo dev build against the emitted `.so` artifacts and verify create/send/sign on emulator + physical device
2. Run `ancap-mobile/scripts/build-ios-native.ps1` on macOS/Xcode
3. Verify create/send/sign, PIN, biometrics, and SecureVault flows on real devices
4. Verify the remaining MASVS/device-release gates on real hardware (PIN/biometric/vault migration + native signing path)
5. Run TestFlight + Play Internal validation
6. Prepare listing/legal/release artifacts and cut v1.0.0
7. In parallel for post-v1.0 Smart Pay: unblock local non-custodial EVM spend/sign + real route execution integration, then harden receipt/history/recovery UX

_Update this file when closing tasks (change `[ ]` → `[x]`)._
