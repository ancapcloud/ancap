# Street QR campaign

Status: implementation proposed; not deployed. Baseline d7a4ec26d77e875848b9bcef5dae367ce4a624c1.

- Printed URL: https://ancap.cloud/q/street
- Next.js redirects without caching to https://api.ancap.cloud/v1/qr/street.
- Backend atomically increments a persistent daily PostgreSQL counter and redirects to the homepage with fixed QR/sticker/street UTM parameters.
- Admin statistics: existing ops console Analytics page, `/ops-x7k9m2/analytics`; API `GET /v1/qr/street/stats?days=30`, platform-admin access required.
- Total is lifetime aggregate; today and daily buckets use Europe/Berlin. Displayed history is 30 days, API supports 1–90. No visitor identifiers, cookies, IPs or user agents are stored by this counter. Ordinary infrastructure logs are independent.
- These are qualifying GET requests, not unique people or guaranteed camera scans. Repeat opens count; manually shared links count. Known bot/prefetch headers and HEAD requests do not count; undetected automation can still count.
- Counter writes use an atomic upsert. A failed write does not block redirects, but that request may be absent from statistics. A database connection outage can still affect the endpoint.

## Release gate

Written merge/deploy approval required. Run `alembic upgrade head` (migration 090) before starting the new backend. Deploy backend and frontend. Verify anonymous stats are denied, admin stats load, and a real GET through the printed URL increments today/total exactly once and lands on the homepage. HEAD must not increment. Verify a physical proof scans before printing the full run. Do not distribute the revised QR before this gate passes.

## Validation

- Four isolated backend tests passed against SQLite: repeat/persistent aggregates, anonymous stats denial, HEAD/prefetch/bot exclusion, write-failure redirect, and 20 concurrent increments (the first test covers several checks). Run with `.venv/bin/python -m pytest --noconftest tests/test_qr_campaigns_unit.py -q`; optional `aiosqlite` is required.
- Two frontend redirect tests passed; TypeScript check passed.
- Alembic reports a single head: `090_qr_daily_counts`. PostgreSQL migration/integration checks require a test database; ordinary test setup was blocked because localhost:5432 is unavailable.
- Updated QR PNG at 1500/600/300 px and rendered PDF decode to the tracking URL.
