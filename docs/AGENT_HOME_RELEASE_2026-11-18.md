# Agent review and homepage animation repair — 18 November 2026

Baseline: GitHub master `c761cf23`. This is a bounded review of the available
Hermes/OpenClaw results and the failed GitHub checks, not a blanket security certification.

## Agent results and local recovery

At intake, Hermes remained at `154ae971` and OpenClaw at `10caacdf`, the same heads
reviewed on 15 November. Their useful changes are already integrated by PR #160;
the unsafe zero-deadline airdrop relaxation and earlier rejected backlog remain
excluded. There are no additional accepted commits to merge from these heads.
Failed drafts/stashes are not release candidates.

Both isolated working directories contained missing tracked files (41 Hermes,
18 OpenClaw). Only absent tracked paths were restored from each directory's own
HEAD. Existing edits and retained stashes were preserved. The local repair
inventory is `agent-bridge/runtime/workspace-repair-20261118.json` (not public).
Ollama was not listening on loopback port 11434; the existing local service was
started with the documented single-runner/context settings. Its version/model
endpoints responded and both agents resumed planning. This is service recovery,
not evidence of a new successful autonomous product result.

During review, OpenClaw attempted to replace unknown-route rejection in
`projectPresentation` with a generic Crypto result and remove existing test
assertions. The acceptance guard rejected that attempt. No such fallback is
included in this release; subsequent drafts still require their normal gates.

## Homepage repair

The marketing redesign excluded `/` from NetworkBackground and placed an opaque
first-run surface above the global background. Restoring only the route condition
would draw a canvas hidden behind that surface.

Mount the original network renderer inside the isolated first-run surface, above
its background and below its content. Keep one canvas on the homepage; preserve
the separate `/projects` and `/investors` presentation behavior, light/dark visual
contrast, pointer transparency, reduced-motion handling and visibility cleanup.

The new browser regression failed on the previous production homepage because
the canvas was missing. The corrected tests verify painted pixels change over
time, compare hero screenshots with the network visible/hidden to detect opaque
covering layers, exercise desktop/mobile in both themes, and verify a static
reduced-motion frame resumes when the preference changes. The workflow CTA
remains reachable.

## GitHub security repair

Crypto CI run `43869333705` failed its dependency audit. Update the lockfile using
Cargo, without suppressing advisories or changing the ACP protocol:

- quinn-proto 0.11.18 → 0.11.19 (RUSTSEC-2026-0523 and -0524).
- quinn-udp 0.5.14 → 0.5.16 (RUSTSEC-2026-0538).
- libz-sys 1.1.31 → 1.1.33 (newly discovered RUSTSEC-2026-0544).
- rustix 1.1.4 → 1.1.6 (RUSTSEC-2026-0486 unsound xattr API).

Fresh cargo-audit succeeds with no vulnerability/unsound findings. Seven
unmaintained-package warnings remain: basic-toml, bincode, chrono, paste and the
three pqcrypto crates. Replacing serialization or cryptographic libraries requires
a separately reviewed compatibility migration; no warning is silenced here.

## Validation and acceptance

- Frontend unit suite: 131 passed; TypeScript passed.
- Animation browser suite: 5 passed, including theme, mobile and compositing checks.
- Existing first-run responsive/language checks passed; the CTA/auth-return scenario
  passed on a focused rerun after a local development-server startup failure.
- Targeted backend/auth/cost/RPC suite: 30 passed.
- ACP crypto tests passed with both default PQC and classical-only features.
- Tracked secret scan: 2239 files, no findings; Alembic has one head.

Full Linux node/FFI/wallet compatibility, GitHub CI and deployment are accepted by
the matching PR/master workflow results. Production activation must also match
`/internal/frontend-build`; local code edits alone do not establish deployment.
No issuance, signing, bridge reserve operation or contract deployment is included.

The full deploy path now builds API, frontend and ACP-node sequentially, avoiding
the documented concurrent compiler/Next.js resource contention. All images must
build before migrations or activation; isolated shell tests verify service order
and that frontend/node build failures prevent activation. Use full deployment so
the patched Rust dependencies reach the production ACP-node image as well.
