from __future__ import annotations

from decimal import Decimal
from uuid import uuid4


from app.config import get_settings



def _register_user(client):
    email = f"payout_user_{uuid4().hex[:12]}@test.com"
    password = "password123"
    res = client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": "payout user"},
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
            "reference": "test-payout-funding",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()



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



def test_create_payout_request_holds_user_balance(client):
    user, headers = _register_user(client)
    _deposit_user_credits(client, user["id"], amount="25", currency="ACP", headers=headers)

    created = client.post(
        "/v1/payouts/request",
        json={
            "amount": {"amount": "10", "currency": "ACP"},
            "method": "acp_wallet",
            "destination": "ACP_TEST_DESTINATION_123",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    payload = created.json()
    assert payload["status"] == "pending"
    assert payload["method"] == "acp_wallet"
    assert Decimal(payload["amount"]["amount"]) == Decimal("10")
    assert payload["amount"]["currency"] == "ACP"
    assert _user_balance(client, user["id"], "ACP", headers=headers) == Decimal("15.000000000000000000")

    listed = client.get("/v1/payouts", headers=headers)
    assert listed.status_code == 200, listed.text
    items = listed.json()["items"]
    assert any(item["id"] == payload["id"] and item["status"] == "pending" for item in items)



def test_create_payout_request_rejects_insufficient_balance(client):
    user, headers = _register_user(client)
    _deposit_user_credits(client, user["id"], amount="5", currency="ACP", headers=headers)

    created = client.post(
        "/v1/payouts/request",
        json={
            "amount": {"amount": "10", "currency": "ACP"},
            "method": "acp_wallet",
            "destination": "ACP_TOO_HIGH_DESTINATION",
        },
        headers=headers,
    )
    assert created.status_code == 402, created.text
    assert created.json()["detail"] == "Insufficient balance"



def test_admin_can_approve_payout_request(client, monkeypatch):
    user, headers = _register_user(client)
    _deposit_user_credits(client, user["id"], amount="25", currency="ACP", headers=headers)
    created = client.post(
        "/v1/payouts/request",
        json={
            "amount": {"amount": "7", "currency": "ACP"},
            "method": "bsc_address",
            "destination": "0x1234567890abcdef1234567890abcdef12345678",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    payout = created.json()

    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", user["id"])
    get_settings.cache_clear()
    try:
        listed = client.get("/v1/admin/payouts?status=pending", headers=headers)
        assert listed.status_code == 200, listed.text
        assert any(item["id"] == payout["id"] for item in listed.json()["items"])

        approved = client.post(
            f"/v1/admin/payouts/{payout['id']}/approve",
            json={"admin_notes": "ready for off-platform transfer"},
            headers=headers,
        )
        assert approved.status_code == 200, approved.text
        approved_payload = approved.json()
        assert approved_payload["status"] == "approved"
        assert approved_payload["admin_notes"] == "ready for off-platform transfer"
        assert approved_payload["processed_at"] is not None
        assert _user_balance(client, user["id"], "ACP", headers=headers) == Decimal("18.000000000000000000")
    finally:
        monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "")
        get_settings.cache_clear()



def test_admin_can_reject_payout_request_and_refund_hold(client, monkeypatch):
    user, headers = _register_user(client)
    _deposit_user_credits(client, user["id"], amount="25", currency="ACP", headers=headers)
    created = client.post(
        "/v1/payouts/request",
        json={
            "amount": {"amount": "9", "currency": "ACP"},
            "method": "bank_transfer",
            "destination": "DE89 3704 0044 0532 0130 00",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    payout = created.json()
    assert _user_balance(client, user["id"], "ACP", headers=headers) == Decimal("16.000000000000000000")

    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", user["id"])
    get_settings.cache_clear()
    try:
        rejected = client.post(
            f"/v1/admin/payouts/{payout['id']}/reject",
            json={"admin_notes": "destination verification failed"},
            headers=headers,
        )
        assert rejected.status_code == 200, rejected.text
        rejected_payload = rejected.json()
        assert rejected_payload["status"] == "rejected"
        assert rejected_payload["admin_notes"] == "destination verification failed"
        assert rejected_payload["processed_at"] is not None
        assert _user_balance(client, user["id"], "ACP", headers=headers) == Decimal("25.000000000000000000")
    finally:
        monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "")
        get_settings.cache_clear()



def test_non_admin_cannot_list_or_approve_payouts(client):
    user, headers = _register_user(client)
    _deposit_user_credits(client, user["id"], amount="15", currency="ACP", headers=headers)
    created = client.post(
        "/v1/payouts/request",
        json={
            "amount": {"amount": "5", "currency": "ACP"},
            "method": "acp_wallet",
            "destination": "ACP_NON_ADMIN_DESTINATION",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    payout_id = created.json()["id"]

    listed = client.get("/v1/admin/payouts", headers=headers)
    assert listed.status_code in {403, 503}, listed.text

    approved = client.post(
        f"/v1/admin/payouts/{payout_id}/approve",
        json={"admin_notes": "should not work"},
        headers=headers,
    )
    assert approved.status_code in {403, 503}, approved.text



def test_duplicate_pending_payout_request_conflicts(client):
    user, headers = _register_user(client)
    _deposit_user_credits(client, user["id"], amount="25", currency="ACP", headers=headers)

    first = client.post(
        "/v1/payouts/request",
        json={
            "amount": {"amount": "5", "currency": "ACP"},
            "method": "acp_wallet",
            "destination": "ACP_DUPLICATE_DESTINATION",
        },
        headers=headers,
    )
    assert first.status_code == 201, first.text

    second = client.post(
        "/v1/payouts/request",
        json={
            "amount": {"amount": "5", "currency": "ACP"},
            "method": "acp_wallet",
            "destination": "ACP_DUPLICATE_DESTINATION",
        },
        headers=headers,
    )
    assert second.status_code == 409, second.text
    assert second.json()["detail"] == "Matching payout request is already in progress"



def test_create_payout_request_rejects_non_acp_currency(client):
    user, headers = _register_user(client)
    _deposit_user_credits(client, user["id"], amount="25", currency="ACP", headers=headers)

    created = client.post(
        "/v1/payouts/request",
        json={
            "amount": {"amount": "10", "currency": "USD"},
            "method": "bank_transfer",
            "destination": "DE89 3704 0044 0532 0130 00",
        },
        headers=headers,
    )
    assert created.status_code == 400, created.text
    assert created.json()["detail"] == "Payouts currently support ACP only"



def test_payout_status_filters_and_terminal_reprocessing_guards(client, monkeypatch):
    user, headers = _register_user(client)
    _deposit_user_credits(client, user["id"], amount="30", currency="ACP", headers=headers)

    pending = client.post(
        "/v1/payouts/request",
        json={
            "amount": {"amount": "5", "currency": "ACP"},
            "method": "acp_wallet",
            "destination": "ACP_PENDING_DESTINATION",
        },
        headers=headers,
    )
    assert pending.status_code == 201, pending.text
    pending_id = pending.json()["id"]

    to_reject = client.post(
        "/v1/payouts/request",
        json={
            "amount": {"amount": "6", "currency": "ACP"},
            "method": "bank_transfer",
            "destination": "DE89 3704 0044 0532 0130 00",
        },
        headers=headers,
    )
    assert to_reject.status_code == 201, to_reject.text
    rejected_id = to_reject.json()["id"]

    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", user["id"])
    get_settings.cache_clear()
    try:
        rejected = client.post(
            f"/v1/admin/payouts/{rejected_id}/reject",
            json={"admin_notes": "bank details mismatch"},
            headers=headers,
        )
        assert rejected.status_code == 200, rejected.text
        assert rejected.json()["status"] == "rejected"

        pending_items = client.get("/v1/payouts?status=pending", headers=headers)
        assert pending_items.status_code == 200, pending_items.text
        assert [item["id"] for item in pending_items.json()["items"]] == [pending_id]

        rejected_items = client.get("/v1/payouts?status=rejected", headers=headers)
        assert rejected_items.status_code == 200, rejected_items.text
        assert [item["id"] for item in rejected_items.json()["items"]] == [rejected_id]

        invalid_filter = client.get("/v1/payouts?status=wat", headers=headers)
        assert invalid_filter.status_code == 400, invalid_filter.text
        assert invalid_filter.json()["detail"] == "Unsupported payout status filter"

        reprocess = client.post(
            f"/v1/admin/payouts/{rejected_id}/approve",
            json={"admin_notes": "should stay terminal"},
            headers=headers,
        )
        assert reprocess.status_code == 409, reprocess.text
        assert reprocess.json()["detail"] == "Payout request is already rejected"
    finally:
        monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "")
        get_settings.cache_clear()
