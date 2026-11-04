"""Listings and Orders."""
from tests.conftest import unique_name


import pytest

# Moderation routes used by these tests are platform-admin only.
pytestmark = pytest.mark.usefixtures("platform_admin")

USER_AUTH_HEADER = {"X-Requested-With": "XMLHttpRequest"}

VERTICAL_SPEC = {
    "allowed_actions": [{"name": "a", "args_schema": {"type": "object"}}],
    "required_resources": ["data_feed"],
    "metrics": [{"name": "m", "value_schema": {"type": "number"}}],
    "risk_spec": {},
}


def _strategy_with_listing(client):
    owner_agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("lo_agent"), "public_key": "x" * 32, "roles": ["seller"]},
    )
    vert = client.post(
        "/v1/verticals/propose",
        json={"name": unique_name("lo_vert"), "spec": VERTICAL_SPEC},
    )
    vid = vert.json()["id"]
    client.post(f"/v1/verticals/{vid}/review", json={"decision": "approve"})
    strat = client.post(
        "/v1/strategies",
        json={"name": unique_name("lo_s"), "vertical_id": vid, "owner_agent_id": owner_agent.json()["id"]},
    )
    sid = strat.json()["id"]
    workflow = {
        "vertical_id": vid,
        "version": "1.0",
        "steps": [{"id": "s1", "action": "a", "args": {"x": 1}}],
    }
    ver = client.post(
        f"/v1/strategies/{sid}/versions",
        json={"semver": "0.1.0", "workflow": workflow},
    )
    assert ver.status_code == 201, ver.text
    version_id = ver.json()["id"]
    listing = client.post(
        "/v1/listings",
        json={
            "strategy_id": sid,
            "strategy_version_id": version_id,
            "fee_model": {"type": "one_time", "one_time_price": {"amount": "10", "currency": "VUSD"}},
            "status": "active",
        },
    )
    assert listing.status_code == 201, listing.text
    return owner_agent.json()["id"], sid, listing.json()["id"]


def _buyer_agent(client):
    r = client.post(
        "/v1/agents",
        json={"display_name": unique_name("buyer"), "public_key": "b" * 32, "roles": ["buyer"]},
    )
    return r.json()["id"]


def test_create_listing(client):
    _, _, listing_id = _strategy_with_listing(client)
    assert listing_id


def test_list_listings(client):
    _strategy_with_listing(client)
    r = client.get("/v1/listings", params={"limit": 5})
    assert r.status_code == 200
    assert "items" in r.json()


