import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest

from app.services import home_chat, llm

pytestmark = pytest.mark.asyncio


@pytest.fixture
def setup(monkeypatch):
    settings = SimpleNamespace(
        llm_provider="teneta_claude", llm_model="claude-sonnet-4-6",
        llm_timeout_seconds=45, llm_max_tokens=1800, llm_fallback_to_template=True,
        llm_openrouter_fallback_enabled=True,
        llm_openrouter_fallback_model="anthropic/claude-sonnet-4.6",
        openrouter_api_key="test-provider-credential", openrouter_base_url="https://openrouter.ai/api/v1",
        openrouter_site_url="https://ancap.cloud", openrouter_app_name="ANCAP", home_chat_timeout_seconds=45,
    )
    monkeypatch.setattr(llm, "get_settings", lambda: settings)
    monkeypatch.setattr(home_chat, "get_settings", lambda: settings)
    primary = AsyncMock(return_value=("", {}, 0, "failed", "auth_error"))
    monkeypatch.setattr(llm, "_call_with_retry", primary)
    reserve = AsyncMock(return_value=(200, {
        "model": "anthropic/claude-sonnet-4.6",
        "choices": [{"message": {"content": json.dumps({"deliverable": {"summary": "AI result"}})}}],
    }))
    monkeypatch.setattr(home_chat, "_openrouter_request", reserve)
    store = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
    monkeypatch.setattr(llm, "_store_usage_event", store)
    monkeypatch.setattr(llm, "execute_workflow_template", lambda *_: {"deliverable": "vetted template"})
    template = SimpleNamespace(slug="test-report", title="Report", summary="Generate report",
                               category="Tools", output_items=["Report"])
    return settings, primary, reserve, store, template


async def execute(template):
    return await llm.execute_paid_workflow_with_llm(
        None, template=template, inputs={}, owner_user_id=None, workflow_run_id=None,
    )


async def test_auth_failure_uses_reserve_ai_and_records_actual_provider(setup):
    _, _, reserve, store, template = setup
    result = await execute(template)
    assert result.status == "succeeded" and not result.fallback_used
    assert result.provider == "openrouter" and result.model == "anthropic/claude-sonnet-4.6"
    assert result.result["deliverable"]["summary"] == "AI result"
    assert result.result["llm_usage"]["provider_fallback_used"] is True
    assert result.result["llm_usage"]["primary_failure_reason"] == "auth_error"
    metadata = store.call_args.kwargs["metadata"]
    assert metadata["primary_provider"] == "teneta_claude"
    assert metadata["primary_failure_reason"] == "auth_error"
    body = reserve.call_args.args[2]
    assert body["provider"] == {"data_collection": "deny", "zdr": True}
    assert body["max_tokens"] == 1800
    assert "test-provider-credential" not in json.dumps(body)


async def test_primary_success_does_not_call_reserve(setup):
    _, primary, reserve, _, template = setup
    primary.return_value = ('{"deliverable":"primary result"}', {}, 0, "ok", None)
    result = await execute(template)
    assert result.provider == "teneta_claude" and result.status == "succeeded"
    reserve.assert_not_called()


async def test_operator_opt_in_and_configured_key_are_required(setup):
    settings, _, reserve, _, template = setup
    settings.llm_openrouter_fallback_enabled = False
    assert (await execute(template)).fallback_used
    settings.llm_openrouter_fallback_enabled = True
    settings.openrouter_api_key = ""
    assert (await execute(template)).fallback_used
    reserve.assert_not_called()


async def test_customer_byok_or_pinned_model_is_never_forwarded(setup):
    _, _, reserve, _, template = setup
    for credentials in [{"api_key": "customer-private-key"}, {"provider": "openai"}, {"model": "pinned-model"}]:
        token = llm.workflow_provider_credentials.set(credentials)
        try:
            assert (await execute(template)).fallback_used
        finally:
            llm.workflow_provider_credentials.reset(token)
    reserve.assert_not_called()


async def test_trial_token_limit_is_preserved_during_failover(setup):
    _, _, reserve, _, template = setup
    token = llm.workflow_provider_credentials.set({"max_tokens": 800})
    try:
        assert (await execute(template)).status == "succeeded"
        assert reserve.call_args.args[2]["max_tokens"] == 800
    finally:
        llm.workflow_provider_credentials.reset(token)


async def test_compliance_locked_workflow_never_calls_any_provider(setup):
    _, primary, reserve, _, template = setup
    template.slug = "aeterna-adhd-support"
    assert (await execute(template)).status == "compliance_locked"
    primary.assert_not_called()
    reserve.assert_not_called()


async def test_disabled_provider_never_falls_through_to_reserve(setup):
    settings, primary, reserve, _, template = setup
    settings.llm_provider = "disabled"
    assert (await execute(template)).status == "disabled"
    primary.assert_not_called()
    reserve.assert_not_called()


async def test_reserve_rejection_retains_degraded_template_and_failure_trace(setup):
    _, _, reserve, store, template = setup
    reserve.return_value = (402, {"error": {"message": "not persisted"}})
    result = await execute(template)
    assert result.fallback_used and result.failure_reason == "auth_error"
    assert result.result["degraded_run"] is True
    assert store.call_args.kwargs["metadata"]["reserve_failure_reason"] == "balance_error"


async def test_reserve_timeout_is_recorded_without_raw_error(setup, monkeypatch):
    _, _, _, store, template = setup
    monkeypatch.setattr(llm, "_call_openrouter_fallback", AsyncMock(side_effect=TimeoutError()))
    result = await execute(template)
    assert result.fallback_used
    assert store.call_args.kwargs["metadata"]["reserve_failure_reason"] == "timeout"


async def test_auth_failure_records_zero_retries_and_does_not_sleep(setup, monkeypatch):
    _, _, _, _, _ = setup
    request = httpx.Request("POST", "https://provider.invalid/v1/messages")
    error = httpx.HTTPStatusError("redacted", request=request, response=httpx.Response(401, request=request))
    monkeypatch.undo()
    monkeypatch.setattr(llm, "_call_teneta_claude", AsyncMock(side_effect=error))
    sleep = AsyncMock()
    monkeypatch.setattr(llm.asyncio, "sleep", sleep)
    text, _, retries, status, reason = await llm._call_with_retry("teneta_claude", "probe")
    assert not text and retries == 0 and status == "failed" and reason == "auth_error"
    sleep.assert_not_called()


async def test_empty_timeout_is_retryable_and_backoff_yields_event_loop(monkeypatch):
    client = AsyncMock(side_effect=[httpx.ReadTimeout(""), ("result", {})])
    monkeypatch.setattr(llm, "_call_teneta_claude", client)
    sleep = AsyncMock()
    monkeypatch.setattr(llm.asyncio, "sleep", sleep)
    text, _, retries, status, _ = await llm._call_with_retry("teneta_claude", "probe")
    assert text == "result" and retries == 1 and status == "ok"
    sleep.assert_awaited_once_with(1)
    assert llm._classify_failure(httpx.ReadTimeout("")) == "timeout"


async def test_reserve_http_client_rejects_untrusted_host_before_network(setup, monkeypatch):
    settings, _, _, _, _ = setup
    settings.openrouter_base_url = "https://attacker.invalid/api/v1"
    # Restore the actual HTTPS allowlist implementation, not the provider stub.
    monkeypatch.undo()
    monkeypatch.setattr(home_chat, "get_settings", lambda: settings)
    monkeypatch.setattr(llm, "get_settings", lambda: settings)
    with pytest.raises(RuntimeError, match="unavailable"):
        await llm._call_openrouter_fallback("probe")
