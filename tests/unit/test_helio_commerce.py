"""MoonPay Commerce / Helio adapter unit tests (no live API calls)."""
from __future__ import annotations

import hashlib
import hmac
import json

from app.services import helio_commerce as helio


def test_helio_status_fail_closed_without_env(monkeypatch):
    monkeypatch.setattr(
        "app.services.helio_commerce.get_settings",
        lambda: type(
            "S",
            (),
            {
                "helio_public_key": "",
                "helio_secret_key": "",
                "helio_paylink_id": "",
                "helio_webhook_shared_token": "",
                "helio_network": "main",
                "helio_primary_payment_method": "fiat",
                "helio_default_amount": "10",
                "helio_currency_hint": "USDC",
            },
        )(),
    )
    assert helio.helio_is_configured() is False
    status = helio.helio_public_status()
    assert status.configured is False
    assert status.paylink_id is None


def test_helio_status_exposes_paylink_when_configured(monkeypatch):
    monkeypatch.setattr(
        "app.services.helio_commerce.get_settings",
        lambda: type(
            "S",
            (),
            {
                "helio_public_key": "pub",
                "helio_secret_key": "sec",
                "helio_paylink_id": "paylink-abc",
                "helio_webhook_shared_token": "tok",
                "helio_network": "main",
                "helio_primary_payment_method": "fiat",
                "helio_default_amount": "25",
                "helio_currency_hint": "USDC",
            },
        )(),
    )
    assert helio.helio_is_configured() is True
    status = helio.helio_public_status()
    assert status.paylink_id == "paylink-abc"
    assert status.default_amount == "25"
    assert status.webhook_secret_present is True


def test_verify_helio_webhook_signature(monkeypatch):
    token = "shared-token-example"
    body = json.dumps({"event": "CREATED", "transactionObject": {"id": "tx1"}}).encode("utf-8")
    sig = hmac.new(token.encode("utf-8"), body, hashlib.sha256).hexdigest()
    monkeypatch.setattr(
        "app.services.helio_commerce.get_settings",
        lambda: type("S", (), {"helio_webhook_shared_token": token})(),
    )
    assert helio.verify_helio_webhook_signature(body, sig) is True
    assert helio.verify_helio_webhook_signature(body, "deadbeef") is False
    assert helio.verify_helio_webhook_signature(body, None) is False


def test_summarize_helio_webhook():
    meta = helio.summarize_helio_webhook(
        {"event": "CREATED", "transactionObject": {"id": "tx9", "paylinkId": "pl1", "status": "SUCCESS"}}
    )
    assert meta["transaction_id"] == "tx9"
    assert meta["paylink_id"] == "pl1"


def test_webhook_log_tokens_cannot_inject_lines_or_terminal_controls(caplog):
    import logging
    malicious = "payment\r\nFORGED\t\x1b[31m\u2028" + "x" * 200
    with caplog.at_level(logging.INFO, logger=helio.__name__):
        helio.summarize_helio_webhook({"event": malicious,
            "transactionObject": {"id": malicious, "paylinkId": malicious, "status": malicious}})
    assert len(caplog.records) == 1
    message = caplog.records[0].getMessage()
    assert all(char not in message for char in "\r\n\t\x1b\u2028")
    assert len(helio._safe_log_token(malicious)) <= 64
