# OpenClaw / Hermes commit repair — 9 November 2026

Integration baseline: GitHub master `6c7216ef`. Original agent history is retained;
no history rewriting, force push or deployment is part of this repair. The user's
pre-existing staged/unstaged work is preserved separately from the reviewed branch.

## Findings and disposition

The local agents used stale branches and tests unrelated to some production edits.
A model approving a short diff was insufficient evidence of correctness. The
per-commit inventory is `AGENT_COMMIT_DISPOSITIONS_2026-11-09.json`.

Rejected changes include:

- Hermes `0cb268de`: `_scan_address_utxo_units` reads undefined `units_list`.
- Hermes `aec06357`: remainder becomes Decimal, contradicting the integer API,
  while Decimal context rounding remains unfixed. Replaced with integer arithmetic.
- Hermes `924ba16b`: negative amount formatting is incorrect and ordinary values
  acquire eight trailing decimals. Replaced with signed exact integer formatting.
- Hermes `a32d5f03`, `a693a8ee`: OCR errors other than a small status set become
  accepted. Preserve the existing non-200 rejection.
- Hermes `7b90887b` and follow-ups: malformed encrypted credentials become empty
  plaintext instead of failing authentication. Preserve fail-closed behavior.
- Hermes `f982326b`, `9df3da1e`: substitutes a payment-method name for a paylink ID.
- Hermes `48131317` and follow-ups: redundant mapped-IP checks after canonicalization;
  public IPv6 may reach an unsupported `is_ula` attribute. Preserve existing policy.
- Hermes `d4676e64`: enumerating dictionary items still indexes consecutive IDs;
  it does not repair the claimed response-order race. Original ID mapping retained.
- OpenClaw `f7b4e196`: catches Next.js redirect control flow, breaking navigation.
- OpenClaw `a7f537db`: replaces the working redirect with a relative server fetch
  to an invented transaction endpoint.
- OpenClaw `646cbc19`, `bcafc01d`: replaces valid locale keys with invented packs/URLs.
- OpenClaw `dd9b6276`: leaves payment confirmation busy after completion.
- OpenClaw rendering try/catch changes: JSX creation does not catch descendant
  render failures. Existing Next.js boundaries are retained.
- OpenClaw BigInt/deadline/fragment/fallback/import/format changes: either equivalent
  code, redundant preconditions or unproved behavior changes. Not integrated.
- Arbitrary links, token banners, silent error removal and unrelated log messages
  are excluded. Existing current-master fixes remain intact.

Retained: existing master consolidation of role/bootstrap/RPC/UI fixes, JSON Accept
header, and accessible review feedback. The genuine amount precision defect is
fixed without changing the 1 ACP = 10 rACP equivalent ratio or legacy obligations.

## Stronger acceptance

Automatic selection requires a related test file. Every automatically planned fix
must change its regression suite. An isolated export first runs original baseline
tests successfully, then requires the revised tests to fail by assertion against
unchanged baseline production code. Import/syntax/name errors and test collection
failures do not count. Ordinary checks then verify the edited production code.
The model reviewer receives actual source as well as the diff and must verify the
ticket diagnosis. Completed demonstration seeds are removed from configuration.

Existing inference serialization, fixture preflight, path guards and preservation
of failed attempts are published with a dedicated Windows Agent Bridge CI workflow.
Neither agent can push, merge or deploy automatically.

## Verification

Exact integer regressions were demonstrated against master: original 8 tests pass;
revised suite exposes 3 assertion failures. The corrected targeted suite passes (18 tests).
Frontend: 122 unit tests and TypeScript pass. 43 coordination checks and the native scope checks pass; the migration graph has
one head (`106_renewal_events_rop04`). GitHub CI acceptance is tracked on the PR.

The evidence covers the reviewed commit backlog and acceptance mechanism; it is
not a claim that every possible ANCAP defect is eliminated.
