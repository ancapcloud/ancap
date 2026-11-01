# Homepage concierge — 2026-11-01

Local implementation inspired by Starli's bounded evidence/action/result pattern.

- Existing modes, five languages, free-only model routing and response fields stay intact.
- A model can request one validated read-only `search_workflows` or `platform_guide` lookup, then must answer. No shell, arbitrary URLs, account access or side effects.
- Workflow search reads active local templates, ranks search terms, and returns at most five entries with catalog-converted prices, outputs and existing run links. Checkout remains authoritative.
- Unknown or malformed actions and repeated lookups fail closed. Internal actions are not returned as answers.
- One wall-clock deadline covers model selection, catalog loading, fallback and the optional follow-up. At most three fallback candidates plus one successful lookup continuation.
- Successful concrete fallback candidates are reported accurately. Missing concrete router identity stays `openrouter/free`, without inventing a model.
- Prompt includes EUR pricing, ACP accounting and rACP equivalent policy. History remains limited to eight supplied messages, with no new anonymous chat storage.

Validation: 20 tests passed across `tests/api/test_home_chat.py` and
`tests/unit/test_text_security_regressions.py` using Python 3.11 with repository runtime dependencies.
Includes tool allowlist, catalog output, repeated lookup bound, total deadline,
malformed provider payloads, model fallback identity and existing API regressions.

Limitations: no live-provider evaluation or deployment performed. Free models may
ignore lookup instructions; grounding instructions reduce hallucinations but do
not constitute semantic verification of every answer. Search is lexical, so a
visitor may need to clarify terms. No persistent memory beyond submitted history.
