from __future__ import annotations

import json
from decimal import Decimal
from uuid import uuid4

import pytest

from app.config import get_settings
from app.services import stripe_payments


@pytest.fixture(autouse=True)
def _stripe_env(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "stripe_secret_test_ancap")
    monkeypatch.setenv("STRIPE_PUBLISHABLE_KEY", "stripe_publishable_test_ancap")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "stripe_webhook_test_ancap")
    get_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()


def _register_user(client):
    email = f"stripe_user_{uuid4().hex[:12]}@test.com"
    password = "password123"
    res = client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": "stripe user"},
        headers={"Authorization": ""},
    )
    assert res.status_code in (200, 201), res.text
    token = res.json()["access_token"]
    user = client.get("/v1/users/me", headers={"Authorization": f"Bearer {token}"}).json()
    return user, {"Authorization": f"Bearer {token}"}


async def _fake_create_intent(session, user, body):
    from app.db.models import PaymentIntent, PaymentIntentStatusEnum
    from app.schemas import WorkflowCreditPackagePublic
    from app.schemas.common import Money

    suffix = uuid4().hex[:12]
    stripe_payment_intent_id = f"pi_test_{suffix}"
    intent = PaymentIntent(
        owner_user_id=user.id,
        workflow_run_id=None,
        intent_type="credit_topup",
        status=PaymentIntentStatusEnum.requires_payment.value,
        payment_method="stripe",
        amount_currency="USD",
        amount_value=Decimal("19.99"),
        payment_reference=f"stripe:{stripe_payment_intent_id}",
        stripe_payment_intent_id=stripe_payment_intent_id,
        provider_payload_json={"package_slug": body.package_slug, "mode": "stripe",
            "price": {"amount": "19.99", "currency": "USD"},
            "credit_amount": {"amount": "100", "currency": "ACP"}},
    )
    session.add(intent)
    await session.flush()
    await session.refresh(intent)
    package = WorkflowCreditPackagePublic(
        slug=body.package_slug,
        title="Launch Credits",
        description="Test package",
        price=Money(amount="19.99", currency="USD"),
        credit_amount=Money(amount="100", currency="ACP"),
        accepted_currencies=["USD"],
        bonus_percent=5,
        recommended_for=["tests"],
    )
    stripe = {
        "customer_id": "cus_test_123",
        "payment_intent_id": stripe_payment_intent_id,
        "client_secret": f"{stripe_payment_intent_id}_secret_456",
        "publishable_key": "stripe_publishable_test_ancap",
        "amount": {"amount": "19.99", "currency": "USD"},
        "currency": "USD",
        "payment_method_types": ["card"],
        "status": "requires_payment_method",
    }
    return intent, package, stripe_payments.StripeIntentSessionPublic.model_validate(stripe)


async def _fake_list_methods(session, user):
    return stripe_payments.PaymentMethodsResponse(
        items=[
            stripe_payments.PaymentMethodPublic(
                id="pm_card_visa",
                type="card",
                customer_id="cus_test_123",
                reusable=True,
                card=stripe_payments.PaymentMethodCardPublic(
                    brand="visa",
                    last4="4242",
                    exp_month=12,
                    exp_year=2030,
                    funding="credit",
                    country="US",
                ),
            )
        ]
    )


async def _fake_detach(_session, _user, payment_method_id):
    assert payment_method_id == "pm_card_visa"
    return None


