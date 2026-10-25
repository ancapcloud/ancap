"""Homepage dialog: automatic OpenRouter free model, key stays server-side."""
from __future__ import annotations

from types import SimpleNamespace

import anyio
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from starlette.requests import Request

from app.schemas.home_chat import HomeChatRequest
from app.services.home_chat import (
    HomeChatError,
    HomeChatResult,
    build_messages,
    clear_home_chat_state,
    complete_home_chat,
    free_model_ids,
    pretty_model,
)
from app.services.rate_limit import clear_rate_limit_state


def _settings(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "home_chat_enabled": True,
        "openrouter_api_key": "test-key",
        "openrouter_base_url": "https://openrouter.ai/api/v1",
        "openrouter_site_url": "https://ancap.cloud",
        "openrouter_app_name": "ANCAP",
        "home_chat_timeout_seconds": 5,
        "home_chat_max_tokens": 200,
        "home_chat_ip_limit": 2,
        "home_chat_ip_window_seconds": 3600,
        "home_chat_global_limit": 50,
        "home_chat_global_window_seconds": 86400,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _request() -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/v1/home-chat/messages",
        "headers": [(b"x-forwarded-for", b"203.0.113.8")],
        "client": ("203.0.113.8", 1234),
        "query_string": b"",
        "scheme": "http",
        "server": ("test", 80),
    }
    return Request(scope)


def test_pretty_model_and_free_filter():
    assert pretty_model("google/gemma-3-12b-it:free") == "Gemma 3 12B"
    assert pretty_model("meta-llama/llama-3.3-70b-instruct:free") == "Llama 3.3 70B"
    assert pretty_model("qwen/qwen-2.5-7b-instruct:free") == "Qwen 2.5 7B"
    assert pretty_model("openrouter/free") == "Free auto"
    ids = free_model_ids(
        [
            {"id": "openai/gpt-4o", "pricing": {"prompt": "0.01", "completion": "0.03"}},
            {"id": "openrouter/free", "pricing": {"prompt": "0", "completion": "0"}},
            {
                "id": "google/gemma-3-12b-it:free",
                "pricing": {"prompt": "0", "completion": "0", "request": "0"},
                "architecture": {"output_modalities": ["text"]},
            },
            {
                "id": "vendor/picture:free",
                "pricing": {"prompt": "0", "completion": "0"},
                "architecture": {"output_modalities": ["image"]},
            },
            {"id": "qwen/qwen-2.5-7b-instruct:free", "pricing": {"prompt": "0", "completion": "0"}},
        ]
    )
    assert ids[0] == "google/gemma-3-12b-it:free"
    assert "openai/gpt-4o" not in ids
    assert "vendor/picture:free" not in ids
    assert "openrouter/free" not in ids


def test_client_cannot_choose_model():
    with pytest.raises(ValidationError):
        HomeChatRequest.model_validate(
            {"messages": [{"role": "user", "content": "hi"}], "model": "openai/gpt-4o"}
        )


def test_build_messages_uses_language_and_hides_secrets():
    wired = build_messages(
        messages=[{"role": "user", "content": "Привет"}],
        mode="plan",
        lang="ru",
    )
    assert wired[0]["role"] == "system"
    assert "Russian" in wired[0]["content"]
    assert "plan" in wired[0]["content"].lower() or "Plan" in wired[0]["content"] or "idea" in wired[0]["content"]
    assert "sk-or-" not in wired[0]["content"]
    assert wired[-1] == {"role": "user", "content": "Привет"}


def test_routes_registered():
    from app.main import app

    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/v1/home-chat/messages" in paths
    assert "/v1/home-chat/status" in paths
    assert "/home-chat/messages" in paths


def test_fallback_skips_paid_models(monkeypatch):
    clear_home_chat_state()
    calls: list[tuple[str, str | None]] = []

    async def fake_request(method: str, path: str, json_body: dict | None = None):
        model = None if json_body is None else json_body.get("model")
        calls.append((path, model if isinstance(model, str) else None))
        if path == "/chat/completions" and model == "openrouter/free":
            return 404, {"error": {"message": "No endpoints found for model"}}
        if path == "/models":
            return 200, {
                "data": [
                    {"id": "openai/gpt-4o", "pricing": {"prompt": "0.01", "completion": "0.02"}},
                    {"id": "google/gemma-3-12b-it:free", "pricing": {"prompt": "0", "completion": "0"}},
                ]
            }
        assert isinstance(model, str) and model.endswith(":free")
        return 200, {"model": model, "choices": [{"message": {"content": "Готово"}}]}

    monkeypatch.setattr("app.services.home_chat.get_settings", lambda: _settings())
    monkeypatch.setattr("app.services.home_chat._openrouter_request", fake_request)

    async def _run() -> HomeChatResult:
        return await complete_home_chat(messages=[{"role": "user", "content": "Привет"}], lang="ru")

    result = anyio.run(_run)
    assert result.reply == "Готово"
    assert result.model.endswith(":free")
    assert result.label == "Gemma 3 12B"
    assert calls[0] == ("/chat/completions", "openrouter/free")
    assert all(model is None or model == "openrouter/free" or model.endswith(":free") for _, model in calls)
    clear_home_chat_state()


def test_refuses_off_host_base_url(monkeypatch):
    class Boom:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("network")

    monkeypatch.setattr("app.services.home_chat.httpx.AsyncClient", Boom)
    monkeypatch.setattr(
        "app.services.home_chat.get_settings",
        lambda: _settings(openrouter_base_url="http://169.254.169.254/latest"),
    )

    async def _run() -> None:
        with pytest.raises(HomeChatError) as caught:
            await complete_home_chat(messages=[{"role": "user", "content": "hi"}])
        assert caught.value.code == "NOT_CONFIGURED"

    anyio.run(_run)


def test_missing_key_is_503(monkeypatch):
    from app.api.routers.home_chat import post_home_chat

    monkeypatch.setattr(
        "app.api.routers.home_chat.get_settings",
        lambda: _settings(openrouter_api_key=""),
    )
    payload = HomeChatRequest.model_validate({"messages": [{"role": "user", "content": "hi"}]})

    async def _run() -> None:
        with pytest.raises(HTTPException) as caught:
            await post_home_chat(payload, _request())
        assert caught.value.status_code == 503
        assert caught.value.detail["code"] == "NOT_CONFIGURED"

    anyio.run(_run)


def test_rate_limit_and_automatic_reply(monkeypatch):
    from app.api.routers.home_chat import post_home_chat

    clear_rate_limit_state()
    monkeypatch.setattr("app.api.routers.home_chat.get_settings", lambda: _settings(home_chat_ip_limit=2))

    async def fake_complete(**kwargs: object) -> HomeChatResult:
        assert "model" not in kwargs
        return HomeChatResult(reply="ok", model="google/gemma-3-12b-it:free", label="Gemma 3 12B")

    monkeypatch.setattr("app.api.routers.home_chat.complete_home_chat", fake_complete)
    payload = HomeChatRequest.model_validate({"messages": [{"role": "user", "content": "hi"}], "mode": "cloud"})

    async def _run() -> None:
        first = await post_home_chat(payload, _request())
        assert first.selection == "automatic"
        assert first.model.endswith(":free")
        await post_home_chat(payload, _request())
        with pytest.raises(HTTPException) as caught:
            await post_home_chat(payload, _request())
        assert caught.value.status_code == 429

    anyio.run(_run)
    clear_rate_limit_state()
