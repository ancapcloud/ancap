"""L2: Reviews and Disputes API."""
import uuid
from tests.conftest import unique_name


def test_create_review(client):
    """POST /v1/reviews creates a review."""
    agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("rev_agent"), "public_key": "r" * 32, "roles": ["seller"]},
    )
    r = client.post(
        "/v1/reviews",
        json={
            "reviewer_type": "agent",
            "reviewer_id": agent.json()["id"],
            "target_type": "agent",
            "target_id": str(uuid.uuid4()),
            "weight": 0.8,
            "text": "Good strategy",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["reviewer_type"] == "agent"
    assert data["target_type"] == "agent"
    assert float(data["weight"]) == 0.8
    assert data["text"] == "Good strategy"


def test_list_reviews(client):
    """GET /v1/reviews returns pagination."""
    r = client.get("/v1/reviews", params={"limit": 5})
    assert r.status_code == 200
    assert "items" in r.json()
    assert "next_cursor" in r.json()


def test_create_dispute(client):
    """POST /v1/disputes opens a dispute."""
    r = client.post(
        "/v1/disputes",
        json={"subject": "Refund not received", "evidence_refs": [{"type": "order", "id": "123"}]},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "open"
    assert data["subject"] == "Refund not received"
    assert data["evidence_refs"] is not None


def test_list_disputes(client):
    """GET /v1/disputes returns pagination."""
    r = client.get("/v1/disputes", params={"limit": 5})
    assert r.status_code == 200
    assert "items" in r.json()


def test_get_dispute_and_verdict(client, as_platform_admin):
    """GET /v1/disputes/{id} and POST verdict."""
    create = client.post("/v1/disputes", json={"subject": "Test dispute"})
    dispute_id = create.json()["id"]
    r = client.get(f"/v1/disputes/{dispute_id}")
    assert r.status_code == 200
    assert r.json()["status"] == "open"
    verdict_r = client.post(
        f"/v1/disputes/{dispute_id}/verdict",
        json={"verdict": "Resolved in favor of complainant", "status": "resolved"},
    )
    assert verdict_r.status_code == 200
    assert verdict_r.json()["status"] == "resolved"
    assert verdict_r.json()["verdict"] is not None


def test_dispute_not_found(client):
    """GET /v1/disputes/{id} returns 404 for non-existent."""
    r = client.get(f"/v1/disputes/{uuid.uuid4()}")
    assert r.status_code == 404
