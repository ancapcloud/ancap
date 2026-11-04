"""Risk API: limits, kill, status."""
import uuid
from tests.conftest import unique_name


def test_set_risk_limits(client, as_platform_admin):
    """POST /v1/risk/limits sets policy for a scope."""
    pool = client.post(
        "/v1/pools",
        json={"name": unique_name("risk_pool"), "risk_profile": "low"},
    )
    pool_id = pool.json()["id"]
    r = client.post(
        "/v1/risk/limits",
        json={
            "scope_type": "pool",
            "scope_id": pool_id,
            "policy_json": {"max_steps": 100, "max_loss_pct": 0.1},
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["scope_type"] == "pool"
    assert data["scope_id"] == pool_id


def test_risk_kill(client, as_platform_admin):
    """POST /v1/risk/kill sets circuit breaker to halted."""
    pool = client.post(
        "/v1/pools",
        json={"name": unique_name("kill_pool"), "risk_profile": "medium"},
    )
    r = client.post(
        "/v1/risk/kill",
        json={"scope_type": "pool", "scope_id": pool.json()["id"]},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["state"] == "halted"


def test_risk_status_run_not_found(client):
    """GET /v1/risk/status/{run_id} returns 404 for non-existent run."""
    r = client.get(f"/v1/risk/status/{uuid.uuid4()}")
    assert r.status_code == 404


def test_risk_status_success(client, base_vertical_id):
    """GET /v1/risk/status/{run_id} returns state and killed_by_risk."""
    from tests.test_runs import BASE_WORKFLOW
    vid = base_vertical_id
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("rs"), "public_key": "r" * 32, "roles": ["seller"]},
    )
    workflow = {**BASE_WORKFLOW, "vertical_id": vid}
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("rs_s"), "vertical_id": vid, "owner_agent_id": agent.json()["id"]},
    )
    ver = client.post(
        f"/v1/strategies/{strat.json()['id']}/versions",
        json={"semver": "0.1.0", "workflow": workflow},
    )
    pool = client.post("/v1/pools", json={"name": unique_name("rs_p"), "risk_profile": "low"})
    run_r = client.post(
        "/v1/runs",
        json={"strategy_version_id": ver.json()["id"], "pool_id": pool.json()["id"]},
        headers={"Idempotency-Key": unique_name("idk_risk_run")},
    )
    run_id = run_r.json()["id"]
    r = client.get(f"/v1/risk/status/{run_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["run_id"] == run_id
    assert data["state"] == "succeeded"
    assert "killed_by_risk" in data
    assert data["killed_by_risk"] is False
