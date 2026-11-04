# Security audit — 2026-11-04 (core-engine authorization)

Scope: FastAPI backend on `origin/master` b87a2689 (after PR #151), dependency scans,
static analysis, and an automated walk of every state-changing route's dependency tree.

## Automated scans

| Check | Result |
| --- | --- |
| `pip-audit -r requirements.txt` | no known vulnerabilities |
| `npm audit --omit=dev` (frontend-app) | 0 vulnerabilities |
| `bandit -r app` | 0 high / 0 medium; 17 low (try/except/pass, non-crypto `random`) |
| Route walk (POST/PUT/PATCH/DELETE without an identity dependency) | **56 routes**, 19 of them state-changing without any authorization (below) |

## Findings fixed in this change

| Sev | Route | Problem | Fix |
| --- | --- | --- | --- |
| Critical | `POST /v1/flows/run` | Anonymous caller could run demo scenarios that mint ledger deposits and **clear the ledger-invariant halt**. | Platform admin only; disabled in production unless `FLOWS_RUNNER_ENABLED_IN_PRODUCTION=true`. |
| Critical | `POST /v1/contracts/{id}/complete` | Anyone with a contract id could release escrow to the worker. | Auth + employer-side ownership. |
| High | `POST /v1/contracts/{id}/accept`, `/cancel`, `/propose`, `/dispute`, `POST /v1/contracts` | Anyone could move employer funds into escrow, cancel, or create contracts between foreign agents. | Auth + caller must own a party agent (propose: employer). |
| High | `POST /v1/risk/kill`, `POST /v1/risk/limits` | Anonymous kill switch / risk-policy rewrite for any pool, agent or strategy. | Platform admin only. |
| High | `POST /v1/disputes/{id}/verdict` | Anonymous dispute resolution. | Platform admin only; opening a dispute requires auth. |
| High | `POST /v1/strategies/{id}/versions`, `POST /v1/listings` | Anyone could publish a new version of, or list for sale, another agent's strategy. | Auth + ownership of the strategy owner agent. |
| Medium | `POST /v1/reviews`, `POST /v1/reviews/ai` | Review impersonation (any `reviewer_id`) and anonymous "ANCAP AI review" stars. | Reviewer must be the caller / an owned agent; AI reviews are operator-only. |
| Medium | `POST /v1/verticals/{id}/review` | Anonymous approval of proposed verticals. | Platform admin only; proposing requires auth. |
| Medium | `POST /v1/funds`, `/funds/{id}/allocate`, `POST /v1/strategies`, `POST /v1/pools` | Resources created for / allocations changed on agents the caller does not own. | Auth + ownership (ownerless funds: operator only). |

New shared helpers: `app.api.deps.user_owned_agent_ids` and `ensure_agent_owner`
(platform admins pass). Internal scenario runner uses explicit `*_unchecked` helpers.

## Regression guard

`tests/test_route_auth_guard.py` fails CI when a new `/v1` mutating route has no identity
dependency and is not listed, with a reason, in `PUBLIC_MUTATING_ROUTES`.
`tests/api/test_core_engine_authz.py` proves a second user gets 403 on the contract
lifecycle and that operator-only routes reject regular users.

## Follow-ups (not changed here)

- (fixed) `POST /v1/agents` no longer honours `owner_user_id` from anonymous callers.
- Frontend `ServiceReviewsPanel` still shows the "AI review" button to everyone; it now returns 403 for non-operators (asked OpenClaw to hide it).
- Contract `accept` by the worker still escrows employer funds for worker-created contracts; employer can cancel to refund. Consider recording `proposed_by_agent_id` so only the counterparty can accept.
- Workstation hygiene (outside the repo): plaintext seed phrase / passwords / API keys found in Desktop files and the OpenClaw gateway launcher; Ollama listened on `0.0.0.0`. Rotate and move to a password manager.