def test_create_and_get_stripe_payment_intent_route(client, monkeypatch):
    _user, headers = _register_user(client)
    monkeypatch.setattr(stripe_payments, "create_stripe_credit_topup_intent", _fake_create_intent)

    async def _fake_fetch(stripe_payment_intent_id: str):
        return {
            "id": stripe_payment_intent_id,
            "status": "requires_payment_method",
            "payment_method_types": ["card"],
        }

    monkeypatch.setattr(stripe_payments, "fetch_stripe_payment_intent", _fake_fetch)

    response = client.post(
        "/v1/payments/stripe/intent",
        json={
            "package_slug": "launch-credits",
            "currency": "USD",
            "save_payment_method": True,
        },
        headers=headers,
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["item"]["intent_type"] == "credit_topup"
    assert payload["item"]["payment_method"] == "stripe"
    assert payload["item"]["payment_reference"].startswith("stripe:pi_test_")
    assert payload["package"]["slug"] == "launch-credits"
    assert payload["stripe"]["payment_intent_id"].startswith("pi_test_")
    assert payload["stripe"]["publishable_key"] == "stripe_publishable_test_ancap"

    fetched = client.get(f"/v1/payments/stripe/intents/{payload['item']['id']}", headers=headers)
    assert fetched.status_code == 200, fetched.text
    fetched_payload = fetched.json()
    assert fetched_payload["item"]["id"] == payload["item"]["id"]
    assert fetched_payload["item"]["status"] == payload["item"]["status"]
    assert fetched_payload["package"]["slug"] == "launch-credits"
    assert fetched_payload["credited"] is False


def test_list_and_delete_payment_methods(client, monkeypatch):
    _user, headers = _register_user(client)
    monkeypatch.setattr(stripe_payments, "list_stripe_payment_methods_for_user", _fake_list_methods)
    monkeypatch.setattr(stripe_payments, "detach_stripe_payment_method_for_user", _fake_detach)

    listed = client.get("/v1/payments/methods", headers=headers)
    assert listed.status_code == 200, listed.text
    payload = listed.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == "pm_card_visa"
    assert payload["items"][0]["card"]["last4"] == "4242"

    deleted = client.delete("/v1/payments/methods/pm_card_visa", headers=headers)
    assert deleted.status_code == 204, deleted.text


def test_create_stripe_payment_intent_is_idempotent(client, monkeypatch):
    _user, headers = _register_user(client)
    call_count = 0

    async def _counted_fake_create(session, user, body):
        nonlocal call_count
        call_count += 1
        return await _fake_create_intent(session, user, body)

    monkeypatch.setattr(stripe_payments, "create_stripe_credit_topup_intent", _counted_fake_create)
    headers_with_idempotency = {**headers, "Idempotency-Key": f"stripe-create-{uuid4().hex}"}
    body = {
        "package_slug": "launch-credits",
        "currency": "USD",
        "save_payment_method": True,
    }

    first = client.post("/v1/payments/stripe/intent", json=body, headers=headers_with_idempotency)
    assert first.status_code == 201, first.text

    second = client.post("/v1/payments/stripe/intent", json=body, headers=headers_with_idempotency)
    assert second.status_code == 200, second.text
    first_payload = first.json()
    second_payload = second.json()
    assert second_payload["item"]["id"] == first_payload["item"]["id"]
    assert second_payload["item"]["payment_reference"] == first_payload["item"]["payment_reference"]
    assert second_payload["package"] == first_payload["package"]
    assert second_payload["stripe"]["payment_intent_id"] == first_payload["stripe"]["payment_intent_id"]
    assert second_payload["stripe"]["client_secret"] == first_payload["stripe"]["client_secret"]
    assert call_count == 1


def test_stripe_webhook_captures_credit_topup_once(client, monkeypatch):
    user, headers = _register_user(client)
    monkeypatch.setattr(stripe_payments, "create_stripe_credit_topup_intent", _fake_create_intent)
    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", user["id"])
    get_settings.cache_clear()

    create_intent = client.post(
        "/v1/payments/stripe/intent",
        json={"package_slug": "launch-credits", "currency": "USD"},
        headers=headers,
    )
    assert create_intent.status_code == 201, create_intent.text
    payload = create_intent.json()
    payment_intent_id = payload["item"]["id"]
    stripe_payment_intent_id = payload["stripe"]["payment_intent_id"]

    event_id = f"evt_test_topup_succeeded_{uuid4().hex[:10]}"
    event = {
        "id": event_id,
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": stripe_payment_intent_id,
                "status": "succeeded",
            }
        },
    }
    raw = json.dumps(event, separators=(",", ":")).encode("utf-8")
    signature = stripe_payments.build_stripe_webhook_signature(raw, "stripe_webhook_test_ancap")

    webhook = client.post(
        "/v1/webhooks/stripe",
        data=raw,
        headers={"Stripe-Signature": signature, "Content-Type": "application/json"},
    )
    assert webhook.status_code == 200, webhook.text
    ack = webhook.json()
    assert ack == {
        "received": True,
        "duplicate": False,
        "processed": True,
        "event_id": event_id,
        "event_type": "payment_intent.succeeded",
    }

    topups = client.get("/v1/workflow-store/admin/top-up-intents?status=captured", headers=headers)
    assert topups.status_code == 200, topups.text
    captured = next(item for item in topups.json()["items"] if item["item"]["id"] == payment_intent_id)
    assert captured["credited"] is True
    assert captured["item"]["status"] == "captured"
    assert captured["item"]["capture_ledger_event_id"] is not None

    fetched = client.get(f"/v1/payments/stripe/intents/{payment_intent_id}", headers=headers)
    assert fetched.status_code == 200, fetched.text
    fetched_payload = fetched.json()
    assert fetched_payload["credited"] is True
    assert fetched_payload["item"]["provider_payload"]["stripe_status"] == "succeeded"
    assert fetched_payload["item"]["provider_payload"]["stripe_last_event_id"] == event_id
    assert fetched_payload["item"]["provider_payload"]["stripe_last_event_type"] == "payment_intent.succeeded"
    assert fetched_payload["item"]["provider_payload"]["stripe_last_event_at"]
    assert fetched_payload["item"]["provider_payload"]["confirm_note"] == "Stripe webhook payment confirmation"

    balance = client.get(f"/v1/ledger/balance?owner_type=user&owner_id={user['id']}", headers=headers)
    assert balance.status_code == 200, balance.text
    acp_balance = next(item for item in balance.json()["balances"] if item["currency"] == "ACP")
    assert Decimal(acp_balance["amount"]) == Decimal("100.000000000000000000")

    duplicate = client.post(
        "/v1/webhooks/stripe",
        data=raw,
        headers={"Stripe-Signature": signature, "Content-Type": "application/json"},
    )
    assert duplicate.status_code == 200, duplicate.text
    assert duplicate.json() == {
        "received": True,
        "duplicate": True,
        "processed": True,
        "event_id": event_id,
        "event_type": "payment_intent.succeeded",
    }

    balance_after_duplicate = client.get(f"/v1/ledger/balance?owner_type=user&owner_id={user['id']}", headers=headers)
    acp_balance_after_duplicate = next(item for item in balance_after_duplicate.json()["balances"] if item["currency"] == "ACP")
    assert Decimal(acp_balance_after_duplicate["amount"]) == Decimal("100.000000000000000000")


