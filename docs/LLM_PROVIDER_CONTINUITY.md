# LLM provider continuity

2026-11-01: the configured Teneta endpoint returned HTTP 401 (`invalid api key`)
for a live service probe. A configured key alone does not prove provider health.
Rotate that credential to restore the primary route; do not put keys in reports.

The optional reserve keeps actual AI execution available when the platform's
primary provider rejects or cannot complete a request:

```dotenv
LLM_OPENROUTER_FALLBACK_ENABLED=true
LLM_OPENROUTER_FALLBACK_MODEL=anthropic/claude-sonnet-4.6
```

It uses the existing server-side `OPENROUTER_API_KEY`. The reserve model is paid
by the configured provider account; check its credit and limits before enabling.
The default is disabled. Apply the environment through the normal compose
deployment after CI succeeds.

The primary route is tried first. Reserve requests retain the workflow/trial
token cap and carry `provider.data_collection=deny` and `provider.zdr=true`.
If no eligible endpoint is available, the existing degraded-template handling
remains in effect; privacy restrictions are never relaxed to obtain a response.
These routing controls follow the [provider's documented policy](https://openrouter.ai/blog/insights/zero-data-retention/).
HTTPS host restrictions, disabled redirects and isolated HTTP client settings
are shared with the existing OpenRouter transport.

Customer BYOK keys and explicitly pinned provider/model choices never use the
platform reserve. Disabled execution and compliance-locked workflows keep
their existing behavior. A trial's smaller token budget also applies to reserve
execution.

Successful reserve output is actual AI output, so `fallback_used` remains false
(that field denotes a template substitute). Receipts identify the actual
`provider` and `model`, with `provider_fallback_used=true` and the classified
`primary_failure_reason`. Usage-event metadata retains primary provider/model
and any reserve failure classification, without provider credentials or raw
upstream error messages. Primary health remains degraded until its credential
is repaired.

Regression coverage: `tests/unit/test_llm_provider_failover.py`, workflow store,
workflow operations, homepage chat and MCP commerce tests. Live acceptance must
exercise the reserve itself; a homepage chat reply alone is insufficient.
