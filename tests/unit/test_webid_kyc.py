"""WebID KYC partner-slot unit tests (no live API calls)."""
from __future__ import annotations

import hashlib
import hmac
from functools import partial
from urllib.parse import urlparse

import pytest

from app.services import webid_kyc as webid


def _settings(**overrides):
    base = {
        "webid_enabled": False,
        "webid_api_base": "",
        "webid_client_id": "",
        "webid_client_secret": "",
        "webid_create_path": "/api/v1/identification",
        "webid_light_redirect_base": "",
        "webid_return_url": "https://ancap.cloud/cards",
        "webid_webhook_secret": "",
        "webid_product": "VideoID",
    }
    base.update(overrides)
    return type("S", (), base)()


def _default_settings():
    return _settings()


def test_webid_status_fail_closed_by_default(monkeypatch):
    monkeypatch.setattr("app.services.webid_kyc.get_settings", _default_settings)
    assert webid.webid_is_configured() is False
    assert webid.webid_sessions_ready() is False
    status = webid.webid_public_status()
    assert status.configured is False
    assert status.enabled is False
    assert status.sessions_ready is False
    assert status.issues_cards is False
    assert status.apple_pay_ready is False
    assert status.role == "kyc_partner_slot"
    assert status.waitlist_interest == "physical_card_apple_pay"
    assert status.session_path == "/v1/commerce/webid/session"
    assert status.webhook_path == "/v1/commerce/webid/webhook"
    partner = urlparse(status.partner_url)
    assert partner.scheme == "https" and partner.hostname == "webid-solutions.com"


def test_webid_enabled_still_fail_closed_without_credentials(monkeypatch):
    monkeypatch.setattr(
        "app.services.webid_kyc.get_settings",
        partial(_settings, webid_enabled=True, webid_api_base="https://example.invalid"),
    )
    assert webid.webid_is_configured() is False
    status = webid.webid_public_status()
    assert status.enabled is True
    assert status.configured is False
    assert status.sessions_ready is False
    assert status.issues_cards is False


@pytest.mark.asyncio
async def test_start_session_fail_closed(monkeypatch):
    monkeypatch.setattr("app.services.webid_kyc.get_settings", _default_settings)
    with pytest.raises(webid.WebIdNotConfigured):
        await webid.start_webid_session(user_id="user-1")


@pytest.mark.asyncio
async def test_start_session_light_redirect_without_upstream(monkeypatch):
    monkeypatch.setattr(
        "app.services.webid_kyc.get_settings",
        lambda: _settings(
            webid_enabled=True,
            webid_api_base="https://example.invalid",
            webid_client_id="cust",
            webid_client_secret="secret",
            webid_create_path="",
            webid_light_redirect_base="https://gateway.example/light",
        ),
    )
    result = await webid.start_webid_session(user_id="user-1")
    assert result.status == "ready"
    assert result.issues_cards is False
    assert result.redirect_url is not None
    assert result.redirect_url.startswith("https://gateway.example/light?")
    assert "actionId=" in result.redirect_url
    assert "returnUrl=" in result.redirect_url


def test_webhook_signature_hmac(monkeypatch):
    secret = "test-webhook-secret"
    monkeypatch.setattr(
        "app.services.webid_kyc.get_settings",
        lambda: _settings(webid_webhook_secret=secret),
    )
    body = b'{"event":"identification.completed","actionId":"123456789","status":"success"}'
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert webid.verify_webid_webhook_signature(body, digest) is True
    assert webid.verify_webid_webhook_signature(body, f"sha256={digest}") is True
    assert webid.verify_webid_webhook_signature(body, "deadbeef") is False
    assert webid.verify_webid_webhook_signature(body, None) is False


def test_summarize_webhook_fields():
    meta = webid.summarize_webid_webhook(
        {"event": "identification.completed", "actionId": "123456789", "status": "success"}
    )
    assert meta["event"] == "identification.completed"
    assert meta["action_id"] == "123456789"
    assert meta["identification_status"] == "success"
