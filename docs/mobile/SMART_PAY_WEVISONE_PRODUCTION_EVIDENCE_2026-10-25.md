# Smart Pay production verification — 2026-10-25

Application release: `80159c799052d814a8911b79e1e52db0bff0ba45`.
PR #119 supplies the integration; PR #121 bounds wallet Rust compilation to two jobs and serializes API/frontend builds.
Deployment run: https://github.com/ancapcloud/ancap/actions/runs/40229062179 (success).

## Measured checks

- Public `/api/v1/system/health`: HTTP 200, status ok.
- Public `/api/v1/system/ready`: HTTP 200, database and Redis ready.
- Public `/internal/frontend-build`: `80159c7`.
- Guest POST `/api/v1/payment-scanner/parse`: HTTP 401.
- Real production Python service invoked `parse_payment_image`, followed by the router preview conversion, on a synthetic English invoice. Provider `wevisone` used verified private HTTPS, a restricted reverse SSH channel and the local Docker GPU worker. Correct checksum-valid address, 12.50 ACP, `can_pay_acp=true`, `requires_manual_confirm=true` were asserted. API numeric representation 12.5 equals 12.50.
- No payment or funded transaction was submitted. Authenticated public browser upload was not tested: the user requested server verification without account login.
- Public browser displayed the localized login requirement and all five language selectors (EN/RU/UK/DE/繁中). Local authenticated upload evidence remains in the local GPU evidence document.

## Operational limits and recovery

The first deployment exhausted the 4 GB VPS while two builds ran concurrently. The operator rebooted the VPS. The aborted deployment was cancelled; the retry succeeded after limiting Rust parallelism, serializing builds and adding 2 GB swap. Existing services recovered and were checked before the retry.

The model runs on the Windows PC, not the VPS. The PC, Docker worker and SSH tunnel must stay running. Windows scheduled autostart was not installed: automatic approval rejected that command with `blocked by policy`. The foreground `scripts/maintain-wevisone-tunnel.ps1` loop reconnects while it remains running; after PC restart the operator must launch it again. After VPS/firewall restart, rerun `scripts/install-wevisone-private-relay.sh` to restore the narrowly scoped firewall rule.

The five-language interface is preserved. Exact OCR passed EN/RU/UK/DE synthetic fixtures locally; the 繁中 fixture misread the address and was blocked by checksum validation. This is not a claim of reliable five-language payment recognition. Always review source, amount and recipient; payment confirmation remains manual.
