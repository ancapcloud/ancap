"""Verticals: list, propose, get, review."""
import uuid
from tests.conftest import unique_name

VERTICAL_SPEC = {
    "allowed_actions": [
        {"name": "fetch", "args_schema": {"type": "object"}, "description": "Fetch data"},
    ],
    "required_resources": ["data_feed"],
    "metrics": [
        {"name": "pnl", "value_schema": {"type": "number"}, "description": "P&L"},
    ],
    "risk_spec": {},
}


def test_propose_vertical(client):
    r = client.post(
        "/v1/verticals/propose",
        json={"name": unique_name("vertical"), "spec": VERTICAL_SPEC},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "proposed"
    assert "id" in data


def test_list_verticals(client):
    r = client.get("/v1/verticals", params={"limit": 5})
    assert r.status_code == 200
    assert "items" in r.json()


def test_get_vertical_with_spec(client):
    create = client.post(
        "/v1/verticals/propose",
        json={"name": unique_name("v"), "spec": VERTICAL_SPEC},
    )
    vid = create.json()["id"]
    r = client.get(f"/v1/verticals/{vid}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == vid
    assert "spec" in data
    assert data["spec"]["allowed_actions"]


def test_review_vertical_approve(client, as_platform_admin):
    create = client.post(
        "/v1/verticals/propose",
        json={"name": unique_name("review"), "spec": VERTICAL_SPEC},
    )
    vid = create.json()["id"]
    r = client.post(f"/v1/verticals/{vid}/review", json={"decision": "approve"})
    assert r.status_code == 200
    assert r.json()["status"] == "active"


def test_review_vertical_reject(client, as_platform_admin):
    create = client.post(
        "/v1/verticals/propose",
        json={"name": unique_name("reject"), "spec": VERTICAL_SPEC},
    )
    vid = create.json()["id"]
    r = client.post(f"/v1/verticals/{vid}/review", json={"decision": "reject"})
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_get_vertical_not_found(client):
    """GET /v1/verticals/{id} with non-existent id returns 404."""
    r = client.get(f"/v1/verticals/{uuid.uuid4()}")
    assert r.status_code == 404
    assert "not found" in (r.json().get("detail") or "").lower()
