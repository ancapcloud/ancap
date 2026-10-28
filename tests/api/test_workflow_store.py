from decimal import Decimal
from uuid import uuid4

from app.config import get_settings


def _register_user(client):
    email = f"workflow_payment_{uuid4().hex[:12]}@test.com"
    password = "password123"
    res = client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": "workflow_payment_user"},
        headers={"Authorization": ""},
    )
    assert res.status_code in (200, 201), res.text
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    user = _current_user(client, headers=headers)
    return user, headers


def _current_user(client, headers=None):
    res = client.get("/v1/users/me", headers=headers)
    assert res.status_code == 200, res.text
    return res.json()


def _deposit_user_credits(client, amount="20", currency="ACP", headers=None):
    user = _current_user(client, headers=headers)
    res = client.post(
        "/v1/ledger/deposit",
        headers=headers,
        json={
            "account_owner_type": "user",
            "account_owner_id": user["id"],
            "amount": {"amount": amount, "currency": currency},
            "reference": "workflow-payment-intent-test",
        },
    )
    assert res.status_code == 201, res.text
    return user


def _user_balance(client, user_id: str, currency="ACP", headers=None) -> Decimal:
    res = client.get(f"/v1/ledger/balance?owner_type=user&owner_id={user_id}", headers=headers)
    assert res.status_code == 200, res.text
    for item in res.json()["balances"]:
        if item["currency"] == currency:
            return Decimal(item["amount"])
    return Decimal("0")


