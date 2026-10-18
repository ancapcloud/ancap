"""TECH auction + AuctionEscrow anchoring tests."""

from tests.api.test_organizations import _register_and_login


def test_tech_auction_catalog_and_bid(client):
    catalog = client.get("/v1/tech-auction/catalog")
    assert catalog.status_code == 200, catalog.text
    body = catalog.json()
    assert body["currency"] == "ACP"
    assert len(body["lots"]) >= 3
    assert len(body["technologies"]) >= 3
    stack_ids = {t["id"] for t in body["technologies"]}
    assert "stack-floquet-bosonic" in stack_ids
    assert "stack-stardust-weather" in stack_ids
    assert "stack-aeterna-synthetic-blood-mamba" in stack_ids
    assert "stack-aeterna-oxygen-carrier" in stack_ids
    assert any(lot["id"] == "tech-floquet-bosonic" for lot in body["lots"])
    assert any(lot["id"] == "tech-stardust-weather-control-global" for lot in body["lots"])
    assert any(lot["id"] == "tech-aeterna-synthetic-blood-mamba" for lot in body["lots"])
    assert any(lot["id"] == "tech-aeterna-oxygen-carrier" for lot in body["lots"])
    assert any(lot["category"] == "quantum_compute" for lot in body["lots"])
    assert any(lot["category"] == "weather_control" for lot in body["lots"])
    weather = next(lot for lot in body["lots"] if lot["id"] == "tech-stardust-weather-control-global")
    assert weather["starting_acp"].startswith("58000")
    mamba = next(lot for lot in body["lots"] if lot["id"] == "tech-aeterna-synthetic-blood-mamba")
    assert mamba["starting_acp"] == "98000.00000000" or mamba["starting_acp"].startswith("98000")
    ox = next(lot for lot in body["lots"] if lot["id"] == "tech-aeterna-oxygen-carrier")
    assert ox["starting_acp"].startswith("92000")
    lot_id = body["lots"][0]["id"]
    _, headers, _ = _register_and_login(client, "Tech Bidder")
    # The increment is personalized by network-growth score. Quote as the
    # bidder, rather than reusing the test client's previous authenticated user.
    bidder_lot = client.get(f"/v1/tech-auction/lots/{lot_id}", headers=headers)
    assert bidder_lot.status_code == 200, bidder_lot.text
    min_next = bidder_lot.json()["min_next_acp"]
    bid = client.post(
        f"/v1/tech-auction/lots/{lot_id}/bids",
        headers=headers,
        json={"amount_acp": min_next},
    )
    assert bid.status_code == 201, bid.text
    data = bid.json()
    assert data["status"] == "winning"
    assert data["tx_hash"]
    assert data["tx_hash"].startswith("0x")
    assert data.get("deal_cipher_id", "").startswith("xwing-draft10")
    assert data.get("deal_content_hash", "").startswith("sha256:")
    catalog2 = client.get("/v1/tech-auction/catalog")
    assert catalog2.json()["deal_encryption"]["cipher_id"].startswith("xwing-draft10")


def test_tech_auction_list_anchors_create(client):
    _, headers, _ = _register_and_login(client, "Tech Seller")
    listed = client.post(
        "/v1/tech-auction/lots",
        headers=headers,
        json={
            "category": "ai_workflow",
            "title": "Custom ACP workflow pack",
            "stack": "FastAPI + ledger",
            "blurb": "Licensed workflow rail for agents with ACP metering.",
            "starting_acp": "5000",
            "license_acknowledged": True,
        },
    )
    assert listed.status_code == 201, listed.text
    lot = listed.json()
    assert lot["tx_hash"]
    assert lot["contract_hash"]
