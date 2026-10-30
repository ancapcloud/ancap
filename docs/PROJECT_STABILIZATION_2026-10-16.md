> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Stabilization and next development plan — 16 October 2026

## Scope and acceptance

This release checks the public homepage, frontend build, mobile SDK, backend,
GitHub findings and the primary / Oracle / local ACP peers. It preserves the
pre-existing uncommitted native wallet, bridge, SACP and listing work. Passing
CI is not a claim that every open security alert or roadmap item is complete.

## Findings and changes

- Homepage: desktop 1440px and mobile 390px had no uncaught JavaScript errors or
  horizontal overflow. Production presentation tests passed in five languages;
  hydration checks passed on eight core routes. The AI-project link now uses
  the existing translated catalog title in every supported language.
- Payment Scanner: editing or replacing an invoice clears the previous payment
  preview and confirmation. Unsupported/oversized images are rejected before
  upload; preview object URLs are released on replacement and unmount.
- Recovery: explorer network detection checks exact hostnames or dot-delimited
  subdomains; lookalike domains cannot select a trusted chain. Backend uses
  `hostname` rather than `netloc`, so userinfo and ports cannot confuse it.
- Deployment: frontend-only helper fails after exhausted Git fetch retries,
  validates compose configuration, probes the actual :8080 proxy, checks current
  Smart Pay markup and API readiness, and requires the deployed build ID to
  match the checkout. Deployment workflows declare read-only repository access.
- Local node helpers explicitly select the binary target directory and package,
  and fail after a Cargo error rather than starting an older executable.
- `python scripts/check_acp_peers.py` provides a read-only acceptance check:
  all three peers must agree on height/tip and report initialized, consistent
  210M ACP issued/max supply. A missing RPC method fails the check.

## Verified baseline before this release

- Production build: `49f9c5e`; public homepage, API readiness and full health 200.
- Primary and Oracle: height 18, tip
  `ab6bdd19f2bccd95c00b661d88fd0482b9a9c7079287f1ced51ae23e67bcd018`,
  issued supply 210,000,000 ACP and `supply_invariant_ok=true`.
- Local node was stopped. Restarting its existing data restored height/tip 18,
  but its old executable lacked `gettxoutsetinfo`; rebuild acceptance is required.
- Primary services running; API, PostgreSQL and Redis healthy. Primary disk 81%
  used (7.3 GB free); Oracle disk 33% used. Capacity cleanup needs a separate,
  reviewed retention decision rather than deleting node or database data.
- Frontend: 67 unit tests, lint and production build passed before corrections.
- Mobile/SDK: typecheck and 294 tests passed before corrections; the hostname
  regression adds one test.
- Production browser checks: 11 presentation scenarios and 2 hydration scenarios
  passed. These checks did not execute payments or publish reviews.
- Local frontend dependency audit: seven high findings in development tooling
  around braces/Tailwind 3; no patch for the underlying braces advisory was
  advertised. Do not force a Tailwind major upgrade as an untested audit fix.

## Ordered development plan

### P0 — Security and release correctness

1. Complete runtime dependency refresh with a Linux Python 3.11 hashed lock,
   backend regression tests, migration check and production health verification.
2. Triage remaining GitHub CodeQL findings by actual data flow. Separate
   exploitable runtime issues from test fixtures, intentional high-entropy token
   hashing and style findings. Do not dismiss alerts merely to reach zero.
3. Refresh mobile transitive dependencies on a clean baseline, preserving the
   current native wallet work; run npm install/build/typecheck/tests and Android
   release smoke. Track advisories with no upstream patch explicitly.
4. Require three-peer acceptance after node releases and exact deployed commit
   verification after web releases. Keep miner/consensus changes separately reviewed.
5. Review primary-host image/build-cache retention and restore evidence; acceptance
   is sufficient build headroom and a verified recoverable database/node backup.

### P1 — Finish the mobile release already in progress

1. Finish the existing SecureVault/import/export changes in their own commits.
2. Run create, restore, send and sign on Pixel_10_Pro, then physical-device PIN,
   biometrics and MASVS checks. Keep physical sign-off open until measured.
3. Produce signed Play Internal and TestFlight builds; complete iOS native build
   on macOS. Acceptance: reproducible release and documented recovery flow.

### P2 — Deepen the working ACP workflow product

1. Measure discovery → preview → funded run → receipt → repeat-run conversion.
2. Improve paid-run failure/retry explanations and creator delivery review using
   real support evidence; acceptance is a completed ACP run with verifiable receipt.
3. Finish deposit-watcher automation with replay/idempotency/reconciliation tests
   before removing desk assistance. Keep ACP/wACP 1:10 and sACP identities distinct.

### P3 — Expand after the release gates

1. Build React Flow strategy editing after the builder API contract is stable.
2. Enable community project orders and payouts only with explicit acceptance,
   dispute and settlement controls; the current catalog remains preview.
3. Keep securities, wearables, orbital infrastructure and full decentralization
   as separate staged tracks. Their foundation APIs do not mean live external
   infrastructure, licensing, hardware or partner delivery is complete.

## Release completion evidence

- First release `cb318c4`: [backend CI](https://github.com/ancapcloud/ancap/actions/runs/38926121481)
  passed 934 tests (37 skipped), docs regressions, Bandit and Docker build.
  [Frontend CI](https://github.com/ancapcloud/ancap/actions/runs/38926121628)
  passed frontend/mobile SDK jobs and 43 browser scenarios.
  [Deployment](https://github.com/ancapcloud/ancap/actions/runs/38926121813),
  CodeQL, Docs CI and Secret Hygiene passed.
- Rebuilt local node supports supply RPC and HTTPS sync. The legacy data directory
  was retained as `Sicret/acp-node-data-host-legacy-20261016`; the default data
  directory now holds independently synchronized and validated chain state.
  All three peers passed the new supply/tip acceptance check.
- Dependency follow-up updates eight Python packages (aiohttp, mako, multidict,
  python-multipart, starlette, urllib3, web3, yarl), with Linux-resolved pins and
  PyPI artifact hashes. Local `pip check`, 108 targeted backend tests and 39 unit
  tests passed after the upgrade.
- Mobile security patch refreshes compatible XML, URI, brace-expansion, HTTP,
  YAML, CSS, source-map and test-runner dependencies. Existing Expo/RN major
  versions and the uncommitted native-wallet manifest change remain separate.
  Updated mobile/SDK tests (295), typecheck and SDK build passed locally.
- Remaining npm advisories involving Expo/RN/tooling need separate compatibility
  work, including advisories without an upstream patch. They are not all fixed
  by this release. Physical device/store-release gates also remain open.

Recorded 2026-10-21 for published `ab32ea0`: Docs, Secret Hygiene, CodeQL,
Frontend, Backend, Crypto and Deploy ancap.cloud all succeeded on that push.
Live frontend build id is `ab32ea0`; API health returned ok. Job links are in
`MASTER_ROADMAP.md`. Interrupted local full-suite runs are not counted as
completed test runs. CI success does not close the open Dependabot alerts,
physical-device checks or a funded ACP transaction.
