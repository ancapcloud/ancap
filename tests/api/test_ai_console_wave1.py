from decimal import Decimal

from app.config import get_settings
from tests.conftest import unique_email, unique_name


def _register_and_login(client) -> str:
    email = unique_email()
    password = "password123"
    r = client.post("/auth/users", json={"email": email, "password": password, "display_name": "AI Console"})
    assert r.status_code in (201, 400), r.text
    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def _current_user(client, token: str) -> dict:
    response = client.get("/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text
    return response.json()


def _deposit_user_credits(client, token: str, amount: str = "20", currency: str = "ACP") -> dict:
    user = _current_user(client, token)
    response = client.post(
        "/v1/ledger/deposit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "account_owner_type": "user",
            "account_owner_id": user["id"],
            "amount": {"amount": amount, "currency": currency},
            "reference": "ai-console-referral-test",
        },
    )
    assert response.status_code == 201, response.text
    return user


def _user_balance(client, token: str, user_id: str, currency: str = "ACP") -> Decimal:
    response = client.get(
        f"/v1/ledger/balance?owner_type=user&owner_id={user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    for item in response.json()["balances"]:
        if item["currency"] == currency:
            return Decimal(item["amount"])
    return Decimal("0")


def _create_paid_workflow_run(client, token: str) -> dict:
    response = client.post(
        "/v1/workflow-store/runs",
        json={
            "workflow_slug": "token-risk-report",
            "payment_currency": "ACP",
            "unlock_full_result": True,
            "inputs": {
                "project_name": "AI Console Referral",
                "token_symbol": "AIC",
                "chain": "Base",
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_referral_summary_endpoint(client):
    owner_token = _register_and_login(client)
    referred_token = _register_and_login(client)

    code_resp = client.post("/referrals/codes/create", headers={"Authorization": f"Bearer {owner_token}"}, json={})
    assert code_resp.status_code == 201, code_resp.text
    code = code_resp.json()["code"]

    attr_resp = client.post(
        "/referrals/attribute",
        headers={"Authorization": f"Bearer {referred_token}"},
        json={"code": code},
    )
    assert attr_resp.status_code == 201, attr_resp.text

    summary = client.get("/referrals/me/summary", headers={"Authorization": f"Bearer {owner_token}"})
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["total_attributions"] >= 1
    assert {"pending", "eligible", "rewarded", "rejected"} & set(body.keys())


def test_referral_summary_reports_reward_totals_after_first_paid_workflow(client):
    owner_token = _register_and_login(client)
    referred_token = _register_and_login(client)

    code_resp = client.post("/referrals/codes/create", headers={"Authorization": f"Bearer {owner_token}"}, json={})
    assert code_resp.status_code == 201, code_resp.text
    code = code_resp.json()["code"]

    attr_resp = client.post(
        "/referrals/attribute",
        headers={"Authorization": f"Bearer {referred_token}"},
        json={"code": code, "source": "ai_console"},
    )
    assert attr_resp.status_code == 201, attr_resp.text

    owner_user = _current_user(client, owner_token)
    referred_user = _deposit_user_credits(client, referred_token)
    run = _create_paid_workflow_run(client, referred_token)
    run_id = run["id"]

    reserve = client.post(
        f"/v1/workflow-store/runs/{run_id}/payment-intents",
        json={"payment_method": "credits"},
        headers={"Authorization": f"Bearer {referred_token}"},
    )
    assert reserve.status_code == 201, reserve.text

    execute = client.post(
        f"/v1/workflow-store/runs/{run_id}/execute",
        headers={"Authorization": f"Bearer {referred_token}"},
    )
    assert execute.status_code == 200, execute.text
    assert execute.json()["item"]["receipt"]["proof"]["referral_rewards"]["status"] == "rewarded"

    summary = client.get("/referrals/me/summary", headers={"Authorization": f"Bearer {owner_token}"})
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["rewarded"] >= 1
    assert body["total_reward_events"] >= 1
    assert Decimal(body["total_reward_acp_amount"]) >= Decimal("25")
    assert Decimal(body["signup_bonus_acp_amount"]) >= Decimal("25")
    assert Decimal(body["commission_share_acp_amount"]) > Decimal("0")

    rewards = client.get("/referrals/me/rewards", headers={"Authorization": f"Bearer {owner_token}"})
    assert rewards.status_code == 200, rewards.text
    reward_payload = rewards.json()
    trigger_types = {item["trigger_type"] for item in reward_payload}
    assert {"referral_signup_bonus", "referral_commission_share"}.issubset(trigger_types)

    assert _user_balance(client, owner_token, owner_user["id"], "ACP") >= Decimal("25")
    assert _user_balance(client, referred_token, referred_user["id"], "ACP") == Decimal("5.000000000000000000")


def test_referral_rewards_enqueue_onchain_payout_jobs_when_runtime_enabled(client, db_cursor, monkeypatch):
    monkeypatch.setenv("REFERRAL_ONCHAIN_PAYOUT_ENABLED", "true")
    monkeypatch.setenv("REFERRAL_ONCHAIN_PAYOUT_KEYSTORE_FILE", "/run/secrets/referrals/operator.json")
    monkeypatch.setenv("REFERRAL_ONCHAIN_PAYOUT_FEE_ACP", "0.25")
    monkeypatch.setenv("ACP_RPC_URL", "http://acp-rpc.test")
    get_settings.cache_clear()
    try:
        owner_token = _register_and_login(client)
        referred_token = _register_and_login(client)

        code_resp = client.post("/referrals/codes/create", headers={"Authorization": f"Bearer {owner_token}"}, json={})
        assert code_resp.status_code == 201, code_resp.text
        code = code_resp.json()["code"]

        attr_resp = client.post(
            "/referrals/attribute",
            headers={"Authorization": f"Bearer {referred_token}"},
            json={"code": code, "source": "ai_console_onchain"},
        )
        assert attr_resp.status_code == 201, attr_resp.text

        owner_user = _current_user(client, owner_token)
        _deposit_user_credits(client, referred_token)
        run_id = _create_paid_workflow_run(client, referred_token)["id"]

        reserve = client.post(
            f"/v1/workflow-store/runs/{run_id}/payment-intents",
            json={"payment_method": "credits"},
            headers={"Authorization": f"Bearer {referred_token}"},
        )
        assert reserve.status_code == 201, reserve.text

        execute = client.post(
            f"/v1/workflow-store/runs/{run_id}/execute",
            headers={"Authorization": f"Bearer {referred_token}"},
        )
        assert execute.status_code == 200, execute.text

        db_cursor.execute(
            """
            SELECT rre.trigger_type, ropj.amount_value, ropj.status, ropj.to_address
            FROM referral_onchain_payout_jobs ropj
            JOIN referral_reward_events rre ON rre.id = ropj.reward_event_id
            WHERE rre.beneficiary_user_id = %s
            ORDER BY rre.trigger_type ASC
            """,
            (owner_user["id"],),
        )
        rows = db_cursor.fetchall()
        assert len(rows) == 2

        payout_by_trigger = {trigger: (Decimal(str(amount)), status, to_address) for trigger, amount, status, to_address in rows}
        assert payout_by_trigger["referral_commission_share"][0] == Decimal("1.50000000")
        assert payout_by_trigger["referral_signup_bonus"][0] == Decimal("25")
        assert all(status == "pending" for _, status, _ in payout_by_trigger.values())
        assert all(str(to_address).startswith("acp") for _, _, to_address in payout_by_trigger.values())
    finally:
        monkeypatch.setenv("REFERRAL_ONCHAIN_PAYOUT_ENABLED", "false")
        monkeypatch.setenv("REFERRAL_ONCHAIN_PAYOUT_KEYSTORE_FILE", "")
        monkeypatch.setenv("REFERRAL_ONCHAIN_PAYOUT_FEE_ACP", "")
        monkeypatch.setenv("ACP_RPC_URL", "")
        get_settings.cache_clear()


def test_system_jobs_tick_sends_referral_onchain_payout_jobs_when_runtime_enabled(client, db_cursor, monkeypatch):
    from app.services import referrals as referrals_service
    from unittest.mock import AsyncMock
    monkeypatch.setattr("app.services.acp_utxo_index.acp_utxo_index_tick", AsyncMock(return_value={"ok": True}))

    monkeypatch.setenv("REFERRAL_ONCHAIN_PAYOUT_ENABLED", "true")
    monkeypatch.setenv("REFERRAL_ONCHAIN_PAYOUT_KEYSTORE_FILE", "/run/secrets/referrals/operator.json")
    monkeypatch.setenv("REFERRAL_ONCHAIN_PAYOUT_FEE_ACP", "0.25")
    monkeypatch.setenv("ACP_RPC_URL", "http://acp-rpc.test")
    get_settings.cache_clear()

    walletd_calls: list[list[str]] = []

    def fake_run_walletd(args, timeout_s=180):
        walletd_calls.append(list(args))
        return {"accepted": True, "txid": f"ref-payout-{len(walletd_calls)}"}

    monkeypatch.setattr(referrals_service, "_run_walletd", fake_run_walletd)
    try:
        owner_token = _register_and_login(client)
        referred_token = _register_and_login(client)

        code_resp = client.post("/referrals/codes/create", headers={"Authorization": f"Bearer {owner_token}"}, json={})
        assert code_resp.status_code == 201, code_resp.text
        code = code_resp.json()["code"]

        attr_resp = client.post(
            "/referrals/attribute",
            headers={"Authorization": f"Bearer {referred_token}"},
            json={"code": code, "source": "ai_console_onchain_tick"},
        )
        assert attr_resp.status_code == 201, attr_resp.text

        owner_user = _current_user(client, owner_token)
        _deposit_user_credits(client, referred_token)
        run_id = _create_paid_workflow_run(client, referred_token)["id"]

        reserve = client.post(
            f"/v1/workflow-store/runs/{run_id}/payment-intents",
            json={"payment_method": "credits"},
            headers={"Authorization": f"Bearer {referred_token}"},
        )
        assert reserve.status_code == 201, reserve.text

        execute = client.post(
            f"/v1/workflow-store/runs/{run_id}/execute",
            headers={"Authorization": f"Bearer {referred_token}"},
        )
        assert execute.status_code == 200, execute.text

        tick = client.post("/v1/system/jobs/tick")
        assert tick.status_code == 200, tick.text
        payload = tick.json()["growth_referrals"]["onchain_payout_jobs"]
        assert payload["processed"] >= 2
        assert payload["sent"] >= 2
        assert payload["failed"] == 0
        assert len(walletd_calls) >= 2
        assert all(call[:6] == ["transfer", "--rpc", "http://acp-rpc.test", "--keystore-file", "/run/secrets/referrals/operator.json", "--to"] for call in walletd_calls)
        assert all("--fee-acp" in call and "0.25" in call for call in walletd_calls)

        db_cursor.execute(
            """
            SELECT status, txid, attempts
            FROM referral_onchain_payout_jobs ropj
            JOIN referral_reward_events rre ON rre.id = ropj.reward_event_id
            WHERE rre.beneficiary_user_id = %s
            ORDER BY ropj.created_at ASC
            """,
            (owner_user["id"],),
        )
        rows = db_cursor.fetchall()
        assert len(rows) == 2
        assert all(status == "sent" for status, _txid, _attempts in rows)
        assert all(str(txid).startswith("ref-payout-") for _status, txid, _attempts in rows)
        assert all(int(attempts) == 1 for _status, _txid, attempts in rows)
    finally:
        monkeypatch.setenv("REFERRAL_ONCHAIN_PAYOUT_ENABLED", "false")
        monkeypatch.setenv("REFERRAL_ONCHAIN_PAYOUT_KEYSTORE_FILE", "")
        monkeypatch.setenv("REFERRAL_ONCHAIN_PAYOUT_FEE_ACP", "")
        monkeypatch.setenv("ACP_RPC_URL", "")
        get_settings.cache_clear()


def test_system_graph_enforcement_preview_for_authenticated_user(client):
    token = _register_and_login(client)
    response = client.get(
        "/v1/system/graph-enforcement/preview?limit=5",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "enabled" in body
    assert "thresholds" in body
    assert isinstance(body["items"], list)


def test_decision_logs_written_for_listing_gate(client, base_vertical_id, monkeypatch):
    # This test specifically asserts the participation-gate denial path. The
    # global test environment has gates disabled to keep the rest of the suite
    # green, so re-enable them just for this test and clear the settings cache.
    from app.config import get_settings

    monkeypatch.setenv("PARTICIPATION_GATES_ENABLED", "true")
    get_settings.cache_clear()
    try:
        token = _register_and_login(client)
        agent_resp = client.post(
            "/agents",
            headers={"Authorization": f"Bearer {token}"},
            json={"display_name": unique_name("gate_agent"), "public_key": "x" * 32, "roles": ["seller"]},
        )
        assert agent_resp.status_code == 201, agent_resp.text
        agent_id = agent_resp.json()["id"]

        strategy_resp = client.post(
            "/strategies",
            json={"name": unique_name("gate_strategy"), "vertical_id": base_vertical_id, "owner_agent_id": agent_id},
        )
        assert strategy_resp.status_code == 201, strategy_resp.text
        strategy_id = strategy_resp.json()["id"]

        ver_resp = client.post(
            f"/strategies/{strategy_id}/versions",
            json={
                "semver": "1.0.0",
                "workflow": {
                    "vertical_id": base_vertical_id,
                    "version": "1.0",
                    "steps": [{"id": "s1", "action": "const", "args": {"value": 1}}],
                },
            },
        )
        assert ver_resp.status_code == 201, ver_resp.text
        version_id = ver_resp.json()["id"]

        listing_resp = client.post(
            "/listings",
            json={
                "strategy_id": strategy_id,
                "strategy_version_id": version_id,
                "fee_model": {"type": "one_time", "one_time_price": {"amount": "10", "currency": "USD"}},
                "status": "active",
            },
        )
        assert listing_resp.status_code == 403, listing_resp.text

        logs_resp = client.get("/v1/internal/ops/decision-logs?scope=listings.create&limit=20")
        assert logs_resp.status_code == 200, logs_resp.text
        logs = logs_resp.json()
        assert any(item["scope"] == "listings.create" for item in logs)
    finally:
        get_settings.cache_clear()
