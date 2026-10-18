# Wallet and side-track engineering audit — 2026-10-17

Follow-up continued on 2026-10-18; the dated baseline/evidence paths are retained.

## Scope and baseline

Reviewed local commits b9a3fb2, a096757, 23267af and dfbdcb7 on master, initially
unpublished. Existing consensus/node, bridge, SACP, listing, frontend component,
social/investor work was already dirty and is outside this changeset. Android
Gradle repository/memory adjustments were also pre-existing; they are reviewed
as mobile build prerequisites, with the JDK path delimiter corrected here.
No production deployment, public mint, oracle switch, LP operation or funded
transaction is part of this audit.

## Findings and corrections

- Vault: cleanup after an active-pointer switch could throw into rollback and
  delete the now-active generation. Commit outcome is separated from cleanup;
  a rejected pointer promise is checked by reading its actual value before
  deleting anything. An unknown pointer outcome preserves tracked allocations.
- Reads, saves, mnemonic updates, protection changes and wipe are serialized.
  Wipe retains failed allocations, settles outstanding deletions and reports
  incomplete removal. A subsequent retry can finish it. Allocation metadata is
  written before chunks so a process death does not hide orphan chunks.
- Chunking now bounds UTF-8 bytes without splitting Unicode code points. Chunk
  and pending-generation metadata have strict bounded parsing. Existing vault
  presence does not disappear because a biometric read failed. Secret reads
  and replacement of an existing wallet require an unlocked PIN session;
  ordinary saves preserve existing biometric protection.
- KeystoreV3 is plaintext private-key material, despite its name. New exports
  use the existing Argon2id + XChaCha20-Poly1305 KeystoreJson envelope (outer v2,
  authenticated inner v3), not a newly invented crypto format. Native roundtrip,
  wrong password, tampering and unsupported KDF parameters are tested. No backup
  password is persisted alongside the vault. Old native clients fail closed.
- Create and Settings offer encrypted file export; import supports password
  decryption and the system file picker. Android uses a user-selected SAF
  folder. iOS sharing returns an explicit unverified-save outcome. Only encrypted
  envelopes can be written to the app-owned export helper. Existing plaintext
  imports remain available for migration. App-owned copies and picker/share
  cache have explicit cleanup; user-owned external files are not wiped.
- Smart Pay execute no longer automatically submits server-returned routes.
  The helper accepts only one ready native ACP step and defaults to sign-only.
  Explicit submission requires pre-submission persistence of signed bytes/txid;
  an ambiguous response retains that txid and requires reconciliation. Unsupported
  prerequisites, duplicate/multiple legs and handled steps cannot trigger signing.
  SDK signing also verifies that the keystore belongs to the confirmed sender.
- Watcher: candidate matches require exact case-sensitive Tron deposit addresses,
  order-address/amount validation and no conflicting claim. Fetching paginates
  confirmed USDT with fixed query filters and a bounded time/response budget.
  Incomplete fetches leave the cursor unchanged; a 24-hour overlap covers bounded
  index lag. Audit lookup no longer depends on the latest 300 events. All modes
  that mutate orders are rejected until durable attribution/claim controls exist.
  Jobs isolate watcher DB failures with a savepoint. The flag remains default off.
- Fee recycle: zero 30-day revenue is authoritative; historical total cannot
  replace it. Missing/non-finite/negative inputs and non-positive thresholds fail
  closed. CLI and service share parsing. CLI reports oracle state as unverified
  instead of asserting that a remote oracle is disabled.
- Sign smoke now distinguishes success, funding block and unobserved/failed
  result. Reset scripts require explicit disposable-wallet consent and verify
  Pixel_10_Pro. Host/device temporary copies are cleaned in finally. The old
  generation script delegates to the encrypted recovery scenario.
- Native tooling fails after Cargo/generation failures. Regeneration applies
  the UniFFI 0.28 Kotlin message-field workaround deterministically; wire format
  is unchanged. Gradle JDK discovery uses comma-separated paths.
- The old emulator sign smoke also hid a real HTTPS transport failure. Native
  reqwest now uses bundled WebPKI roots rather than desktop native-certificate
  discovery on Android. Certificate and hostname verification remain enabled.
- Once TLS worked, signing exposed a second bug: `getnetworkinfo` is not a
  public node method. The signer reads chain ID from the public best-block
  header (`getbestblockhash` + `getblock`) and validates its u32 range. No
  operator token is embedded in the app and node auth policy is unchanged.
  Public read-only host probes confirmed these methods and chain ID 1001.