def test_stripe_intent_idempotency_key_reuse_with_different_payload_conflicts(client, monkeypatch):
    _user, headers = _register_user(client)
    monkeypatch.setattr(stripe_payments, "create_stripe_credit_topup_intent", _fake_create_intent)
    shared_headers = {**headers, "Idempotency-Key": f"stripe-reuse-{uuid4().hex}"}

    first = client.post(
        "/v1/payments/stripe/intent",
        json={"package_slug": "launch-credits", "currency": "USD"},
        headers=shared_headers,
    )
    assert first.status_code == 201, first.text

    second = client.post(
        "/v1/payments/stripe/intent",
        json={"package_slug": "growth-credits", "currency": "USD"},
        headers=shared_headers,
    )
    assert second.status_code == 409, second.text
    assert second.json()["detail"] == "Idempotency-Key reuse with different request payload"


def test_stripe_intent_fails_closed_without_config(client, monkeypatch):
    _user, headers = _register_user(client)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "")
    monkeypatch.setenv("STRIPE_PUBLISHABLE_KEY", "")
    get_settings.cache_clear()

    response = client.post(
        "/v1/payments/stripe/intent",
        json={"package_slug": "launch-credits", "currency": "USD"},
        headers=headers,
    )
    assert response.status_code == 503, response.text
    assert response.json()["detail"] == "Stripe payments are not configured"



def test_stripe_intent_rejects_saved_payment_method_from_another_customer(client, monkeypatch):
    _user, headers = _register_user(client)
    stripe_calls: list[tuple[str, str]] = []

    async def _fake_stripe_request(method: str, path: str, *, data=None, params=None):
        stripe_calls.append((method, path))
        if method == "POST" and path == "/customers":
            return {"id": "cus_owner_123"}
        if method == "GET" and path == "/payment_methods/pm_foreign_card":
            return {
                "id": "pm_foreign_card",
                "type": "card",
                "customer": "cus_other_999",
            }
        if method == "POST" and path == "/payment_intents":
            pytest.fail("Stripe PaymentIntent creation must not run for a foreign saved payment method")
        raise AssertionError(f"Unexpected Stripe request: {method} {path}")

    monkeypatch.setattr(stripe_payments, "_stripe_request", _fake_stripe_request)

    response = client.post(
        "/v1/payments/stripe/intent",
        json={
            "package_slug": "launch-credits",
            "currency": "USD",
            "payment_method_id": "pm_foreign_card",
            "save_payment_method": True,
        },
        headers=headers,
    )
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Payment method not found"
    assert ("POST", "/customers") in stripe_calls
    assert ("GET", "/payment_methods/pm_foreign_card") in stripe_calls
    assert ("POST", "/payment_intents") not in stripe_calls



