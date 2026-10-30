> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# ANCAP docs repo initial issues seed

Status: active prep for the future public `ancap-docs` repository.

This seed captures the first small public-safe issue backlog for the future docs repo so launch-day tracking does not start from an empty board or chat-memory reconstruction.

## Goal

Open the future docs repo with a starter issue set that:
- proves the label / milestone / board taxonomy is actually usable;
- gives maintainers and early contributors a clear first queue;
- keeps the first public issues aligned with roadmap truth and trust-surface priorities.

## Recommended initial issues

### 1. Align Discussions categories and pin seeded bootstrap topics
Use for:
- removing or repurposing extra default live categories such as `General` / `Polls` if they still exist;
- updating category descriptions to match the checked-in ANCAP seed;
- pinning the seeded bootstrap topics so the Discussions landing surface stops depending on memory.

Suggested routing:
- milestone: `Docs repo bootstrap`
- labels: `docs`
- board fields: `Status=Inbox`, `Area=docs`, `Priority=P1`
- expected live state: `OPEN`
- status note: keep this one open until the remaining live Discussions category-description drift, extra default categories, and unpinned seeded bootstrap topics are actually fixed in the public repo UI.

### 2. Publish official contract-address and verification index
Use for:
- one public-safe page that lists official ACP / wACP / bridge contract addresses and explorer links;
- cross-links to contract-verification guidance and bridge-risk docs;
- explicit fake-contract / scam-warning copy near the official address list.

Suggested routing:
- milestone: `Trust and audit docs baseline`
- labels: `docs`, `contracts`, `security`, `bridge`
- board fields: `Status=Inbox`, `Area=contracts`, `Priority=P1`
- expected live state: `CLOSED`
- status note: this seed is meant to stay closed once the public-safe contract-address and verification index is live in the exported docs bundle and the matching live repo issue has been completed.

### 3. Add public integration examples index and cross-links
Use for:
- a contributor-friendly index page for payment, wallet, and bridge-facing public examples;
- linking those example surfaces from the docs-repo landing pages and integration docs;
- making the first public integration backlog visible without browsing the whole monorepo tree.

Suggested routing:
- milestone: `Integration docs and examples`
- labels: `docs`, `sdk`, `good first issue`
- board fields: `Status=Inbox`, `Area=sdk`, `Priority=P2`
- expected live state: `CLOSED`
- status note: this seed is meant to stay closed once the public integration examples index and the intended cross-links are live in the exported docs bundle and the matching live repo issue has been completed.

### 4. Reconcile roadmap / status / changelog wording for the first monthly update
Use for:
- checking that `MASTER_ROADMAP.md`, `docs/STATUS_MATRIX.md`, and `docs/CHANGELOG_PUBLIC.md` describe the same shipped truth;
- turning any wording drift into explicit follow-up edits before the first public monthly update;
- ensuring the update cadence seed can point at honest source documents instead of contradictory copy.

Suggested routing:
- milestone: `Roadmap and status sync`
- labels: `docs`, `help wanted`
- board fields: `Status=Inbox`, `Area=docs`, `Priority=P2`
- expected live state: `CLOSED`
- status note: this seed is meant to stay closed once the roadmap / status / changelog wording slice is aligned in the exported docs bundle and the matching live repo issue has been completed.

## Application notes

- Keep the starter issue set intentionally small; the goal is a credible first public queue, not backlog theater.
- Prefer issues that are public-safe, roadmap-aligned, and understandable without private operator context.
- Use `good first issue` only when the work is genuinely approachable and low-context.
- Do **not** seed issues for private infra, signer internals, secrets, abuse controls, or operator-only chores.

## Bootstrap usage

During the first `ancap-docs` repo setup:

1. Create labels and milestones first.
2. Use this file plus `.github/bootstrap/ancap-docs-initial-issues.json` as the source of truth for the first public issue backlog.
3. Treat `expected live state` + `status note` as checked-in truth too, so the bootstrap helper can verify whether a seeded issue should still be open or is intentionally closed because the shipped docs slice is already live.
4. Map each seeded issue into the suggested milestone and board fields from `docs/ANCAP_DOCS_PROJECT_BOARD_SEED.md`.
5. If launch-day reality changes one of these starter issues, update this file and the matching JSON seed together.

## Definition of done for this prep slice

This seed is doing its job when the future docs repo can open with a small, public-safe, roadmap-aligned starter backlog and the first public issues no longer depend on someone recreating them from memory.