- UniFFI unit errors had empty messages, hiding the domain failure behind an
  empty Expo rejection. Android/iOS mappings now provide explicit messages and
  stable existing codes for invalid input and insufficient funds. Android
  avoids chaining an empty unit error as the deepest rejection; iOS compilation
  remains an external macOS gate.
- The block scan exceeded the public nginx 5 requests/second burst budget and
  tried to decode an HTML HTTP 503 as JSON. Reads are now paced, 429/503 retries
  are bounded (four attempts, bounded Retry-After), and HTTP status is checked
  before decoding. The synthetic-sign fixture injects an HTML/text 503 first.
- Release builds now reject the template debug signing key through
  `:app:verifyReleaseSigning`; the negative guard test passed. Operator/EAS may
  provide the final signing configuration without committing credentials.
- Backend test fixes use Decimal for the exact ACP:wACP ratio and isolate
  deployment fixtures from the developer's real .env, host nginx/sudo and live
  ACP RPC. Bash tests explicitly verify fake docker/git resolution under WSL.
  Binary LF stdin preserves the final Bash option on Windows. The auction
  integration test obtains its personalized minimum as the actual bidder.

## Verification log

Completed so far:

- Targeted backend/mobile-roadmap regression: 58 passed; pip check passed.
- Final system/mobile-roadmap follow-up: 23 passed; separate OpenAPI uniqueness
  regression: 1 passed. Duplicate-operation warnings are resolved.
- After aligning the final store/backup status rows, roadmap regression: 13 passed.
- Deployment-script suite: 65 passed, including Windows PowerShell and WSL Bash
  runtime cases. These use fake services and do not deploy anything.
- API coverage in split runs: 397 tests passed before the personalized-auction
  assertion failed; after correcting its user context, all 75 tests from
  test_tech_auction.py through the final API module passed (472 API tests covered).
  This is not represented as a single uninterrupted green full-suite run.
- Remaining backend suite (excluding API and deployment module): 476 passed,
  5 skipped in an isolated database. The earlier scan-race failure passed when
  rerun with stable HEAD. OpenAPI duplicate operation IDs exposed by this run
  were corrected by splitting the deposit-address GET/POST route definitions.
- An earlier non-API run stopped at the secret-evidence generator because HEAD
  changed between its two scans during a local commit. The mismatch correctly
  failed closed. The rerun holds HEAD stable; interrupted/failed earlier broad
  runs are not counted as acceptance.
- Backend unit/mobile documentation slice: 106 passed after status correction.
- Targeted vault/backup/route tests: 57 passed after pointer-acknowledgement and
  biometric-preservation regressions were added.
- Mobile SDK build and workspace typecheck passed; consolidated mobile tests:
  346 passed (Expo 216, API client 32, bridge client 18, BSC client 26, wallet SDK 54).
- Native wallet smoke: 3 passed on Windows (identity, mnemonic limitation,
  encrypted password/tamper roundtrip). Positive local-sign fixture: 1 passed.
  The fixture serves synthetic UTXOs only on loopback, independently verifies
  the resulting hybrid signature, sender/view address, recipient, amount, fee,
  chain ID, txid and network-tamper rejection, and rejects any broadcast RPC.
  It uses no real ACP and does not close funded emulator/chain acceptance.
- Android Rust libraries rebuilt with --locked for arm64-v8a, x86_64 and armeabi-v7a.
- Encrypted recovery on Pixel_10_Pro passed: create -> encrypted Copy (55,303
  bytes) -> host pull -> explicit disposable-wallet `pm clear` -> restore file
  -> password decrypt -> save -> restart. Address before and after:
  `acp1qp2j34cyc530jn8rr5qjsc7whg7p34qjyqde4tyn`.
  `SMOKE_OK=True`; no mnemonic was used. This tests app-file restoration via
  host transport, not Android SAF/system-picker interaction. An earlier run
  interrupted by emulator SystemUI/launcher ANR is not counted as passed.
- Installed debug package: `cloud.ancap.acpwallet`, versionName 1.0.0,
  versionCode 1, minSdk 24, targetSdk 34; emulator Android 17 / API 37.
  Final debug APK SHA-256 (TLS + public-header RPC + pacing/error mapping):
  `04d62e07f801c72690811c0619083a6db85ed1ab46b4fd1048d489cd7a32e4c2`.
  `:app:assembleDebug` passed and `adb install -r` succeeded.