def test_create_stripe_payment_intent_records_saved_method_selection_metadata(client, monkeypatch):
    user_payload, _headers = _register_user(client)
    stripe_calls: list[tuple[str, str, dict | None]] = []

    async def _fake_stripe_request(method: str, path: str, *, data=None, params=None):
        payload = dict(data) if isinstance(data, dict) else None
        stripe_calls.append((method, path, payload))
        if method == "POST" and path == "/customers":
            return {"id": "cus_owner_123"}
        if method == "GET" and path == "/payment_methods/pm_saved_123":
            return {
                "id": "pm_saved_123",
                "type": "card",
                "customer": "cus_owner_123",
            }
        if method == "POST" and path == "/payment_intents":
            assert payload is not None
            assert payload["payment_method"] == "pm_saved_123"
            assert payload["setup_future_usage"] == "off_session"
            assert payload["metadata[ancap_payment_method_selection]"] == "saved_method"
            assert payload["metadata[ancap_save_payment_method_requested]"] == "true"
            return {
                "id": "pi_saved_method_123",
                "client_secret": "pi_saved_method_123_secret_456",
                "status": "requires_payment_method",
                "payment_method_types": ["card"],
            }
        raise AssertionError(f"Unexpected Stripe request: {method} {path}")

    monkeypatch.setattr(stripe_payments, "_stripe_request", _fake_stripe_request)

    import asyncio
    from app.db.session import SessionLocal

    async def _run():
        async with SessionLocal() as session:
            user = await stripe_payments.get_user_or_404(session, user_payload["id"])
            body = stripe_payments.StripeIntentCreateRequest(
                package_slug="launch-credits",
                currency="USD",
                payment_method_id="pm_saved_123",
                save_payment_method=True,
                note="saved-card-test",
            )
            intent, _package, stripe = await stripe_payments.create_stripe_credit_topup_intent(session, user, body)
            assert stripe.payment_intent_id == "pi_saved_method_123"
            assert intent.provider_payload_json["payment_method_selection"] == "saved_method"
            assert intent.provider_payload_json["save_payment_method_requested"] is True
            assert intent.provider_payload_json["requested_payment_method_id"] == "pm_saved_123"
            assert intent.provider_payload_json["payment_method_id"] == "pm_saved_123"

    asyncio.run(_run())
    assert ("GET", "/payment_methods/pm_saved_123") in [(method, path) for method, path, _ in stripe_calls]
    assert ("POST", "/payment_intents") in [(method, path) for method, path, _ in stripe_calls]



def test_create_stripe_payment_intent_records_new_card_selection_metadata(client, monkeypatch):
    user_payload, _headers = _register_user(client)
    stripe_calls: list[tuple[str, str, dict | None]] = []

    async def _fake_stripe_request(method: str, path: str, *, data=None, params=None):
        payload = dict(data) if isinstance(data, dict) else None
        stripe_calls.append((method, path, payload))
        if method == "POST" and path == "/customers":
            return {"id": "cus_owner_456"}
        if method == "POST" and path == "/payment_intents":
            assert payload is not None
            assert "payment_method" not in payload
            assert payload["setup_future_usage"] == "off_session"
            assert payload["metadata[ancap_payment_method_selection]"] == "new_card"
            assert payload["metadata[ancap_save_payment_method_requested]"] == "true"
            return {
                "id": "pi_new_card_123",
                "client_secret": "pi_new_card_123_secret_456",
                "status": "requires_payment_method",
                "payment_method_types": ["card"],
            }
        raise AssertionError(f"Unexpected Stripe request: {method} {path}")

    monkeypatch.setattr(stripe_payments, "_stripe_request", _fake_stripe_request)

    import asyncio
    from app.db.session import SessionLocal

    async def _run():
        async with SessionLocal() as session:
            user = await stripe_payments.get_user_or_404(session, user_payload["id"])
            body = stripe_payments.StripeIntentCreateRequest(
                package_slug="launch-credits",
                currency="USD",
                save_payment_method=True,
                note="new-card-test",
            )
            intent, _package, stripe = await stripe_payments.create_stripe_credit_topup_intent(session, user, body)
            assert stripe.payment_intent_id == "pi_new_card_123"
            assert intent.provider_payload_json["payment_method_selection"] == "new_card"
            assert intent.provider_payload_json["save_payment_method_requested"] is True
            assert intent.provider_payload_json["requested_payment_method_id"] is None
            assert intent.provider_payload_json["payment_method_id"] is None

    asyncio.run(_run())
    assert ("POST", "/payment_intents") in [(method, path) for method, path, _ in stripe_calls]



