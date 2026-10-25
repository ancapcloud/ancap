from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.config import get_settings


def _register_user(client):
    email = f"refund_user_{uuid4().hex[:12]}@test.com"
    password = "password123"
    res = client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": "refund user"},
        headers={"Authorization": ""},
    )
    assert res.status_code in (200, 201), res.text
    token = res.json()["access_token"]
    user = client.get("/v1/users/me", headers={"Authorization": f"Bearer {token}"}).json()
    return user, {"Authorization": f"Bearer {token}"}


def _deposit_user_credits(client, user_id: str, *, amount: str, currency: str, headers: dict[str, str]):
    response = client.post(
        "/v1/ledger/deposit",
        json={
            "account_owner_type": "user",
            "account_owner_id": user_id,
            "amount": {"amount": amount, "currency": currency},
            "reference": "test-refund-funding",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text


def _user_balance(client, user_id: str, currency: str, *, headers: dict[str, str]) -> Decimal:
    response = client.get(
        "/v1/ledger/balance",
        params={"owner_type": "user", "owner_id": user_id},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    for item in payload["balances"]:
        if item["currency"] == currency:
            return Decimal(item["amount"])
    return Decimal("0")


def _create_paid_workflow_intent(client, headers: dict[str, str], user_id: str) -> tuple[dict, dict]:
    run = client.post(
        "/v1/workflow-store/runs",
        json={
            "workflow_slug": "token-risk-report",
            "payment_currency": "ACP",
            "unlock_full_result": True,
            "inputs": {
                "project_name": "Refund Flow Test",
                "token_symbol": "RFD",
                "chain": "Base",
            },
        },
        headers=headers,
    )
    assert run.status_code == 201, run.text
    run_payload = run.json()

    reserve = client.post(
        f"/v1/workflow-store/runs/{run_payload['id']}/payment-intents",
        json={"payment_method": "credits", "note": "reserve for refund test"},
        headers=headers,
    )
    assert reserve.status_code == 201, reserve.text

    execute = client.post(f"/v1/workflow-store/runs/{run_payload['id']}/execute", headers=headers)
    assert execute.status_code == 200, execute.text
    executed_payload = execute.json()
    payment_intent_id = executed_payload["item"]["receipt"]["proof"]["payment_intent_id"]

    payment_intent = client.get(f"/v1/payments/stripe/intents/{payment_intent_id}", headers=headers)
    assert payment_intent.status_code == 404

    return run_payload, {
        "payment_intent_id": payment_intent_id,
        "run_id": run_payload["id"],
        "price": run_payload["price"],
    }


def _get_run(client, run_id: str, headers: dict[str, str]) -> dict:
    response = client.get(f"/v1/workflow-store/runs/{run_id}", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_user_can_create_refund_request_for_captured_workflow_payment(client, monkeypatch):
    user, headers = _register_user(client)
    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", user["id"])
    get_settings.cache_clear()
    try:
        _deposit_user_credits(client, user["id"], amount="20", currency="ACP", headers=headers)
        _run, payment = _create_paid_workflow_intent(client, headers, user["id"])

        refund = client.post(
            "/v1/payments/refund-request",
            json={
                "payment_intent_id": payment["payment_intent_id"],
                "reason": "Result did not match the requested scope.",
            },
            headers=headers,
        )
        assert refund.status_code == 201, refund.text
        payload = refund.json()
        assert payload["payment_intent_id"] == payment["payment_intent_id"]
        assert payload["user_id"] == user["id"]
        assert payload["status"] == "pending"
        assert payload["amount"]["currency"] == "ACP"
        assert Decimal(payload["amount"]["amount"]) == Decimal(payment["price"]["amount"])

        listed = client.get("/v1/payments/refund-requests?status=pending", headers=headers)
        assert listed.status_code == 200, listed.text
        assert any(item["id"] == payload["id"] for item in listed.json()["items"])
    finally:
        monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "")
        get_settings.cache_clear()


def test_admin_can_approve_refund_request_and_credit_user_back(client, monkeypatch):
    user, headers = _register_user(client)
    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", user["id"])
    get_settings.cache_clear()
    try:
        _deposit_user_credits(client, user["id"], amount="20", currency="ACP", headers=headers)
        run, payment = _create_paid_workflow_intent(client, headers, user["id"])
        assert _user_balance(client, user["id"], "ACP", headers=headers) == Decimal("5.000000000000000000")

        created = client.post(
            "/v1/payments/refund-request",
            json={
                "payment_intent_id": payment["payment_intent_id"],
                "reason": "Need to reverse this charged workflow.",
            },
            headers=headers,
        )
        assert created.status_code == 201, created.text
        refund_id = created.json()["id"]

        approved = client.post(
            f"/v1/admin/refund-requests/{refund_id}/approve",
            json={"admin_notes": "Approved after manual review"},
            headers=headers,
        )
        assert approved.status_code == 200, approved.text
        approved_payload = approved.json()
        assert approved_payload["status"] == "approved"
        assert approved_payload["admin_notes"] == "Approved after manual review"
        assert approved_payload["refund_ledger_event_id"] is not None
        assert approved_payload["processed_at"] is not None
        assert _user_balance(client, user["id"], "ACP", headers=headers) == Decimal("20.000000000000000000")

        run_payload = _get_run(client, run["id"], headers)
        assert run_payload["receipt"]["proof"]["payment_intent_status"] == "refunded"
        assert run_payload["receipt"]["proof"]["payment_intents"][-1]["status"] == "refunded"
    finally:
        monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "")
        get_settings.cache_clear()


def test_admin_can_reject_refund_request_without_crediting_balance(client, monkeypatch):
    user, headers = _register_user(client)
    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", user["id"])
    get_settings.cache_clear()
    try:
        _deposit_user_credits(client, user["id"], amount="20", currency="ACP", headers=headers)
        _run, payment = _create_paid_workflow_intent(client, headers, user["id"])
        before = _user_balance(client, user["id"], "ACP", headers=headers)

        created = client.post(
            "/v1/payments/refund-request",
            json={
                "payment_intent_id": payment["payment_intent_id"],
                "reason": "Requesting refund for review rejection path.",
            },
            headers=headers,
        )
        assert created.status_code == 201, created.text
        refund_id = created.json()["id"]

        rejected = client.post(
            f"/v1/admin/refund-requests/{refund_id}/reject",
            json={"admin_notes": "Evidence insufficient"},
            headers=headers,
        )
        assert rejected.status_code == 200, rejected.text
        rejected_payload = rejected.json()
        assert rejected_payload["status"] == "rejected"
        assert rejected_payload["admin_notes"] == "Evidence insufficient"
        assert _user_balance(client, user["id"], "ACP", headers=headers) == before
    finally:
        monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "")
        get_settings.cache_clear()


def test_refund_request_rejects_duplicate_pending_request(client, monkeypatch):
    user, headers = _register_user(client)
    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", user["id"])
    get_settings.cache_clear()
    try:
        _deposit_user_credits(client, user["id"], amount="20", currency="ACP", headers=headers)
        _run, payment = _create_paid_workflow_intent(client, headers, user["id"])

        first = client.post(
            "/v1/payments/refund-request",
            json={"payment_intent_id": payment["payment_intent_id"], "reason": "first request"},
            headers=headers,
        )
        assert first.status_code == 201, first.text

        second = client.post(
            "/v1/payments/refund-request",
            json={"payment_intent_id": payment["payment_intent_id"], "reason": "duplicate request"},
            headers=headers,
        )
        assert second.status_code == 409, second.text
        assert second.json()["detail"] == "Refund request is already pending for this payment intent"
    finally:
        monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "")
        get_settings.cache_clear()


