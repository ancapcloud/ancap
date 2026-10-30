> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# CodeQL triage — 2026-10-17

Triage of open GitHub code-scanning alerts by data flow (not zeroing for optics).
`WACP_ORACLE_USE_V3` remains **false**; sACP public mint stays blocked pending legal S4.

## Fixed this wave

| Alert | Rule | Disposition |
|-------|------|-------------|
| #462–#465 | `py/log-injection` in `app/services/helio_commerce.py` | **Fixed** — webhook fields pass through `_safe_log_token` before logging |

## Open — actionable later

| Alert | Rule | Path | Disposition |
|-------|------|------|-------------|
| #481 | `js/xss-through-dom` | `frontend-app/src/app/payment-scanner/page.tsx` | Review DOM write path on next frontend hardening pass; no `dangerouslySetInnerHTML` today — verify text-node sinks |
| Helio / commerce depth | — | — | Re-scan after deploy of log sanitize |

## Open — non-runtime / style (do not dismiss as “fixed”)

| Rule cluster | Examples | Disposition |
|--------------|----------|-------------|
| `py/unnecessary-lambda` | unit tests | Style; keep until natural refactor |
| `py/unused-import` / `unused-local-variable` | dating, explorer | Cleanup when touching those modules |
| `py/ineffectual-statement` | `app/main.py` | Note — verify on next main.py edit |
| `py/incomplete-url-substring-sanitization` | `tests/api/test_weather.py` | Test fixture only |

## Explicit non-goals this wave

- Do not flip `WACP_ORACLE_USE_V3`
- Do not enable public sACP mint
- Do not auto-dismiss alerts without data-flow review

## Follow-up local source review

The current payment-scanner page uses React text interpolation for parsed label,
address and notes; the explorer path encodes the address with encodeURIComponent.
The image preview is a local object URL after raster MIME/size validation; the
URL is revoked on replacement/unmount. No innerHTML, outerHTML, srcDoc or
scriptable HTML sink was found in this local file. This is a source-level
observation, not a dismissal of alert #481: retrieve its actual SARIF source/sink
trace and rescan the committed tree before changing GitHub disposition.
Helio control-character/length regression test is added; GitHub closure and
post-deploy verification are still external evidence, not implied by unit tests.

Retrieved GitHub alert #481 and SARIF analysis `1968504235` for commit
`cd7b3387a8a94f7078a554e77d3321abc574b6f9` during this audit. The exact trace is
`event.target.files` (line 94) → `URL.createObjectURL(file)` (108) →
`photoPreviewUrl` → `<img src={photoPreviewUrl}>` (214). This is an image-resource
sink, not an HTML document or innerHTML assignment. Chromium regression tests
now exercise a spoofed PNG containing SVG/onload code plus script/HTML labels
and notes; all four scanner safety scenarios pass locally against the dev
server. This supports a non-exploitable-image-context assessment for this trace
on the tested browser; it is not universal browser proof or a GitHub dismissal.
Alert #481 remains open; no alert state was changed.

## GitHub/deployment follow-up — 2026-10-18

The image-preview path is now hardened beyond that original assessment:
supported raster MIME and magic bytes must agree, browser decode must succeed,
and dimensions are bounded to 16 megapixels. A canvas encodes the decoded pixels
as PNG; the image sink never receives a raw-upload object URL. Spoofed SVG/PNG
is rejected before preview/upload. Five Chromium scanner regressions passed,
including valid PNG preview and escaped malicious labels. Lint and TypeScript
passed. GitHub rescan, rather than dismissal, determines closure of #481.

Dependabot follow-up removes three stale member Cargo.lock files: Cargo metadata
confirms all four crates use ACP-crypto/Cargo.lock. The authoritative workspace
lock is unchanged. Dependabot is configured at that workspace root. browserslist
is pinned to patched 4.28.7 with its compatible data dependencies; mobile
typecheck and all 346 tests passed after installation.

Other findings are not described as fixed: image-size's available patch changes
the callable CommonJS API used by current Metro; decode-uri-component's patch is
ESM while its current consumer requires CommonJS. The old Expo launcher still
resolves its own ajv 8.11 despite existing npm overrides. These need a validated
Expo/Metro dependency migration. Current braces/node-forge alerts have no patched
version listed by GitHub. No forced major upgrade or bulk alert dismissal was
performed. Advisory counts remain time-specific; CI success is not zero alerts.

## Recount — 2026-10-21

Open Dependabot alerts on this date were #277 braces, #275 node-forge,
#250 and #247 image-size, #9 ajv, and #49 pytest. No compatible lockfile bump
was applied: braces and node-forge have no patched release, image-size 2.0.3 is
the Metro-incompatible bump, ajv 8.20.0 is already overridden but the lockfile
still installs 8.11.0 under expo-dev-launcher, and pytest 9.0.3 is a major
test-runner move. Component, exploit path and closure test for each alert, plus
the rejected Expo, SHA/HKDF and UniFFI pulls, are in
`docs/security/DEPENDENCY_MIGRATION_2026-10-21.md`. Alerts were not dismissed.
