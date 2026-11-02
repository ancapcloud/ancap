"""Unit tests for the global rate-limit middleware helpers."""

from __future__ import annotations

import hashlib

from app.api.global_rate_limit import request_identity, should_rate_limit_path


def _scope(headers: dict[str, str] | None = None, client=("203.0.113.7", 1234)):
    return {
        "type": "http",
        "path": "/v1/users/me",
        "headers": [
            (key.lower().encode("latin-1"), value.encode("latin-1"))
            for key, value in (headers or {}).items()
        ],
        "client": client,
    }


def test_health_and_docs_paths_are_not_limited():
    for path in (
        "/",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
        "/openapi.json",
        "/v1/system/health",
        "/v1/system/ready",
        "/v1/metrics",
    ):
        assert should_rate_limit_path(path) is False, path


def test_api_paths_are_limited():
    assert should_rate_limit_path("/v1/users/me") is True
    assert should_rate_limit_path("/v1/wallet/acp/balance") is True


def test_api_key_is_hashed_not_persisted():
    raw_key = "ancap_live_secret_value"
    ip, subject = request_identity(_scope({"X-API-Key": raw_key}))
    assert ip == "203.0.113.7"
    assert subject == "key:" + hashlib.sha256(raw_key.encode()).hexdigest()[:16]
    assert raw_key not in (subject or "")


def test_bearer_api_key_is_recognised():
    _, subject = request_identity(_scope({"Authorization": "Bearer ancap_abc123"}))
    assert subject == "key:" + hashlib.sha256(b"ancap_abc123").hexdigest()[:16]


def test_forwarded_ip_is_used_when_present():
    ip, subject = request_identity(
        _scope({"X-Forwarded-For": "198.51.100.9, 10.0.0.1"})
    )
    assert ip == "198.51.100.9"
    assert subject is None


def test_client_address_is_the_fallback():
    ip, subject = request_identity(_scope(client=("192.0.2.44", 443)))
    assert ip == "192.0.2.44"
    assert subject is None


def test_middleware_returns_429_after_limit(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api.global_rate_limit import GlobalRateLimitMiddleware
    from app.config import get_settings
    from app.services.rate_limit import clear_rate_limit_state

    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "1")
    get_settings.cache_clear()
    clear_rate_limit_state()

    limited = FastAPI()
    limited.add_middleware(GlobalRateLimitMiddleware)

    @limited.get("/v1/ping")
    def ping():
        return {"ok": True}

    try:
        client = TestClient(limited)
        assert client.get("/v1/ping").status_code == 200
        blocked = client.get("/v1/ping")
        assert blocked.status_code == 429
        assert blocked.headers["Retry-After"] == "60"
        assert blocked.json()["detail"]["code"] == "RATE_LIMITED"
    finally:
        get_settings.cache_clear()
        clear_rate_limit_state()

