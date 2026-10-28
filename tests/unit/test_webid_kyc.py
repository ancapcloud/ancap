"""WebID KYC partner-slot unit tests (no live API calls)."""
from __future__ import annotations

from app.services import webid_kyc as webid


def test_webid_status_fail_closed_by_default(monkeypatch):
    monkeypatch.setattr(
        "app.services.webid_kyc.get_settings",
        type(
            "S",
            (),
            {
                "webid_enabled": False,
                "webid_api_base": "",
                "webid_client_id": "",
                "webid_client_secret": "",
            },
        ),
    )
    assert webid.webid_is_configured() is False
    status = webid.webid_public_status()
    assert status.configured is False
    assert status.enabled is False
    assert status.issues_cards is False
    assert status.apple_pay_ready is False
    assert status.role == "kyc_partner_slot"
    assert status.waitlist_interest == "physical_card_apple_pay"


def test_webid_enabled_still_fail_closed_without_credentials(monkeypatch):
    monkeypatch.setattr(
        "app.services.webid_kyc.get_settings",
        type(
            "S",
            (),
            {
                "webid_enabled": True,
                "webid_api_base": "https://example.invalid",
                "webid_client_id": "",
                "webid_client_secret": "",
            },
        ),
    )
    assert webid.webid_is_configured() is False
    status = webid.webid_public_status()
    assert status.enabled is True
    assert status.configured is False
    assert status.issues_cards is False
