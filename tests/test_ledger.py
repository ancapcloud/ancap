"""Ledger: deposit, withdraw, balance, allocate, events."""
import uuid


from tests.conftest import unique_email, unique_name


def test_deposit_and_balance(client):
    pool = client.post(
        "/v1/pools",
        json={"name": unique_name("ledger_pool"), "risk_profile": "low"},
    )
    pool_id = pool.json()["id"]
    r = client.post(
        "/v1/ledger/deposit",
        json={
            "account_owner_type": "pool_treasury",
            "account_owner_id": pool_id,
            "amount": {"amount": "1000", "currency": "VUSD"},
        },
    )
    assert r.status_code == 201
    r2 = client.get(
        "/v1/ledger/balance",
        params={"owner_type": "pool_treasury", "owner_id": pool_id},
    )
    assert r2.status_code == 200
    balances = r2.json()["balances"]
    vusd = next((b for b in balances if b["currency"] == "VUSD"), None)
    assert vusd is not None
    assert float(vusd["amount"]) == 1000


def test_ledger_events(client):
    pool = client.post(
        "/v1/pools",
        json={"name": unique_name("ev_pool"), "risk_profile": "medium"},
    )
    pool_id = pool.json()["id"]
    client.post(
        "/v1/ledger/deposit",
        json={
            "account_owner_type": "pool_treasury",
            "account_owner_id": pool_id,
            "amount": {"amount": "500", "currency": "VUSD"},
        },
    )
    r = client.get("/v1/ledger/events", params={"limit": 10})
    assert r.status_code == 200
    assert "items" in r.json()


def test_allocate_blocks_unowned_pool_for_authenticated_user(client):
    """POST /v1/ledger/allocate rejects pools without owner_agent_id (fail-closed ownership)."""
    pool = client.post(
        "/v1/pools",
        json={"name": unique_name("alloc_pool"), "risk_profile": "high"},
    )
    assert pool.status_code == 201, pool.text
    pool_id = pool.json()["id"]
    deposit = client.post(
        "/v1/ledger/deposit",
        json={
            "account_owner_type": "pool_treasury",
            "account_owner_id": pool_id,
            "amount": {"amount": "250", "currency": "VUSD"},
        },
    )
    assert deposit.status_code == 201, deposit.text

    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("a"), "public_key": "p" * 32, "roles": ["seller"]},
    )
    vert = client.post(
        "/v1/verticals/propose",
        json={
            "name": unique_name("v"),
            "spec": {
                "allowed_actions": [{"name": "a", "args_schema": {}}],
                "required_resources": ["data_feed"],
                "metrics": [{"name": "m", "value_schema": {}}],
                "risk_spec": {},
            },
        },
    )
    vid = vert.json()["id"]
    client.post(f"/v1/verticals/{vid}/review", json={"decision": "approve"})
    strat = client.post(
        "/v1/strategies",
        json={
            "name": unique_name("s"),
            "vertical_id": vid,
            "owner_agent_id": agent.json()["id"],
        },
    )
    strat_id = strat.json()["id"]

    r = client.post(
        "/v1/ledger/allocate",
        json={
            "pool_id": pool_id,
            "strategy_id": strat_id,
            "amount": {"amount": "100", "currency": "VUSD"},
        },
    )
    assert r.status_code == 403, r.text
    assert "no owner" in (r.json().get("detail") or "").lower()


def test_allocate_requires_matching_pool_owner(client):
    email = unique_email()
    password = "password123"
    register = client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": "other_pool_owner"},
        headers={"Authorization": ""},
    )
    assert register.status_code in (200, 201), register.text
    login = client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
        headers={"Authorization": ""},
    )
    assert login.status_code == 200, login.text
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    owner_agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("owner"), "public_key": "o" * 32, "roles": ["seller"]},
        headers=other_headers,
    )
    assert owner_agent.status_code == 201, owner_agent.text
    pool = client.post(
        "/v1/pools",
        json={
            "name": unique_name("owned_alloc_pool"),
            "risk_profile": "high",
            "owner_agent_id": owner_agent.json()["id"],
        },
        headers=other_headers,
    )
    assert pool.status_code == 201, pool.text
    pool_id = pool.json()["id"]
    deposit = client.post(
        "/v1/ledger/deposit",
        json={
            "account_owner_type": "pool_treasury",
            "account_owner_id": pool_id,
            "amount": {"amount": "250", "currency": "VUSD"},
        },
        headers=other_headers,
    )
    assert deposit.status_code == 201, deposit.text

    other_agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("other"), "public_key": "q" * 32, "roles": ["seller"]},
    )
    vert = client.post(
        "/v1/verticals/propose",
        json={
            "name": unique_name("v2"),
            "spec": {
                "allowed_actions": [{"name": "a", "args_schema": {}}],
                "required_resources": ["data_feed"],
                "metrics": [{"name": "m", "value_schema": {}}],
                "risk_spec": {},
            },
        },
    )
    vid = vert.json()["id"]
    client.post(f"/v1/verticals/{vid}/review", json={"decision": "approve"})
    strat = client.post(
        "/v1/strategies",
        json={
            "name": unique_name("s2"),
            "vertical_id": vid,
            "owner_agent_id": other_agent.json()["id"],
        },
    )

    r = client.post(
        "/v1/ledger/allocate",
        json={
            "pool_id": pool_id,
            "strategy_id": strat.json()["id"],
            "amount": {"amount": "100", "currency": "VUSD"},
        },
    )
    assert r.status_code == 403, f"expected 403 for pool owned by another user, got {r.status_code}: {r.text}"