- Debug APK ELF inspection covered 72 bundled .so entries; 55 have a minimum
  PT_LOAD p_align of 4096. This includes 12 arm64 libraries (React Native,
  Hermes, fbjni, barhopper and image libraries). ACP's arm64/x86_64 .so passed
  this alignment check, but the complete app does not. Unexpected legacy ABI
  entries are also bundled by dependencies; review release ABI filters.
  This is ELF evidence only, not ZIP/AAB alignment or 16 KB runtime acceptance.
- Payment Scanner Chromium safety suite: 4 passed on a local dev server, including
  spoofed-raster/onload and HTML-label cases. GitHub #481/SARIF source/sink trace
  was read; the alert remains open. See ../security/CODEQL_TRIAGE_2026-10-17.md.

Final emulator sign-only smoke after RPC pacing/error mapping reached the actual
native funding check: `SIGN_LOCAL_BLOCKED=funding_required`, same restored
address. No signed funded transaction or broadcast occurred. TLS, public chain
identity reads and the block scan passed this runtime path. Failed intermediate
attempts (TLS, auth, empty error, throttling) are superseded by this evidence,
not counted as signing success. Backend verification is complete in split runs.

## Gates that remain open

- Android stack migration and acceptance for target API 36+ is an engineering
  gate: the audited debug APK targets API 34. New phone apps/updates submitted
  to Play require API 36 from 2026-08-31 ([official policy](https://support.google.com/googleplay/android-developer/answer/11926878?hl=en)).
  Also verify full-artifact 16 KB page-size support, including all Expo/RN
  libraries ([Android guidance](https://developer.android.com/guide/practices/page-sizes)).
  Do not infer support from an NDK build or emulator compatibility mode.
- Funded local signature verification and broadcast require operator test ACP.
- System-picker/SAF cancel/save/install-survival scenarios require native device
  evidence; app-owned Copy/pull smoke alone does not close them.
- Physical PIN/biometrics/MASVS, lifecycle behavior, per-chunk authentication UX,
  release variant and Play-installed artifact remain separate checks.
- iOS native rebuild, physical Keychain tests and TestFlight require macOS and
  Apple distribution access; Swift bindings being generated is not compilation.
- SQ-7 still needs reviewed intent/quote/fee/network binding, durable UI recovery,
  reconcile-before-retry and funded route acceptance before automatic submission.
- Watcher live claims/crediting still need per-transfer event identity, unique DB
  claims and concurrency tests, shared-address ownership attribution, network
  confirmation/reorg reconciliation, replay/backfill acceptance and shadow soak.
  It must not be described as exactly-once automation.
- npm initially reported 40 advisories during compatible Expo dependency
  installation; a subsequent standalone audit reported 60 (6 moderate, 54 high),
  with 8 distinct underlying advisories (including two each for browserslist and
  image-size). Treat these as time-specific scanner snapshots, not fixed totals. No forced Expo/RN major upgrade was performed.
- Bandit was not installed in the local .venv; that SAST check is not claimed as
  passed. Production health/deployed SHA and GitHub rescan were not performed.

## Local correction commits

- 564a482 — shadow-only watcher, matching, pagination and DB savepoint.
- bccd311 — fee-recycle numeric validation and authoritative revenue window.
- ae29d81 — scanner/Helio regressions and CodeQL evidence.
- 971a3e7 — recoverable vault writes and encrypted backups across native/UI.
- f04cd2b — supported-route checks and recoverable Smart Pay submission contract.
- 5a4fa1b — reproducible bindings/builds, signing guard and honest smoke scripts.
- 662146c — isolated deployment probes and exact token-ratio assertions.
- 67ced35 — unique OpenAPI operation IDs and bidder-context regression.
- bfb91f6 — TLS roots, public RPC reads, throttling recovery and native errors.

No push or deployment was performed. Original unrelated node/consensus, bridge,
SACP, listing, frontend component, social and investor WIP remains uncommitted.
The disposable audit PostgreSQL container was identity-checked and removed;
the user's database was not used for these test runs.

## Next execution order

The engineering corrections are split from watcher, fee recycle and security.
Next prepare a separate Android compatibility change: inventory the current
Expo 52/RN 0.76/toolchain and all native dependencies, select a supported API
36+ stack, migrate incrementally, regenerate/review native bindings, and repeat
unit/typecheck/recovery/sign plus release AAB and 16 KB acceptance. Do not
replace that work with a targetSdk number-only bump. In parallel obtain
operator test ACP and physical-device evidence; iOS native acceptance remains
on macOS. Then complete the internal-store handoff with real upload/install IDs.
Keep conversion event/cohort preparation read-only while store gates remain
open. Paid-run retry UX and deposit automation follow the existing release gates;
Smart Pay automatic broadcast follows durable recovery and binding acceptance.
