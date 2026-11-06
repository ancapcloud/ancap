"""Strategies: create, list, get, versions, publish version."""
import uuid
from tests.conftest import unique_name

import pytest

# Moderation routes used by these tests are platform-admin only.
pytestmark = pytest.mark.usefixtures("platform_admin")

VERTICAL_SPEC = {
    "allowed_actions": [{"name": "step", "args_schema": {"type": "object"}}],
    "required_resources": ["data_feed"],
    "metrics": [{"name": "m", "value_schema": {"type": "number"}}],
    "risk_spec": {},
}


def _agent_and_vertical(client):
    agent = client.post(
        "/v1/agents",
        json={
            "display_name": unique_name("strat_agent"),
            "public_key": "k" * 32,
            "roles": ["seller"],
        },
    )
    vert = client.post(
        "/v1/verticals/propose",
        json={"name": unique_name("strat_vert"), "spec": VERTICAL_SPEC},
    )
    vid = vert.json()["id"]
    client.post(f"/v1/verticals/{vid}/review", json={"decision": "approve"})
    return agent.json()["id"], vid


def test_create_strategy(client):
    agent_id, vertical_id = _agent_and_vertical(client)
    r = client.post(
        "/v1/strategies",
        json={
            "name": unique_name("strategy"),
            "vertical_id": vertical_id,
            "owner_agent_id": agent_id,
            "summary": "Test strategy",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "draft"
    assert data["owner_agent_id"] == agent_id


def test_list_and_get_strategy(client):
    agent_id, vertical_id = _agent_and_vertical(client)
    create = client.post(
        "/v1/strategies",
        json={
            "name": unique_name("list_s"),
            "vertical_id": vertical_id,
            "owner_agent_id": agent_id,
        },
    )
    sid = create.json()["id"]
    r = client.get("/v1/strategies", params={"limit": 5})
    assert r.status_code == 200
    assert any(s["id"] == sid for s in r.json()["items"])
    r2 = client.get(f"/v1/strategies/{sid}")
    assert r2.status_code == 200
    assert r2.json()["id"] == sid


def test_publish_version(client):
    agent_id, vertical_id = _agent_and_vertical(client)
    strat = client.post(
        "/v1/strategies",
        json={
            "name": unique_name("ver_s"),
            "vertical_id": vertical_id,
            "owner_agent_id": agent_id,
        },
    )
    sid = strat.json()["id"]
    r = client.post(
        f"/v1/strategies/{sid}/versions",
        json={
            "semver": "0.1.0",
            "workflow": {
                "vertical_id": vertical_id,
                "version": "1.0",
                "steps": [{"id": "s1", "action": "step", "args": {}}],
            },
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["semver"] == "0.1.0"
    assert data["strategy_id"] == sid


def test_get_strategy_version(client):
    agent_id, vertical_id = _agent_and_vertical(client)
    strat = client.post(
        "/v1/strategies",
        json={
            "name": unique_name("gv_s"),
            "vertical_id": vertical_id,
            "owner_agent_id": agent_id,
        },
    )
    sid = strat.json()["id"]
    ver = client.post(
        f"/v1/strategies/{sid}/versions",
        json={
            "semver": "1.0.0",
            "workflow": {
                "vertical_id": vertical_id,
                "version": "1.0",
                "steps": [{"id": "s1", "action": "step", "args": {}}],
            },
        },
    )
    vid = ver.json()["id"]
    r = client.get(f"/v1/strategy-versions/{vid}")
    assert r.status_code == 200
    assert r.json()["id"] == vid


def test_get_strategy_version_not_found(client):
    """GET /v1/strategy-versions/{id} with non-existent id returns 404."""
    r = client.get(f"/v1/strategy-versions/{uuid.uuid4()}")
    assert r.status_code == 404
    assert "not found" in (r.json().get("detail") or "").lower()
