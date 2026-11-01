from __future__ import annotations

from uuid import uuid4

from app.config import get_settings


def _register_user(client, label: str):
    email = f"{label}_{uuid4().hex[:12]}@test.com"
    password = "password123"
    res = client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": label},
        headers={"Authorization": ""},
    )
    assert res.status_code in (200, 201), res.text
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    user = client.get("/v1/users/me", headers=headers).json()
    return user, headers


def test_commerce_plans_public(client):
    response = client.get("/v1/commerce/plans")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 4
    tiers = {item["tier"] for item in data["items"]}
    assert "merchant" in tiers
    assert "developer" in tiers


def test_ramp_waitlist_signup(client):
    response = client.post(
        "/v1/commerce/ramp-waitlist",
        json={"email": f"ramp_{uuid4().hex[:8]}@example.com", "interest": "stablecoin_topup", "region": "EU"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] in {"registered", "already_registered"}


def test_ramp_waitlist_physical_card_apple_pay(client):
    response = client.post(
        "/v1/commerce/ramp-waitlist",
        json={
            "email": f"cards_{uuid4().hex[:8]}@example.com",
            "interest": "physical_card_apple_pay",
            "region": "DE",
            "notes": "future licensed issuer interest",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] in {"registered", "already_registered"}
    assert "id" in body


def test_webid_status_public_fail_closed(client):
    response = client.get("/v1/commerce/webid/status")
    assert response.status_code == 200
    body = response.json()
    assert body["configured"] is False
    assert body["sessions_ready"] is False
    assert body["issues_cards"] is False
    assert body["apple_pay_ready"] is False
    assert body["role"] == "kyc_partner_slot"
    assert body["waitlist_interest"] == "physical_card_apple_pay"
    assert body["session_path"] == "/v1/commerce/webid/session"
    assert body["webhook_path"] == "/v1/commerce/webid/webhook"
    from urllib.parse import urlparse

    partner = urlparse(body["partner_url"])
    assert partner.scheme == "https" and partner.hostname == "webid-solutions.com"
    assert "client_secret" not in body
    assert "WEBID_CLIENT_SECRET" not in str(body)


def test_webid_session_fail_closed_without_credentials(client):
    _, headers = _register_user(client, "webid_session")
    response = client.post("/v1/commerce/webid/session", json={}, headers=headers)
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()


def test_webid_webhook_rejects_without_secret(client):
    response = client.post(
        "/v1/commerce/webid/webhook",
        content=b'{"event":"identification.completed","actionId":"1","status":"success"}',
        headers={"Content-Type": "application/json", "X-Signature": "deadbeef"},
    )
    assert response.status_code == 401


def test_stripe_adapter_status_public(client):
    response = client.get("/v1/payments/stripe/status", headers={"Authorization": ""})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["configured"] is False
    assert body["webhook_secret_present"] is False
    assert "USD" in body["currencies"]
    assert body["webhook_path"] == "/v1/webhooks/stripe"


def test_stripe_verification_readiness_requires_admin(client, monkeypatch):
    user, headers = _register_user(client, "stripe_admin_probe")
    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", user["id"])
    get_settings.cache_clear()
    try:
        denied = client.get("/v1/payments/stripe/verification-readiness")
        assert denied.status_code in {401, 403}

        ok = client.get("/v1/payments/stripe/verification-readiness", headers=headers)
        assert ok.status_code == 200
        payload = ok.json()
        assert "stripe_configured" in payload
        assert "closure_ready" in payload
        assert "runbook" in payload
    finally:
        monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "")
        get_settings.cache_clear()


def test_payment_link_qr_meta(client):
    _, headers = _register_user(client, "qr_merchant")
    create = client.post(
        "/v1/pay/payment-links",
        headers=headers,
        json={"title": "QR link", "amount": "3", "currency": "ACP"},
    )
    assert create.status_code == 201, create.text
    code = create.json()["code"]
    response = client.get(f"/v1/pay/{code}/qr")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == code
    assert data["qr_payload"]
    assert data["pay_url"]