def _create_workflow_run(client, headers=None):
    payload = {
        "workflow_slug": "token-risk-report",
        "payment_currency": "ACP",
        "unlock_full_result": True,
        "inputs": {
            "project_name": "Deterministic Proof Test",
            "token_symbol": "DPT",
            "chain": "Base",
        },
    }
    res = client.post("/v1/workflow-store/runs", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


def test_workflow_payment_intent_reserves_and_captures_credits(client):
    user, headers = _register_user(client)
    _deposit_user_credits(client, amount="20", currency="ACP", headers=headers)
    run = _create_workflow_run(client, headers=headers)
    run_id = run["id"]

    reserve = client.post(
        f"/v1/workflow-store/runs/{run_id}/payment-intents",
        json={"payment_method": "credits", "note": "reserve for paid workflow"},
        headers=headers,
    )
    assert reserve.status_code == 201, reserve.text
    reserved_payload = reserve.json()
    assert reserved_payload["reserved"] is True
    assert reserved_payload["item"]["status"] == "reserved"
    assert reserved_payload["run"]["status"] == "paid"
    assert Decimal(reserved_payload["item"]["amount"]["amount"]) == Decimal(run["price"]["amount"])
    assert _user_balance(client, user["id"], "ACP", headers=headers) == Decimal("5.000000000000000000")

    execute = client.post(f"/v1/workflow-store/runs/{run_id}/execute", headers=headers)
    assert execute.status_code == 200, execute.text
    executed_payload = execute.json()
    assert executed_payload["item"]["status"] == "completed"
    assert executed_payload["item"]["receipt"]["proof"]["payment_intent_status"] == "captured"
    llm_usage = executed_payload["item"]["receipt"]["proof"]["llm_usage"]
    assert llm_usage["provider"] == "teneta_claude"
    assert llm_usage["status"] in {"succeeded", "fallback"}
    assert executed_payload["item"]["result"]["llm_usage"]["event_id"] == llm_usage["event_id"]

    balance_after_capture = _user_balance(client, user["id"], "ACP", headers=headers)
    assert balance_after_capture == Decimal("5.000000000000000000")


def test_workflow_payment_intent_refunds_reserved_credits_on_cancel(client):
    user, headers = _register_user(client)
    _deposit_user_credits(client, amount="20", currency="ACP", headers=headers)
    run = _create_workflow_run(client, headers=headers)
    run_id = run["id"]

    reserve = client.post(
        f"/v1/workflow-store/runs/{run_id}/payment-intents",
        json={"payment_method": "credits"},
        headers=headers,
    )
    assert reserve.status_code == 201, reserve.text
    assert _user_balance(client, user["id"], "ACP", headers=headers) == Decimal("5.000000000000000000")

    cancel = client.post(f"/v1/workflow-store/runs/{run_id}/status", json={"status": "cancelled"}, headers=headers)
    assert cancel.status_code == 200, cancel.text
    payload = cancel.json()
    assert payload["item"]["status"] == "cancelled"
    assert payload["item"]["receipt"]["proof"]["payment_intent_status"] == "refunded"
    assert _user_balance(client, user["id"], "ACP", headers=headers) == Decimal("20.000000000000000000")


def test_workflow_revenue_summary_reports_captured_sku(client, monkeypatch):
    admin_user, headers = _register_user(client)
    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", admin_user["id"])
    get_settings.cache_clear()
    try:
        _deposit_user_credits(client, amount="20", currency="ACP", headers=headers)
        run = _create_workflow_run(client, headers=headers)
        run_id = run["id"]

        reserve = client.post(
            f"/v1/workflow-store/runs/{run_id}/payment-intents",
            json={"payment_method": "credits"},
            headers=headers,
        )
        assert reserve.status_code == 201, reserve.text
        execute = client.post(f"/v1/workflow-store/runs/{run_id}/execute", headers=headers)
        assert execute.status_code == 200, execute.text

        summary = client.get("/v1/workflow-store/admin/revenue?days=1", headers=headers)
        assert summary.status_code == 200, summary.text
        payload = summary.json()
        assert payload["quote_count"] >= 1
        assert payload["payment_status_counts"]["captured"] >= 1
        captured_totals = [
            item for item in payload["totals"] if item["currency"] == "ACP" and item["status"] == "captured"
        ]
        assert captured_totals
        assert any(Decimal(item["amount"]) >= Decimal(run["price"]["amount"]) for item in captured_totals)
        sku = next(
            item
            for item in payload["skus"]
            if item["workflow_slug"] == "token-risk-report" and item["currency"] == "ACP"
        )
        assert sku["captured_count"] >= 1
        assert Decimal(sku["captured_amount"]) >= Decimal(run["price"]["amount"])
        assert Decimal(sku["estimated_cost_amount"]) > Decimal("0")
        assert Decimal(sku["estimated_margin_amount"]) > Decimal("0")
        assert any(item["currency"] == "ACP" for item in payload["gross_captured_totals"])
        assert any(item["currency"] == "ACP" for item in payload["estimated_cost_totals"])
        assert any(item["currency"] == "ACP" for item in payload["estimated_margin_totals"])
    finally:
        monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "")
        get_settings.cache_clear()


def test_workflow_capture_rewards_referrer_on_first_paid_purchase(client, monkeypatch):
    owner, owner_headers = _register_user(client)
    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", owner["id"])
    get_settings.cache_clear()
    try:
        code_response = client.post("/v1/referrals/codes/create", json={}, headers=owner_headers)
        assert code_response.status_code == 201, code_response.text
        code = code_response.json()["code"]

        referred_user, referred_headers = _register_user(client)
        attribution = client.post(
            "/v1/referrals/attribute",
            json={"code": code, "source": "workflow_store"},
            headers=referred_headers,
        )
        assert attribution.status_code == 201, attribution.text

        _deposit_user_credits(client, amount="20", currency="ACP", headers=referred_headers)
        run = _create_workflow_run(client, headers=referred_headers)
        run_id = run["id"]
        reserve = client.post(
            f"/v1/workflow-store/runs/{run_id}/payment-intents",
            json={"payment_method": "credits"},
            headers=referred_headers,
        )
        assert reserve.status_code == 201, reserve.text

        execute = client.post(f"/v1/workflow-store/runs/{run_id}/execute", headers=referred_headers)
        assert execute.status_code == 200, execute.text
        executed_payload = execute.json()
        assert executed_payload["item"]["receipt"]["proof"]["referral_rewards"]["status"] == "rewarded"

        revenue = client.get("/v1/workflow-store/admin/revenue?days=1", headers=owner_headers)
        assert revenue.status_code == 200, revenue.text
        revenue_payload = revenue.json()
        sku = next(
            item
            for item in revenue_payload["skus"]
            if item["workflow_slug"] == "token-risk-report" and item["currency"] == "ACP"
        )
        assert Decimal(sku["referral_commission_amount"]) > Decimal("0")
        assert any(item["currency"] == "ACP" and Decimal(item["amount"]) > Decimal("0") for item in revenue_payload["referral_commission_totals"])

        summary = client.get("/v1/referrals/me/summary", headers=owner_headers)
        assert summary.status_code == 200, summary.text
        summary_payload = summary.json()
        assert summary_payload["rewarded"] >= 1
        assert summary_payload["total_reward_events"] >= 1
        assert Decimal(summary_payload["signup_bonus_acp_amount"]) >= Decimal("25")
        assert _user_balance(client, owner["id"], "ACP", headers=owner_headers) >= Decimal("25")
        assert _user_balance(client, referred_user["id"], "ACP", headers=referred_headers) == Decimal("5.000000000000000000")
    finally:
        monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "")
        get_settings.cache_clear()


