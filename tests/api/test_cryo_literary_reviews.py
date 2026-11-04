"""Cryo desk + literary auction + service/AI reviews."""

from tests.api.test_organizations import _register_and_login


import pytest

# Moderation routes used by these tests are platform-admin only.
pytestmark = pytest.mark.usefixtures("platform_admin")

def test_cryo_catalog(client):
    r = client.get("/v1/cryo/catalog")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "tardigrade" in body["compliance_note"].lower() or "тихоход" in body["compliance_note"].lower()
    assert len(body["services"]) >= 5
    ids = {s["id"] for s in body["services"]}
    assert "cryo-vet-feline-tissue" in ids
    assert "cryo-vet-canine-regen" in ids
    blob = str(body).lower()
    assert "return to life" not in blob
    assert "98%" not in blob
    names = {p["name"].lower() for p in body["partners"]}
    assert any("kriorus" in n or "криорус" in n for n in names)
    assert any("tomorrow" in n for n in names)
    assert all(p.get("clinical_endorsement") is False for p in body["partners"])
    assert all(p.get("ethics_note") for p in body["partners"])
    assert "rwa" in body["compliance_note"].lower() or "yield" in body["compliance_note"].lower()


def test_literary_auction_catalog_and_bid(client):
    catalog = client.get("/v1/literary-auction/catalog")
    assert catalog.status_code == 200, catalog.text
    body = catalog.json()
    assert body["currency"] == "ACP"
    assert len(body["lots"]) >= 3
    lot_id = body["lots"][0]["id"]
    min_next = body["lots"][0]["min_next_acp"]

    _, headers, _ = _register_and_login(client, "Lit Bidder")
    bid = client.post(
        f"/v1/literary-auction/lots/{lot_id}/bids",
        headers=headers,
        json={"amount_acp": min_next},
    )
    assert bid.status_code == 201, bid.text
    data = bid.json()
    assert data["status"] == "winning"
    assert data["tx_hash"]


def test_literary_auction_rejects_pump_over_genre_comparable(client):
    catalog = client.get("/v1/literary-auction/catalog")
    assert catalog.status_code == 200, catalog.text
    body = catalog.json()
    integrity = body["price_integrity"]
    assert integrity["max_start_multiple"] == "12"
    assert integrity["max_genre_comp_multiple"] == "4"
    lot = next(item for item in body["lots"] if item["id"] == "lit-ancap-genesis")
    assert lot["genre_median_acp"]
    assert lot["speculation_flag"] in ("none", "elevated", "blocked")

    _, headers, _ = _register_and_login(client, "Lit Pumper")
    median = float(lot["genre_median_acp"])
    too_high = str(int(median * 4) + 1)
    bid = client.post(
        f"/v1/literary-auction/lots/{lot['id']}/bids",
        headers=headers,
        json={"amount_acp": too_high},
    )
    assert bid.status_code == 400, bid.text
    assert "comparable" in bid.json()["detail"].lower() or "median" in bid.json()["detail"].lower()


def test_service_and_ai_reviews(client):
    target = "a1000001-0000-4000-8000-000000000003"  # cryo-tardigrade-protocol
    user, headers, _ = _register_and_login(client, "Reviewer")
    user_id = user["id"]

    created = client.post(
        "/v1/reviews",
        json={
            "reviewer_type": "user",
            "reviewer_id": user_id,
            "target_type": "service",
            "target_id": target,
            "rating": 5,
            "text": "Clear partner handoff and compliance note.",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    assert created.json()["rating"] == 5

    ai = client.post(
        "/v1/reviews/ai",
        json={"target_type": "service", "target_id": target, "rating": 4, "focus": "cryo desk"},
    )
    assert ai.status_code == 201, ai.text
    assert ai.json()["reviewer_type"] == "ai"

    listed = client.get(f"/v1/reviews?target_type=service&target_id={target}")
    assert listed.status_code == 200, listed.text
    items = listed.json()["items"]
    assert len(items) >= 2
    assert any(i["reviewer_type"] == "ai" for i in items)
