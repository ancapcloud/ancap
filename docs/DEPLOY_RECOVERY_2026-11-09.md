# Deployment recovery — 9 November 2026

Release `7f0e085` (PR #156) passed CI, image builds, migrations and container
health checks. Actions run `42599215114` initially failed immediately after host
nginx reload: compose RPC returned HTTP 200, while both host probes returned 404.
Later probes of the same unchanged routes returned valid JSON-RPC through the
origin and Cloudflare. The failed-job retry completed successfully (attempt 2).

Public health/readiness return 200 with database and Redis ready; frontend build
provenance reports `7f0e085`. This timing is consistent with asynchronous nginx
worker convergence, rather than a failed application build or migration.

The host RPC smoke now uses a bounded retry loop and a domain URL with `--resolve`
to preserve TLS SNI. It requires valid getblockcount replies from both compose
and the HTTPS origin; an HTTP-only success cannot mask a broken TLS route.
HTML, JSON-RPC errors, boolean results and unavailable upstreams remain failures.
Per-run temporary files replace shared fixed paths. `--smoke-only` performs a
rootless diagnostic without patching or reloading nginx.

Validation: six isolated shell scenarios cover delayed readiness and persistent
failures, plus eleven release-gate regressions (17 tests passed). The updated
smoke is also checked against the live origin without modifying nginx config.
