> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Public audit checklist

Public-ready checklist for reviewing ANCAP as a technical project.

This is not an internal secret-handling runbook. It is the public checklist a reviewer, contributor, or auditor can use to see whether the repo tells a coherent and honest story.

## 1. Repository basics

Confirm the repo includes:
- `README.md`
- `LICENSE`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- issue templates / PR template
- CI workflows under `.github/workflows/`
- source-of-truth roadmap (`MASTER_ROADMAP.md`)

## 2. Docs truthfulness

Check that docs do not contradict runtime or roadmap reality:
- `MASTER_ROADMAP.md`
- `docs/STATUS_MATRIX.md`
- `docs/OPEN_SOURCE_GITHUB_TRANSPARENCY.md`
- bridge docs and release docs

Reviewer question: does the repo claim only what is actually implemented and verified?

## 3. Security posture

Check public security surfaces:
- `SECURITY.md`
- responsible disclosure path
- no committed production secrets
- deploy instructions fail closed on missing required secrets
- secret scanning / push protection are enabled on GitHub

## 4. Release hygiene

Check release evidence:
- release workflow exists in `.github/workflows/release.yml`
- release process doc exists in `.github/RELEASE_PROCESS.md`
- release notes / changelog documents are present
- tags/releases policy is documented

## 5. Contract transparency

Check:
- `contracts/bridge-bsc/src/WACP.sol`
- `contracts/bridge-bsc/src/BridgeGateway.sol`
- `contracts/bridge-bsc/README.md`
- `docs/OFFICIAL_CONTRACT_ADDRESSES.md`
- `docs/CONTRACT_VERIFICATION_GUIDE.md`

Reviewer question: can a third party rebuild and reason about the published contract surfaces?

## 6. Bridge operational truth

Check:
- `docs/bridge-spec-v1.md`
- `docs/bridge-pilot-mainnet.md`
- `docs/OFFICIAL_CONTRACT_ADDRESSES.md`
- `docs/BRIDGE_RISK_DOCUMENTATION.md`
- `docs/bridge-launch-checklist.md`

Reviewer question: is the bridge represented truthfully as an operator-mediated reserve-backed rail, not a trustless bridge?

## 7. Integration surface quality

Check:
- examples under `examples/`
- API docs / public routes described in `README.md`
- SDK/integration claims match actual files

Reviewer question: can an external builder discover at least one realistic integration path from repo docs alone?

## 8. Test and CI evidence

Check that current claims are backed by automated surfaces where appropriate:
- backend CI
- frontend CI
- CodeQL
- targeted regression tests for new repo-level claims

Reviewer question: does the repo merely describe quality, or also enforce parts of it automatically?

## 9. Audit verdict template

A lightweight public audit note should answer:
- What commit / tag was reviewed?
- Which docs were treated as source of truth?
- Which claims were verified directly?
- Which items remain open or operationally risky?
- Did the repo tell one coherent story, or several contradictory ones?
