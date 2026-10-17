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