def test_non_admin_cannot_list_or_process_refund_requests(client):
    user, headers = _register_user(client)
    _deposit_user_credits(client, user["id"], amount="20", currency="ACP", headers=headers)
    _run, payment = _create_paid_workflow_intent(client, headers, user["id"])

    created = client.post(
        "/v1/payments/refund-request",
        json={"payment_intent_id": payment["payment_intent_id"], "reason": "non-admin check"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    refund_id = created.json()["id"]

    my_list = client.get(
        "/v1/payments/my-refund-requests",
        params={"payment_intent_id": payment["payment_intent_id"]},
        headers=headers,
    )
    assert my_list.status_code == 200, my_list.text
    assert any(item["id"] == refund_id for item in my_list.json()["items"])

    listed = client.get("/v1/payments/refund-requests", headers=headers)
    assert listed.status_code in {403, 503}, listed.text

    approved = client.post(
        f"/v1/admin/refund-requests/{refund_id}/approve",
        json={"admin_notes": "should not work"},
        headers=headers,
    )
    assert approved.status_code in {403, 503}, approved.text


def test_refund_request_requires_captured_payment_intent(client):
    user, headers = _register_user(client)
    _deposit_user_credits(client, user["id"], amount="20", currency="ACP", headers=headers)

    run = client.post(
        "/v1/workflow-store/runs",
        json={
            "workflow_slug": "token-risk-report",
            "payment_currency": "ACP",
            "unlock_full_result": True,
            "inputs": {
                "project_name": "Refund Pending Test",
                "token_symbol": "PEND",
                "chain": "Base",
            },
        },
        headers=headers,
    )
    assert run.status_code == 201, run.text
    run_id = run.json()["id"]

    reserve = client.post(
        f"/v1/workflow-store/runs/{run_id}/payment-intents",
        json={"payment_method": "credits"},
        headers=headers,
    )
    assert reserve.status_code == 201, reserve.text
    intent_id = reserve.json()["item"]["id"]

    refund = client.post(
        "/v1/payments/refund-request",
        json={"payment_intent_id": intent_id, "reason": "too early"},
        headers=headers,
    )
    assert refund.status_code == 409, refund.text
    assert refund.json()["detail"] == "Refund requests require a captured payment intent"
