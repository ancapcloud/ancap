from decimal import Decimal
from uuid import uuid4

from app.config import get_settings


def create_captured_topup(client, monkeypatch):
    registered = client.post("/v1/auth/users", json={"email": f"snapshot_{uuid4().hex}@test.com", "password": "password123", "display_name": "Snapshot"}, headers={"Authorization": ""})
    assert registered.status_code in (200, 201), registered.text
    headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
    user = client.get("/v1/users/me", headers=headers).json()
    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", user["id"])
    get_settings.cache_clear()
    created = client.post("/v1/workflow-store/credit-packages/launch-credits/top-up-intents", json={"payment_currency": "ACP", "payment_method": "manual"}, headers=headers)
    assert created.status_code == 201, created.text
    payment_id = created.json()["item"]["id"]
    from app.api.routers import workflow_store
    monkeypatch.setattr(workflow_store, "find_credit_package", lambda slug: None)
    confirmed = client.post(f"/v1/workflow-store/admin/top-up-intents/{payment_id}/confirm", json={"payment_reference": f"snapshot-test-{uuid4()}"}, headers=headers)
    assert confirmed.status_code == 200, confirmed.text
    assert Decimal(confirmed.json()["package"]["credit_amount"]["amount"]) == Decimal("100")
    return payment_id, headers


def test_capture_and_refund_keep_order_terms_after_catalog_removal(client, monkeypatch):
    try:
        payment_id, headers = create_captured_topup(client, monkeypatch)
        refund = client.post("/v1/payments/refund-request", json={"payment_intent_id": payment_id, "reason": "Snapshot regression acceptance"}, headers=headers)
        assert refund.status_code == 201, refund.text
        assert Decimal(refund.json()["amount"]["amount"]) == Decimal("100")
        approved = client.post(f"/v1/admin/refund-requests/{refund.json()['id']}/approve", json={}, headers=headers)
        assert approved.status_code == 200, approved.text
        assert approved.json()["status"] == "approved"
    finally:
        get_settings.cache_clear()


def test_stripe_refund_cannot_be_marked_paid_by_ledger_only_approval(client, monkeypatch, db_cursor):
    try:
        payment_id, headers = create_captured_topup(client, monkeypatch)
        db_cursor.execute("UPDATE payment_intents SET payment_method='stripe' WHERE id=%s", (payment_id,))
        db_cursor.connection.commit()
        refund = client.post("/v1/payments/refund-request", json={"payment_intent_id": payment_id, "reason": "Provider confirmation required"}, headers=headers)
        assert refund.status_code == 201, refund.text
        denied = client.post(f"/v1/admin/refund-requests/{refund.json()['id']}/approve", json={}, headers=headers)
        assert denied.status_code == 409, denied.text
        db_cursor.execute("SELECT status, refund_ledger_event_id FROM payment_intents WHERE id=%s", (payment_id,))
        assert db_cursor.fetchone() == ("captured", None)
        pending = client.get("/v1/payments/my-refund-requests", headers=headers)
        assert pending.json()["items"][0]["status"] == "pending"
    finally:
        get_settings.cache_clear()
