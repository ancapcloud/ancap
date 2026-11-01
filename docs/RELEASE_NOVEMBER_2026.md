# November 2026 release candidate

Target: final scoped web/API/MCP release by 30 November 2026 (Europe/Berlin).
This is a target and acceptance plan, not a production-ready declaration.

## Scope and evidence — 1 November

- All nine existing MCP functions: token preview, risk report creation, payment
  links, invoices, payment status, claim creation/redemption, Smart Pay parsing,
  workflow run creation. Creating a workflow record is not funded execution.
- Function schemas for commerce, scanner and workflow requests now come from
  their API Pydantic models. Invoice line items and scanner raw_text are exposed.
  Historical raw scanner calls remain accepted.
- Streamable HTTP version negotiation, malformed argument handling, notification
  handling, batch shape, browser Origin checks and payment-code path validation.
- Legacy SSE sends responses as message events, keeps streams alive and cleans
  up bounded queues. Single worker/sticky routing required; prefer stateless HTTP.
- Stdio is a dependency-free adapter to hosted MCP, sharing its tool catalogue.
- Preview requires an account key even when no paid result is unlocked. Legacy
  agent/org keys do not gain account privileges. Prefer header credentials.
- Combined MCP/account-key/merchant/claim/scanner/nginx run: 61 passed,
  no skips; includes real account keys and PostgreSQL. Protocol-only coverage
  also runs without PostgreSQL.
- Read-only production probe: build 23451f3; health ok; MCP discovery HTTP 200
  with the previous protocol version. Candidate fixes are not deployed.

## Existing unfinished work

The pre-existing uncommitted payment-provenance router prevented application
startup. Its registration was removed, preserving its files. It references a
missing get_db_session, has no enforced admin dependency and no matching
migration; its service calls nonexistent ORM class methods. Do not expose it
until DB/service/schema/auth/migration and tests are completed. The existing
require_admin helper permitted authenticated users when no UUID allowlist was
configured. It now delegates to require_platform_admin and fails closed.

No change here erases historical balances, promotes wACP, or changes the current
EUR service pricing/rACP external-token policy.

## Release acceptance schedule

1. 1–7 November: close MCP route/function regressions and account-key tests;
   reconcile unfinished local work; verify migrations on isolated PostgreSQL.
2. 8–14 November: green backend/frontend/security CI; stage migration and rollback;
   connect real remote and stdio clients; test key revocation and isolation.
3. 15–21 November: approved funded workflow/payment run, receipt and reconciliation;
   verify configured LLM provider and explicitly labelled degraded fallback.
   Close customer-source/research delivery acceptance within the published scope.
4. 22–30 November: freeze features, rerun release checks, deploy the exact tested
   commit, check live build/readiness and nine-function acceptance, record evidence.

Unfunded local tests do not close funded-payment/LLM acceptance. Physical mobile,
iOS native/store signing, OCR payment-grade quality and partner-dependent offers
remain separate releases unless their existing acceptance gates are satisfied.
Do not claim the entire historical expansion roadmap complete for this release.

## Remaining release gates

- [x] All nine functions passed against real account keys and PostgreSQL.
  Account-key/merchant/claim/scanner regressions passed (25 tests).
- [x] Empty PostgreSQL database upgraded from base through all migrations to
  098_merge_release_heads, without the test schema fallback.
- [x] Frontend TypeScript check passed. Invoice Decimal JSON serialization fixed.
- [ ] Unfinished provenance/quality-fixture work reconciled or explicitly excluded.
- [ ] Full backend, frontend build and security CI green on the release commit.
- [ ] Real remote-client connection and all nine function results verified live.
- [ ] Provider-backed execution, funded payment, receipt and reconciliation accepted.
- [ ] Exact build deployed; migrations, rollback and production readiness verified.

## Migration repair

Two heads (097_source_quotas and rop04_add_cost_evidence_fields) blocked
`alembic upgrade head` and caused DB tests to skip. Migration 098 merges them;
the ROP-04 boolean server defaults now use SQL expressions. The full migration
chain was applied successfully on a fresh disposable PostgreSQL 16 database.
This does not assert that the existing production database has been migrated.