def test_allocate_pool_not_found(client):
    """POST /v1/ledger/allocate with non-existent pool_id returns 404."""
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("anf"), "public_key": "k" * 32, "roles": ["seller"]},
    )
    vert = client.post(
        "/v1/verticals/propose",
        json={
            "name": unique_name("vnf"),
            "spec": {
                "allowed_actions": [{"name": "a", "args_schema": {}}],
                "required_resources": [],
                "metrics": [{"name": "m", "value_schema": {}}],
                "risk_spec": {},
            },
        },
    )
    vid = vert.json()["id"]
    client.post(f"/v1/verticals/{vid}/review", json={"decision": "approve"})
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("snf"), "vertical_id": vid, "owner_agent_id": agent.json()["id"]},
    )
    r = client.post(
        "/v1/ledger/allocate",
        json={
            "pool_id": str(uuid.uuid4()),
            "strategy_id": strat.json()["id"],
            "amount": {"amount": "100", "currency": "VUSD"},
        },
    )
    assert r.status_code == 404
    assert "not found" in (r.json().get("detail") or "").lower()


def test_ledger_deposit_blocked_when_invariant_halted(client, db_cursor):
    """When tick has detected invariant violations, next deposit returns 503 (ROADMAP §3).

    The invariant check only applies to transfer events (deposits/withdraws are intentionally
    one-sided in MVP). We inject a malformed transfer event directly via SQL so that
    check_ledger_invariant sees a credit without a matching debit (sum != 0 for VUSD).
    Then tick sets ledger_invariant_halted=true and subsequent operations must be blocked.
    """
    pool = client.post(
        "/v1/pools",
        json={"name": unique_name("halt_pool"), "risk_profile": "low"},
    )
    pool_id = pool.json()["id"]

    # Get the pool's treasury account ID
    account_resp = client.get(
        "/v1/ledger/balance",
        params={"owner_type": "pool_treasury", "owner_id": pool_id},
    )
    assert account_resp.status_code == 200
    account_id = account_resp.json()["account_id"]
    assert account_id, "pool treasury account should exist after pool creation"

    # Inject a malformed transfer event: credit exists (dst_account_id set) but no
    # matching debit — this creates net != 0 for VUSD, triggering the invariant check.
    # src_account_id is deliberately NULL (one-sided credit), breaking double-entry.
    db_cursor.execute(
        f"INSERT INTO ledger_events (id, type, src_account_id, dst_account_id, "
        f"amount_currency, amount_value, ts, metadata) VALUES ("
        f"'{uuid.uuid4()}', 'transfer', NULL, '{account_id}', 'VUSD', "
        f"'500.000000000000000000', NOW(), '{{}}')"
    )
    db_cursor.execute("COMMIT")

    # tick should detect the violation and set halted=true
    r_tick = client.post("/v1/system/jobs/tick")
    assert r_tick.status_code == 200
    violations = r_tick.json().get("ledger_invariant_violations", [])
    assert violations, "tick should report VUSD invariant violation"
    assert any(v.get("currency") == "VUSD" for v in violations)
    # tick sets ledger_invariant_halted=true when violations exist (verified by the
    # halt flag being set internally in job_watermarks; subsequent ops will check it)

    # Next operation must be blocked (tick has set the halt flag)
    r = client.post(
        "/v1/ledger/deposit",
        json={
            "account_owner_type": "pool_treasury",
            "account_owner_id": pool_id,
            "amount": {"amount": "50", "currency": "VUSD"},
        },
    )
    assert r.status_code == 503, f"expected 503 when invariant halted, got {r.status_code}: {r.text}"
    assert "invariant" in (r.json().get("detail") or "").lower()