def test_place_order(client):
    _, _, listing_id = _strategy_with_listing(client)
    buyer_id = _buyer_agent(client)
    # L3: buyer must have balance for order escrow
    client.post(
        "/v1/ledger/deposit",
        json={"account_owner_type": "agent", "account_owner_id": buyer_id, "amount": {"amount": "100", "currency": "VUSD"}},
        headers={"Idempotency-Key": unique_name("idk_dep")},
    )
    r = client.post(
        "/v1/orders",
        json={
            "listing_id": listing_id,
            "buyer_type": "agent",
            "buyer_id": buyer_id,
            "payment_method": "ledger",
        },
        headers={"Idempotency-Key": unique_name("idk_order")},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "paid"
    assert data["listing_id"] == listing_id


def test_list_access_grants(client):
    _, _, listing_id = _strategy_with_listing(client)
    buyer_id = _buyer_agent(client)
    client.post(
        "/v1/ledger/deposit",
        json={"account_owner_type": "agent", "account_owner_id": buyer_id, "amount": {"amount": "100", "currency": "VUSD"}},
        headers={"Idempotency-Key": unique_name("idk_dep2")},
    )
    client.post(
        "/v1/orders",
        json={"listing_id": listing_id, "buyer_type": "agent", "buyer_id": buyer_id, "payment_method": "ledger"},
        headers={"Idempotency-Key": unique_name("idk_order2")},
    )
    r = client.get("/v1/access/grants", params={"limit": 5})
    assert r.status_code == 200
    assert "items" in r.json()


def test_quarantine_new_agent_order_limit(client):
    """Agent created < 24h is limited to quarantine_max_orders_per_day (default 3) orders."""
    listing_ids = [_strategy_with_listing(client)[2] for _ in range(4)]
    buyer_id = _buyer_agent(client)
    client.post(
        "/v1/ledger/deposit",
        json={"account_owner_type": "agent", "account_owner_id": buyer_id, "amount": {"amount": "500", "currency": "VUSD"}},
        headers={"Idempotency-Key": unique_name("idk_dep3")},
    )
    for i in range(3):
        r = client.post(
            "/v1/orders",
            json={"listing_id": listing_ids[i], "buyer_type": "agent", "buyer_id": buyer_id, "payment_method": "ledger"},
            headers={"Idempotency-Key": unique_name(f"idk_o{i}")},
        )
        assert r.status_code == 201, (i, r.status_code, r.text)
    r4 = client.post(
        "/v1/orders",
        json={"listing_id": listing_ids[3], "buyer_type": "agent", "buyer_id": buyer_id, "payment_method": "ledger"},
        headers={"Idempotency-Key": unique_name("idk_o4")},
    )
    assert r4.status_code == 403
    assert "Quarantine" in r4.json().get("detail", "")


def test_marketplace_listings_filters_and_sort(client):
    owner_agent = client.post(
        "/v1/agents",
        json={"display_name": unique_name("market_owner"), "public_key": "m" * 32, "roles": ["seller"]},
    ).json()
    vert = client.post(
        "/v1/verticals/propose",
        json={"name": unique_name("Automation"), "spec": VERTICAL_SPEC},
    ).json()
    client.post(f"/v1/verticals/{vert['id']}/review", json={"decision": "approve"})

    def create_listing(name: str, description: str, amount: str, note: str | None = None):
        strat = client.post(
            "/v1/strategies",
            json={
                "name": name,
                "description": description,
                "vertical_id": vert["id"],
                "owner_agent_id": owner_agent["id"],
            },
        )
        sid = strat.json()["id"]
        workflow = {
            "vertical_id": vert["id"],
            "version": "1.0",
            "steps": [{"id": "s1", "action": "a", "args": {"x": 1}}],
        }
        ver = client.post(f"/v1/strategies/{sid}/versions", json={"semver": "0.1.0", "workflow": workflow})
        assert ver.status_code == 201, ver.text
        listing = client.post(
            "/v1/listings",
            json={
                "strategy_id": sid,
                "strategy_version_id": ver.json()["id"],
                "fee_model": {"type": "one_time", "one_time_price": {"amount": amount, "currency": "ACP"}},
                "status": "active",
                "notes": note,
            },
        )
        assert listing.status_code == 201, listing.text
        return sid, listing.json()["id"]

    alpha_sid, alpha_listing_id = create_listing("Alpha Trading", "Momentum alpha setup", "9", "#featured")
    beta_sid, beta_listing_id = create_listing("Beta Yield", "Stable yield automation", "15")

    opened = client.get(f"/v1/listings/{alpha_listing_id}")
    assert opened.status_code == 200, opened.text

    buyer_id = client.get("/v1/users/me").json()["id"]
    client.post(
        "/v1/ledger/deposit",
        json={"account_owner_type": "user", "account_owner_id": buyer_id, "amount": {"amount": "100", "currency": "ACP"}},
        headers={"Idempotency-Key": unique_name("market_dep")},
    )
    paid = client.post(
        "/v1/orders",
        json={"listing_id": alpha_listing_id, "buyer_type": "user", "buyer_id": buyer_id, "payment_method": "internal"},
        headers={**USER_AUTH_HEADER, "Idempotency-Key": unique_name("market_order")},
    )
    assert paid.status_code == 201, paid.text

    review = client.post(
        "/v1/reviews",
        json={
            "reviewer_type": "user",
            "reviewer_id": buyer_id,
            "target_type": "listing",
            "target_id": alpha_listing_id,
            "weight": 0.95,
            "text": "actually useful",
        },
    )
    assert review.status_code == 201, review.text

    search_res = client.get("/v1/listings/marketplace/listings", params={"search": "Momentum", "sort": "popular", "limit": 10})
    assert search_res.status_code == 200, search_res.text
    search_data = search_res.json()
    assert search_data["total"] >= 1
    assert search_data["items"][0]["strategy_id"] == alpha_sid
    assert search_data["items"][0]["listing_purchases"] >= 1
    assert search_data["items"][0]["listing_views"] >= 1
    assert search_data["items"][0]["rating"] >= 0.9
    assert search_data["items"][0]["is_featured"] is True
    assert search_data["items"][0]["is_trending"] is True
    assert vert["name"] in search_data["available_categories"]

    category_res = client.get(
        "/v1/listings/marketplace/listings",
        params={"category": vert["name"].lower(), "price_max": "10", "sort": "price_asc"},
    )
    assert category_res.status_code == 200, category_res.text
    category_items = category_res.json()["items"]
    assert len(category_items) == 1
    assert category_items[0]["id"] == alpha_listing_id

    rating_res = client.get("/v1/listings/marketplace/listings", params={"sort": "rating"})
    assert rating_res.status_code == 200, rating_res.text
    rating_items = rating_res.json()["items"]
    assert rating_items[0]["id"] == alpha_listing_id
    assert any(item["id"] == beta_listing_id for item in rating_items)
