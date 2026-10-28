from uuid import uuid4

from app.config import get_settings
from tests.conftest import unique_email, unique_name


def _register_and_login(client) -> str:
    email = unique_email()
    password = "password123"
    r = client.post("/v1/auth/users", json={"email": email, "password": password, "display_name": "Growth"})
    assert r.status_code in (201, 400), r.text
    login = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def _create_agent(client, token: str) -> str:
    r = client.post(
        "/v1/agents",
        headers={"Authorization": f"Bearer {token}"},
        json={"display_name": unique_name("growth_agent"), "public_key": "x" * 32, "roles": ["buyer"]},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_faucet_claim_idempotent_once(client):
    token = _register_and_login(client)
    agent_id = _create_agent(client, token)

    r1 = client.post(
        "/v1/onboarding/faucet/claim",
        headers={"Authorization": f"Bearer {token}"},
        json={"currency": "USD", "amount": "10", "agent_id": agent_id},
    )
    assert r1.status_code == 201, r1.text
    body1 = r1.json()
    assert body1["claim_status"] in ("granted", "held", "rejected")

    r2 = client.post(
        "/v1/onboarding/faucet/claim",
        headers={"Authorization": f"Bearer {token}"},
        json={"currency": "USD", "amount": "10", "agent_id": agent_id},
    )
    assert r2.status_code == 201, r2.text
    body2 = r2.json()
    assert body2["id"] == body1["id"]


def test_quickstart_bypasses_owner_tier_gate_for_onboarding_flow(client, monkeypatch):
    token = _register_and_login(client)
    agent_id = _create_agent(client, token)

    monkeypatch.setenv("PARTICIPATION_GATES_ENABLED", "true")
    get_settings.cache_clear()
    try:
        quick = client.post(
            "/v1/onboarding/quickstart/run",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": unique_name("idk_growth_qs")},
            json={"owner_agent_id": agent_id},
        )
        assert quick.status_code == 201, quick.text
        body = quick.json()
        assert body["id"]
        assert body["state"] in ("running", "succeeded", "queued", "failed")
    finally:
        monkeypatch.setenv("PARTICIPATION_GATES_ENABLED", "false")
        get_settings.cache_clear()


def test_referral_attribution_unique(client):
    token_owner = _register_and_login(client)
    token_referred = _register_and_login(client)

    rc = client.post(
        "/v1/referrals/codes/create",
        headers={"Authorization": f"Bearer {token_owner}"},
        json={},
    )
    assert rc.status_code == 201, rc.text
    code = rc.json()["code"]

    a1 = client.post(
        "/v1/referrals/attribute",
        headers={"Authorization": f"Bearer {token_referred}"},
        json={"code": code},
    )
    assert a1.status_code == 201, a1.text

    a2 = client.post(
        "/v1/referrals/attribute",
        headers={"Authorization": f"Bearer {token_referred}"},
        json={"code": code},
    )
    assert a2.status_code in (409, 400), a2.text


def test_social_follow_and_copy(client):
    token = _register_and_login(client)
    agent_id = _create_agent(client, token)

    # Need a vertical id; use list verticals and pick first.
    v = client.get("/v1/verticals?limit=1")
    assert v.status_code == 200, v.text
    vertical_id = (v.json().get("items") or [])[0]["id"]

    s = client.post("/v1/strategies", json={"name": unique_name("grow_s"), "vertical_id": vertical_id, "owner_agent_id": agent_id})
    assert s.status_code == 201, s.text
    strategy_id = s.json()["id"]
    ver = client.post(
        f"/v1/strategies/{strategy_id}/versions",
        json={"semver": "1.0.0", "workflow": {"vertical_id": vertical_id, "version": "1.0", "steps": [{"id": "s1", "action": "const", "args": {"value": 1}}]}},
    )
    assert ver.status_code == 201, ver.text

    f1 = client.post(
        "/v1/social/strategies/follow",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_id": strategy_id},
    )
    assert f1.status_code == 204, f1.text
    f2 = client.post(
        "/v1/social/strategies/follow",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_id": strategy_id},
    )
    assert f2.status_code in (204, 409), f2.text

    c = client.post(
        "/v1/social/strategies/copy",
        headers={"Authorization": f"Bearer {token}"},
        json={"source_strategy_id": strategy_id},
    )
    assert c.status_code == 201, c.text
    assert c.json()["id"] != strategy_id


def test_jobs_tick_sets_ledger_halt_blocks_faucet(client, db_cursor):
    token = _register_and_login(client)
    agent_id = _create_agent(client, token)

    user_me = client.get("/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert user_me.status_code == 200, user_me.text
    user_id = user_me.json()["id"]

    balance = client.get(
        "/v1/ledger/balance",
        headers={"Authorization": f"Bearer {token}"},
        params={"owner_type": "user", "owner_id": user_id},
    )
    assert balance.status_code == 200, balance.text
    account_id = balance.json()["account_id"]
    assert account_id

    malformed_transfer_id = str(uuid4())
    db_cursor.execute(
        """
        INSERT INTO ledger_events (
            id, ts, type, amount_currency, amount_value, src_account_id, dst_account_id, metadata
        )
        VALUES (
            %s, NOW(), 'transfer', 'USD', 1, NULL, %s, '{}'::jsonb
        )
        """,
        (malformed_transfer_id, account_id),
    )
    db_cursor.connection.commit()

    jt = client.post("/v1/system/jobs/tick")
    assert jt.status_code == 200, jt.text
    assert (jt.json().get("ledger_invariant_violations") or []) != []

    r = client.post(
        "/v1/onboarding/faucet/claim",
        headers={"Authorization": f"Bearer {token}"},
        json={"currency": "USD", "amount": "10", "agent_id": agent_id},
    )
    assert r.status_code == 503, r.text