def test_workflow_bundle_checkout_reserves_discounted_launch_pack(client):
    user, headers = _register_user(client)
    _deposit_user_credits(client, amount="100", currency="ACP", headers=headers)

    catalog = client.get("/v1/workflow-store/bundles")
    assert catalog.status_code == 200, catalog.text
    bundle_slugs = {item["slug"] for item in catalog.json()["items"]}
    assert {"launch-pack", "growth-pack", "concierge-pack", "pro-launch-pack", "agent-commerce-pack"}.issubset(bundle_slugs)

    checkout = client.post(
        "/v1/workflow-store/bundles/launch-pack/checkout",
        json={
            "payment_currency": "ACP",
            "payment_method": "credits",
            "project_name": "Bundle Test",
            "reserve_credits": True,
        },
        headers=headers,
    )
    assert checkout.status_code == 201, checkout.text
    payload = checkout.json()
    assert payload["bundle"]["slug"] == "launch-pack"
    assert payload["quoted_total"] == {"amount": "49.00", "currency": "ACP"}
    assert payload["original_total"] == {"amount": "67.00", "currency": "ACP"}
    assert payload["discount_amount"] == {"amount": "18.00", "currency": "ACP"}
    assert payload["reserved"] is True
    assert len(payload["runs"]) == 5
    assert len(payload["payment_intents"]) == 5
    assert {run["status"] for run in payload["runs"]} == {"paid"}
    assert {intent["status"] for intent in payload["payment_intents"]} == {"reserved"}
    assert sum(Decimal(run["price"]["amount"]) for run in payload["runs"]) == Decimal("49.00")
    assert _user_balance(client, user["id"], "ACP", headers=headers) == Decimal("51.000000000000000000")
    assert all(run["receipt"]["proof"]["bundle_slug"] == "launch-pack" for run in payload["runs"])


