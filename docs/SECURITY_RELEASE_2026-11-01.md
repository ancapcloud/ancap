# Security and usability release — 1 November 2026

## Reviewed scope

Reviewed the Theodore changes after published c777417 through the local
cost-evidence commit d4d16ca, the MCP candidate, current dependency/security
alerts and the existing deployment path. This is a bounded code/dependency
review, not a claim that every possible vulnerability has been eliminated.

## Repairs

- Admin quality-fixture handlers now await async services, validate UUIDs,
  paginate with a true total, use the canonical /v1/quality-fixtures path,
  enforce the platform operator allowlist and return private/no-store responses.
  The loader no longer imports nonexistent modules, prints database credentials,
  creates schemas ad hoc or duplicates fixture rows on rerun.
- Removed the duplicate cost-evidence GET handler in favour of one shared typed
  service and a protected compatibility alias. Provider/event metadata can be
  recorded and retrieved; it remains explicitly operator-attested.
- MCP request rate, byte and batch limits; validated payment-code path; fixed
  internal URL authority; shared HTTP schemas; working remote/SSE/stdio dispatch.
  Both remote and stdio passed interoperability checks with the official SDK.
- Invoice quantities must be positive and finite, line currencies must match,
  amounts/totals fit Numeric(36,18), and Decimal line items serialize as JSON.
- Scheduled UTXO RPC work runs in a worker thread instead of blocking the API
  event loop. The existing index state locks remain in use.
- DOCX uses defusedxml with DTDs/entities forbidden, including UTF-16 payloads.
- TRON provider requests require HTTPS and refuse redirects with API credentials.
  rACP operator scripts use exclusive initial journals, descriptor-based regular
  file reads/writes, durable writes and protected voucher-key creation. No
  contract bytecode, issuance, transfer or reserve transaction was performed.
- Updated minimatch/glob/uuid/Vite/ws/tmp resolution without a framework-major
  migration. Frontend Next.js resolved its compatible patched 15.5.28 release.
- CI now fails on medium/high Bandit findings and preserves pipeline failure.
  Deployment no longer has a fallback that ignores migration failures.

## Verification before publication

- 86 targeted backend tests passed, no skips. Subsequent amount precision checks
  are being rechecked before push.
- Frontend: 115 tests, lint, TypeScript and production build passed.
- Mobile: 352 workspace tests plus 13 security tests, workspace type checks,
  Expo Doctor 19/19 and Android bundle export passed.
- npm audit: zero findings in frontend, mobile and rACP operator-tool lockfiles.
- pip-audit: no known vulnerabilities in runtime inputs.
- Bandit: no medium/high findings; low heuristic findings remain for review.
- Secret scanner: 2,079 tracked files, no findings.
- Official MCP Python SDK: remote and stdio handshake, all nine schemas and
  tool-error responses passed with negotiated protocol 2025-11-25.
- Fresh PostgreSQL migrations through 098_merge_release_heads were verified in
  the preceding candidate. CI will repeat migrations on a clean database.

## Publication acceptance

Push, full CI, merge, deployment and live build/readiness verification are still
pending at this document's creation. Record their evidence after publication.
The long local full-suite run encountered two HTTP-client mock signatures;
these are fixed and pass in the targeted rerun. Do not count that interrupted
or failing snapshot as a fully passed final regression run.

Existing uncommitted payment-provenance drafts remain preserved outside the
release worktree and are not exposed. Physical iOS/Android store acceptance,
real funded payment settlement, partner offers and payment-grade OCR remain
separate acceptance gates. Existing balances and obligations are unchanged;
rACP/EUR policy is retained.