def test_stripe_intent_rejects_unsupported_currency(client):
    _user, headers = _register_user(client)

    response = client.post(
        "/v1/payments/stripe/intent",
        json={"package_slug": "launch-credits", "currency": "GBP"},
        headers=headers,
    )
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Unsupported Stripe currency. Supported values: EUR, USD"



def test_stripe_webhook_requires_configured_secret(client, monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "")
    get_settings.cache_clear()
    raw = json.dumps(
        {
            "id": "evt_missing_secret",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_missing_secret", "status": "succeeded"}},
        },
        separators=(",", ":"),
    ).encode("utf-8")

    response = client.post(
        "/v1/webhooks/stripe",
        data=raw,
        headers={"Stripe-Signature": "t=1,v1=fake", "Content-Type": "application/json"},
    )
    assert response.status_code == 503, response.text
    assert response.json()["detail"] == "Stripe webhook secret is not configured"



def test_stripe_webhook_marks_terminal_failure_states(client, monkeypatch):
    _user, headers = _register_user(client)
    monkeypatch.setattr(stripe_payments, "create_stripe_credit_topup_intent", _fake_create_intent)

    created = client.post(
        "/v1/payments/stripe/intent",
        json={"package_slug": "launch-credits", "currency": "USD"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    created_payload = created.json()
    stripe_payment_intent_id = created_payload["stripe"]["payment_intent_id"]
    local_intent_id = created_payload["item"]["id"]

    def send_event(event_type: str, provider_status: str):
        event = {
            "id": f"evt_{event_type.replace('.', '_')}_{uuid4().hex[:10]}",
            "type": event_type,
            "data": {
                "object": {
                    "id": stripe_payment_intent_id,
                    "status": provider_status,
                }
            },
        }
        raw = json.dumps(event, separators=(",", ":")).encode("utf-8")
        signature = stripe_payments.build_stripe_webhook_signature(raw, "stripe_webhook_test_ancap")
        return client.post(
            "/v1/webhooks/stripe",
            data=raw,
            headers={"Stripe-Signature": signature, "Content-Type": "application/json"},
        )

    failed = send_event("payment_intent.payment_failed", "requires_payment_method")
    assert failed.status_code == 200, failed.text
    assert failed.json()["processed"] is True

    fetched_failed = client.get(f"/v1/payments/stripe/intents/{local_intent_id}", headers=headers)
    assert fetched_failed.status_code == 200, fetched_failed.text
    failed_payload = fetched_failed.json()
    assert failed_payload["item"]["status"] == "failed"
    assert failed_payload["credited"] is False
    assert failed_payload["item"]["provider_payload"]["stripe_last_event_type"] == "payment_intent.payment_failed"
    assert failed_payload["item"]["provider_payload"]["stripe_last_event_id"].startswith("evt_payment_intent_payment_failed_")
    assert failed_payload["item"]["provider_payload"]["stripe_last_event_at"]

    cancelled = send_event("payment_intent.canceled", "canceled")
    assert cancelled.status_code == 200, cancelled.text
    # Once the local intent is already terminal, later terminal updates are accepted but do not mutate state.
    assert cancelled.json()["processed"] is False

    fetched_cancelled = client.get(f"/v1/payments/stripe/intents/{local_intent_id}", headers=headers)
    assert fetched_cancelled.status_code == 200, fetched_cancelled.text
    assert fetched_cancelled.json()["item"]["status"] == "failed"
    assert fetched_cancelled.json()["credited"] is False


def test_stripe_poll_sync_captures_success_without_webhook(client, monkeypatch):
    user, headers = _register_user(client)
    monkeypatch.setattr(stripe_payments, "create_stripe_credit_topup_intent", _fake_create_intent)

    async def _fake_fetch(_stripe_payment_intent_id: str):
        return {
            "id": "pi_test_poll_success",
            "status": "succeeded",
            "payment_method": "pm_card_visa",
            "payment_method_types": ["card"],
        }

    created = client.post(
        "/v1/payments/stripe/intent",
        json={"package_slug": "launch-credits", "currency": "USD"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    created_payload = created.json()

    monkeypatch.setattr(stripe_payments, "fetch_stripe_payment_intent", _fake_fetch)
    fetched = client.get(f"/v1/payments/stripe/intents/{created_payload['item']['id']}", headers=headers)
    assert fetched.status_code == 200, fetched.text
    fetched_payload = fetched.json()
    assert fetched_payload["credited"] is True
    assert fetched_payload["item"]["status"] == "captured"
    assert fetched_payload["item"]["provider_payload"]["stripe_status"] == "succeeded"
    assert fetched_payload["item"]["provider_payload"]["payment_method_id"] == "pm_card_visa"
    assert fetched_payload["item"]["provider_payload"]["stripe_last_event_id"] == "stripe:poll"
    assert fetched_payload["item"]["provider_payload"]["stripe_last_event_type"] == "payment_intent.succeeded"
    assert fetched_payload["item"]["provider_payload"]["stripe_last_event_at"]
    assert fetched_payload["item"]["provider_payload"]["stripe_last_polled_at"]
    assert fetched_payload["item"]["provider_payload"]["confirm_note"] == "Stripe poll payment confirmation"

    balance = client.get(f"/v1/ledger/balance?owner_type=user&owner_id={user['id']}", headers=headers)
    assert balance.status_code == 200, balance.text
    acp_balance = next(item for item in balance.json()["balances"] if item["currency"] == "ACP")
    assert Decimal(acp_balance["amount"]) == Decimal("100.000000000000000000")



def test_stripe_poll_sync_marks_cancelled_without_webhook(client, monkeypatch):
    _user, headers = _register_user(client)
    monkeypatch.setattr(stripe_payments, "create_stripe_credit_topup_intent", _fake_create_intent)

    async def _fake_fetch(_stripe_payment_intent_id: str):
        return {
            "id": "pi_test_poll_cancelled",
            "status": "canceled",
            "payment_method_types": ["card"],
        }

    created = client.post(
        "/v1/payments/stripe/intent",
        json={"package_slug": "launch-credits", "currency": "USD"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    created_payload = created.json()

    monkeypatch.setattr(stripe_payments, "fetch_stripe_payment_intent", _fake_fetch)
    fetched = client.get(f"/v1/payments/stripe/intents/{created_payload['item']['id']}", headers=headers)
    assert fetched.status_code == 200, fetched.text
    fetched_payload = fetched.json()
    assert fetched_payload["credited"] is False
    assert fetched_payload["item"]["status"] == "cancelled"
    assert fetched_payload["item"]["provider_payload"]["stripe_status"] == "canceled"
    assert fetched_payload["item"]["provider_payload"]["stripe_last_event_id"] == "stripe:poll"
    assert fetched_payload["item"]["provider_payload"]["stripe_last_event_type"] == "payment_intent.canceled"
    assert fetched_payload["item"]["provider_payload"]["stripe_last_event_at"]
    assert fetched_payload["item"]["provider_payload"]["stripe_last_polled_at"]



def test_stripe_webhook_rejects_invalid_signature(client):
    event = {
        "id": "evt_bad_sig",
        "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_bad_sig", "status": "succeeded"}},
    }
    raw = json.dumps(event).encode("utf-8")
    valid_signature = stripe_payments.build_stripe_webhook_signature(raw, "stripe_webhook_test_ancap")
    invalid_signature = valid_signature.replace("v1=", "v1=deadbeef") if "v1=" in valid_signature else valid_signature + ",v1=deadbeef"

    response = client.post(
        "/v1/webhooks/stripe",
        data=raw,
        headers={"Stripe-Signature": invalid_signature, "Content-Type": "application/json"},
    )
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Invalid Stripe webhook signature"
