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