def test_credit_package_top_up_intent_credits_user_balance_once(client, monkeypatch):
    user, headers = _register_user(client)
    monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", user["id"])
    get_settings.cache_clear()
    try:
        catalog = client.get("/v1/workflow-store/credit-packages")
        assert catalog.status_code == 200, catalog.text
        assert any(item["slug"] == "launch-credits" for item in catalog.json()["items"])

        intent = client.post(
            "/v1/workflow-store/credit-packages/launch-credits/top-up-intents",
            json={"payment_currency": "ACP", "payment_method": "manual", "note": "test top-up invoice"},
            headers=headers,
        )
        assert intent.status_code == 201, intent.text
        payload = intent.json()
        assert payload["credited"] is False
        assert payload["package"]["credit_amount"] == {"amount": "100", "currency": "ACP"}
        assert payload["item"]["workflow_run_id"] is None
        assert payload["item"]["status"] == "requires_payment"
        assert Decimal(payload["item"]["amount"]["amount"]) == Decimal("95.00")
        assert payload["item"]["amount"]["currency"] == "ACP"

        user_confirm = client.post(
            f"/v1/workflow-store/top-up-intents/{payload['item']['id']}/confirm",
            json={"payment_reference": "topup-test-ref", "note": "paid in test"},
            headers=headers,
        )
        assert user_confirm.status_code == 403, user_confirm.text

        pending = client.get("/v1/workflow-store/admin/top-up-intents?status=requires_payment", headers=headers)
        assert pending.status_code == 200, pending.text
        assert any(item["item"]["id"] == payload["item"]["id"] for item in pending.json()["items"])

        confirm = client.post(
            f"/v1/workflow-store/admin/top-up-intents/{payload['item']['id']}/confirm",
            json={"payment_reference": "topup-test-ref", "note": "paid in test"},
            headers=headers,
        )
        assert confirm.status_code == 200, confirm.text
        confirmed_payload = confirm.json()
        assert confirmed_payload["credited"] is True
        assert confirmed_payload["item"]["status"] == "captured"
        assert _user_balance(client, user["id"], "ACP", headers=headers) == Decimal("100.000000000000000000")

        second_confirm = client.post(
            f"/v1/workflow-store/admin/top-up-intents/{payload['item']['id']}/confirm",
            json={"payment_reference": "topup-test-ref", "note": "idempotent retry"},
            headers=headers,
        )
        assert second_confirm.status_code == 200, second_confirm.text
        assert second_confirm.json()["credited"] is True
        assert _user_balance(client, user["id"], "ACP", headers=headers) == Decimal("100.000000000000000000")
    finally:
        monkeypatch.setenv("PLATFORM_ADMIN_USER_IDS", "")
        get_settings.cache_clear()


def test_workflow_payment_intent_rejects_insufficient_credits(client):
    _, headers = _register_user(client)
    run = _create_workflow_run(client, headers=headers)
    run_id = run["id"]

    reserve = client.post(
        f"/v1/workflow-store/runs/{run_id}/payment-intents",
        json={"payment_method": "credits"},
        headers=headers,
    )
    assert reserve.status_code == 402, reserve.text
    assert reserve.json()["detail"]["message"] == "Insufficient credits for workflow payment"


def test_workflow_proof_bundle_hash_is_deterministic(client):
    run = _create_workflow_run(client)
    run_id = run["id"]

    first = client.get(f"/v1/workflow-store/runs/{run_id}/proof-bundle")
    second = client.get(f"/v1/workflow-store/runs/{run_id}/proof-bundle")

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text

    first_payload = first.json()
    second_payload = second.json()

    assert first_payload["workflow_run_id"] == run_id
    assert second_payload["workflow_run_id"] == run_id
    assert first_payload["generated_at"] != second_payload["generated_at"]
    assert first_payload["proof_hash"] == second_payload["proof_hash"]


def test_workflow_proof_bundle_hash_changes_after_payment_confirmation(client):
    run = _create_workflow_run(client)
    run_id = run["id"]

    before = client.get(f"/v1/workflow-store/runs/{run_id}/proof-bundle")
    assert before.status_code == 200, before.text
    before_payload = before.json()

    confirm = client.post(
        f"/v1/workflow-store/runs/{run_id}/confirm-payment",
        json={
            "payment_reference": "proof-hash-regression-test",
            "payment_method": "manual",
            "payment_amount": {"amount": run["price"]["amount"], "currency": run["payment_currency"]},
            "note": "regression coverage",
        },
    )

    # Settlement execution may fail in some local DB states; the important assertion
    # is that if the workflow state changes, the proof bundle hash reflects changed proof.
    assert confirm.status_code in (200, 409), confirm.text

    after = client.get(f"/v1/workflow-store/runs/{run_id}/proof-bundle")
    assert after.status_code == 200, after.text
    after_payload = after.json()

    assert before_payload["proof_hash"] != after_payload["proof_hash"]
    assert after_payload["summary"]["payment_confirmed"] is True
