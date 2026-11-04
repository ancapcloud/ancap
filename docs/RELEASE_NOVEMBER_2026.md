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
  098_merge_release_heads, without the test schema fallback. (Historical: the
  head has since advanced to `104_merge_packet_listing`; a base→104 rehearsal
  has not been re-run — see the 4 November update below.)
- [x] Frontend TypeScript check passed. Invoice Decimal JSON serialization fixed.
- [ ] Unfinished provenance/quality-fixture work reconciled or explicitly excluded.
- [ ] Full backend, frontend build and security CI green on the release commit.
- [ ] Real remote-client connection and all nine function results verified live.
- [ ] Provider-backed execution, funded payment, receipt and reconciliation accepted.
- [ ] Exact build deployed; migrations, rollback and production readiness verified.

## Evidence update — 4 November 2026

Release under test: `a9395368d74cea2218b0e7265d373062c07bfef4` (deployed build
`a939536`). Full inventory and re-verification commands:
`docs/ROP01_ACCEPTANCE_2026-11-04.md`.

- **Migration head**: single head `104_merge_packet_listing`. Deploy 41645358135
  log shows the production upgrade `102_cost_evidence_attribution ->
  103_packet_templates_rop05`, then `103_packet_templates_rop05 +
  103_robinhood_listing -> 104_merge_packet_listing` on 2026-11-03T13:49:22Z.
  Production is past 098; a full base→104 empty-database rehearsal has not been
  re-run and is still required before freeze.
- **CI on the release commit**: Backend CI 41645358246 (1384 passed, 47 skipped;
  unit job 277/7; documentation block 60/5), Docs CI 41645358235, CodeQL
  41645358248, Secret Hygiene 41645358179 — all success.
- **Frontend CI did not run on a9395368**: `frontend-ci.yml` is path-filtered and
  the release commit changed documentation only. The last green Frontend CI is
  41639480462 on `c8bd9142`. The "frontend build on the release commit" part of
  the gate above is therefore still unproven for `a9395368`.
- **Deployment/readiness**: `/api/v1/system/health` → ok;
  `/api/v1/system/ready` → ready with `database` and `redis` true;
  `/internal/frontend-build` → `a939536`. Rollback was not exercised.
- **Security**: no open CodeQL, Dependabot or secret-scanning alerts at
  verification time (2026-11-04).

These facts do not close funded payments, live remote-client acceptance or
commercial acceptance.

## Migration repair

Two heads (097_source_quotas and rop04_add_cost_evidence_fields) blocked
`alembic upgrade head` and caused DB tests to skip. Migration 098 merges them;
the ROP-04 boolean server defaults now use SQL expressions. The full migration
chain was applied successfully on a fresh disposable PostgreSQL 16 database.
This does not assert that the existing production database has been migrated.
