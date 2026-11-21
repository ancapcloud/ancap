# Agent review — 21 November 2026

Baseline: master 9a2be418, PR #162. Review covers new local agent output and
controller recovery; it does not certify the whole product.

## Disposition

Hermes advanced from 154ae971 to 8b5147ff. Reject that commit: its claimed integer
division defect does not exist in payment_wevisone.py. It adds a getattr lookup
for an undeclared setting and tests that inspect source spelling without calling
the OCR operation. A red assertion against the old source is insufficient proof
of a behavioral defect. The previous accepted changes remain in master.

Hermes' pending walletd draft replaces timeout_s with timeout_s or 90 while
claiming multiples of 90 become zero. There is no division. It also replaces
the existing secret-redaction timeout test, removing coverage. Reject the draft.

OpenClaw has no new accepted commit after 10caacdf. Its pending revenueAnalytics
fallback substitutes numeric 0 for string "0" inside Number(), changing no
behavior for the alleged missing-amount case. The existing baseline probe
correctly rejected its green-on-baseline new test. Keep the draft excluded.

Preservation: local branches codex/archive-hermes-20261121 and
codex/archive-openclaw-20261121 retain original heads. Named audit stashes retain
both pending drafts. Runtime audit state and the original OpenClaw pointer/index
are backed up under agent-bridge/runtime (private, ignored by Git).

## Controller corrections

Reject Python division proposals without a division/modulo operation and reject
generated Python test imports of inspect. These narrow guards address observed
failures; they do not replace behavioral review or constitute a sandbox.

OpenClaw's .git file pointed to missing metadata wt-openclaw1 while its reciprocal
registration existed at wt-openclaw with the correct branch. Restore only that
verified relationship, backing up the pointer and metadata. Windows hidden .git
files require r+ mode for updating an existing file. Its restored index was stale;
after preserving it, read-tree HEAD corrected the index and revealed only the
two actual task files. This index intervention is controller recovery, not an
automatic blanket reset. Both worktrees were returned to reviewed master after
stashing their drafts. Historical results and rejection receipts are retained.

Recovery exposed a second root cause: tracked agent-bridge files were junctioned
to the main checkout. A branch switch rewrote live controller edits through that
link. Replace the verified junction with each worktree's own tracked directory.
Do not share tracked code through a junction; absolute controller paths continue
to provide shared runtime/status access. A regression performs an actual checkout
after detaching the link and verifies the live controller remains untouched.

The legacy prompt-context regression depended on local completion status and
failed when the operator's task had already completed. Inject a fixed task in
that test so local and CI runs test the same behavior.

## Validation and release

50 coordination tests and OpenClaw scope-hook checks passed.
Targeted walletd/OCR/RPC compatibility: 45 passed, 2 skipped. Resumed worker
health is recorded separately when available. CI and production activation must be verified
against the merged release SHA; a local green check is not a deployment receipt.
