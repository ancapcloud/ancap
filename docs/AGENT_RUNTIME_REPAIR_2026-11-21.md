# Agent runtime follow-up — 21 November 2026

Baseline: merged controller release 19870ba9. Both processes were live but useful
acceptance was failing. This work addresses observed controller/planner failures;
it does not guarantee the local model will always reason correctly.

OpenClaw's line-based guard rejected any removed line containing it/expect,
including a test-title expansion that preserved every old assertion and added a
new one. Replace the heuristic with a TypeScript syntax comparison: preserve
existing statements, setup, runners and assertions; allow additional test cases,
assertions and it.each inputs. Reject removed/changed checks, setup changes,
runner skip changes and reduced parameter sets. Model review and independent
baseline-red/revised-green proof remain required; this is not a security sandbox
or a complete semantic proof against all forms of test weakening.

The planner repeatedly returned invalid/unverifiable proposals, sometimes with
truncated JSON. Those errors previously changed only transient status, so the
next planner invocation did not receive them in its recent-work journal. Use
bounded JSON schemas for planning and review; require a concrete failing input,
actual and expected result, reject identical results and explicit truncation.
Persist planning rejections and include them in the ordinary failure report.
The existing exact-source evidence check remains in place.

Live verification exposed another false rejection: a normal missing-exception
failure from pytest.raises is pytest.fail.Exception, not AssertionError. The
baseline reporter now recognizes both standard expectation-failure types, still
requiring the call phase and rejecting import/collection/runtime exceptions.
The real isolated baseline probe covers pytest.raises and still rejects a
TypeError-only failure.

The actor prompt now places the exact assigned task after source/inbox examples,
and explicitly preserves its concrete failing input. A regression checks this
ordering. This follows a real OpenClaw attempt that copied a valid chain ID from
an old test instead of the assigned whitespace input; project checks correctly
rejected that attempt even though model review approved it.

Controller tests: final full run 62 passed. Frontend parser checks use installed
TypeScript. CI installs locked frontend dependencies
without install scripts so it can exercise the same parser.

Live validation uses the actual existing OpenClaw/Hermes runtimes, file guards,
shared inference lane, independent model review, baseline probe and project
checks. The controller specified the two concrete tasks: whitespace-only MetaMask
chain IDs and explicit zero webhook ports. These are agent-written outputs from
controller-specified tasks, not evidence of successful autonomous task discovery.
Acceptance results and commit IDs are recorded below. No signing,
token issuance, reserve operations or permission changes are included.

OpenClaw live result: 347446a5, independently verified Vitest and TypeScript,
with a failing baseline regression and successful revised suite. The concrete
whitespace input is present in the actual test; model summaries are not used as
substitutes for file/test evidence. Earlier incorrect-input drafts remain stashed.

Repairs must change their preserved output. An unchanged repair is rejected
before another model review or project check, avoiding repeated acceptance work
on the same uncorrected draft.

Repeated failure to correct a missing pytest import led to a differential local
native-tool probe, without executing model-supplied code. DeepSeek/heretic failed
the import case (it returned the unchanged broken test) and passed the whitespace
case. Already-installed standard ancap-qwen:9b passed both. Explicitly select it
for the managed planner/reviewer, Hermes CLI and ancap OpenClaw profile; preserve
65536 context, one model lane, guards and the previous weights/config backups.
The OpenClaw profile passed its installed config validator without warnings.
The main interactive profile was not part of this managed-profile change.
These are narrow diagnostic probes, not a general capability benchmark.

The installed OpenClaw schema has agents.entries.ancap-site.model, which overrides
agents.defaults.model. Update that dedicated entry and explicitly pass
--model ollama/<selected-model> in every managed OpenClaw command. Hermes already
receives an explicit --model; both commands now pin the same selected model.
The real OpenClaw execution metadata confirms provider ollama, model ancap-qwen:9b.

Preserve original_instructions across repairs. Review compares the cumulative
diff with the original ticket and identifies the latest incremental repair focus
separately. A narrow import-only repair description must not incorrectly forbid
the production fix preserved from the original task.

Final live acceptance:

- Hermes 6370ad60: agent-written zero-port guard and pytest import correction;
  independent baseline-red/revised-green proof and five revised pytest cases
  passed. The controller restored the preserved agent output and reran checks
  and independent review against the original complete ticket after an import-only
  repair description caused a false review rejection. No source was rewritten by
  the controller during that acceptance recovery. Receipt origin is controller-rereview.
- OpenClaw f3fd0a44 on explicitly pinned standard Qwen: preserved the existing
  whitespace check, added an uppercase empty-hex-prefix check, passed baseline
  regression proof, revised Vitest and TypeScript, then committed locally.
- Ordinary automatic scheduling resumed without a maintenance STOP or role
  quarantine. These agent commits remain local task outputs for ordinary product
  integration review/CI; the runtime repair is active on this workstation.
