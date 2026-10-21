# Dependency and CodeQL follow-up — 2026-10-21

Recount of open GitHub alerts on `ancapcloud/ancap` at published `ab32ea0`.
A closed Dependabot pull request is not a fix. CI on that SHA is green and is
not zero alerts. No alert was dismissed from this pass.

Implementation follow-up: after verified deployment of `22cb00a`, the Stripe
request origin is restricted in production, redirects/path escapes are blocked,
and local mock access needs an explicit non-production flag. The nested launcher
AJV lock entry now uses the already pinned 8.20.0 artifact and integrity from the
root lock entry; install/typecheck/tests verify that existing override. These
changes are separate from an Expo native-stack migration. The alert inventory
below is the original snapshot; rescan determines GitHub closure.

GitHub automatically marked #9 (AJV), #290 (Stripe partial SSRF) and #487
(assert side effects) fixed after the security commits. No alert was dismissed.
New alerts indexed during this pass: #299 certifi, #296–#298 Vite. certifi is
patched to 2026.10.19 and Vite stays on patched 6.x; see
[the certifi advisory](https://github.com/advisories/GHSA-6q48-6c7w-9gw2).
The downloaded universal wheel's SHA-256 and removal of the compromised CA were
checked before tests; the unchanged rest of the Linux dependency lock is retained.

## Dependabot

| Alert | Package | Where it runs | Exploit path | Patch | Closure test |
| --- | --- | --- | --- | --- | --- |
| #277 high | `braces` 3.0.3 | `ancap-mobile/package-lock.json`, and frontend dev tooling | Deeply nested brace patterns can exhaust the stack while expanding a glob. Callers are Metro, Expo CLI and frontend build globs, not the payment API. An attacker needs a glob pattern those tools expand. | none (`<= 3.0.3`) | Upstream `braces` above 3.0.3 is in both lockfiles, `npm ci` succeeds, and mobile typecheck plus the workspace tests pass. |
| #275 high | `node-forge` 1.4.0 | `@expo/cli` and `selfsigned` in the mobile lockfile | PKCS#1 v1.5 verification can accept an extra nested DigestAlgorithm. ACP signing and keystore verification go through the Rust wallet, not this package. The exposed verifier is dev-certificate tooling. | none (`<= 1.4.0`) | Expo CLI resolves `node-forge` above 1.4.0, then the mobile install, typecheck and tests pass. |
| #250, #247 high | `image-size` 1.2.1 | Metro 0.81.5 (`image-size` `^1.0.2`) | A crafted ICNS, JXL or HEIF image can loop the parser while Metro reads an asset. This is the bundler, not the production OCR route. | 2.0.3 | Do not force 2.0.3 onto Metro 0.81. Its CommonJS call shape is not the one this Metro uses. Closure is an Expo/Metro release that depends on `image-size` `>= 2.0.3` and still completes `expo export:embed` for the wallet. |
| #9 medium | `ajv` 8.11.0 | nested under `expo-dev-launcher` 5.0.35, which depends on exact `ajv@8.11.0` | ReDoS when the `$data` option is enabled. The root override already asks for `ajv@8.20.0`, including `expo-dev-launcher.ajv`, but `npm ci` still installs 8.11.0 from the lockfile. The launcher is a dev client, not the payment parser. | 8.18.0 within 8.x | Regenerate the lock so the override replaces that nested copy, then `npm ci`, typecheck and the 346 mobile tests pass. Until that lock diff is reviewed, the alert stays open. |
| #49 medium | `pytest` 8.3.4 | `pyproject.toml` dev extra | `CVE-2025-71176` is tmpdir handling inside the test runner. The API image does not ship pytest. | 9.0.3, and every 8.x release is still in range | Move the dev pin to `pytest>=9.0.3` only after `pytest-asyncio` 0.24 and the targeted backend suite pass on Python 3.11. That is a major test-runner migration, not a production patch. |

Frontend `ajv` 6.15.0 is outside advisory #9 (`>= 7.0.0-alpha.0, < 8.18.0`).

## Incompatible upgrades already rejected

These pulls were closed. Closing them did not patch the advisory.

| Pull | Why it is not a fix | Migration | Closure test |
| --- | --- | --- | --- |
| #96 Expo 52 to 58 | Incomplete native migration | The Play-capable line is Expo SDK 54 (React Native 0.81, React 19.1, compileSdk/targetSdk 36), not an unfinished jump to 58. Steps are in `docs/mobile/ANDROID_STACK_MIGRATION_2026-10-21.md`. | Wallet create/restore, encrypted export/import, release AAB, 16 KB ELF check, then a Play Internal install. |
| #98 SHA-256 / HKDF | New digest traits do not match the current `sha2`/`hkdf` callers | Bump `sha2`, `hkdf` and `digest` in one ACP-crypto change. Keep the KeystoreJson Argon2id + XChaCha20-Poly1305 envelope. Regenerate nothing unless the FFI surface changes. | Classical crypto tests, a fixed BIP39 vector, and the native keystore wrong-password/tamper roundtrip. |
| #101 UniFFI / Rust 1.88 | The toolchain bump is not coordinated with bindings | Stay on UniFFI 0.28 until the Rust bump, bindgen and the Kotlin message-field workaround land together. Review the generated Kotlin and Swift diff. | Android native tests on the regenerated bindings. iOS compile stays a macOS job. |

## CodeQL errors still open

| Alert | Component | Exploit path | Closure |
| --- | --- | --- | --- |
| #483–#486 `py/log-injection` | `app/services/helio_commerce.py` webhook log | The four fields already pass through `_safe_log_token`, which drops non-printable characters and caps length. CodeQL does not treat that function as a sanitizer, so the alerts stay open after the `ab32ea0` scan. A webhook sender cannot break the log line unless a future edit logs the raw payload. | Rescan after the sanitizer is visible to CodeQL, or keep the alerts open. Do not dismiss them from the GitHub UI. |
| #290 `py/partial-ssrf` | `app/services/stripe_payments.py` | `stripe_api_base` comes from server settings, then a path is appended. A caller of the HTTP API does not choose the host. An operator who can edit that setting can point the server at another URL and attach the Stripe secret. | Allow only `https://api.stripe.com` in production, with an explicit test override, and rescan. |
| #487 `py/side-effect-in-assert` | `tests/unit/test_swap_tron_deposit_watcher.py` | Test-only. An assertion with a side effect can hide a failure when Python is run with `-O`. It does not ship in the API. | Move the side effect out of the assertion the next time that test is edited. |
| #338, #310, #309, #298 clear-text secret storage or logging | operator scripts and `examples/payment-integration` | These paths can write or print a key or token if an operator runs the script. They are not request handlers. | Remove the secret from the log or file before anyone runs that script against a funded wallet. |
| #314, #315 uninitialized local | `scripts/generate_ancap_docs_live_followup.py` | A docs generator can throw or emit an empty value. It is not a payment path. | Initialize the locals when that generator is next run. |
| #481 `js/xss-through-dom` | payment scanner preview | Prior SARIF trace is an image sink. The committed page re-encodes a decoded raster to PNG. Still open until GitHub rescans the deployed tree. | Rescan `ab32ea0` or later. Do not mark the alert fixed from a local browser run. |

Style notes (`unused-import`, `unnecessary-lambda`, `empty-except`, unpinned action tags) stay open until the touched file is edited. They are not described as fixed.
