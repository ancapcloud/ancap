"""FAUNA companion-animal auction: buy/sell dogs, cats, and other pets on ACP contracts."""
from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.main import app
from app.services.animal_auction import kinds


def _register_user(client, label="fauna"):
    email = f"{label}_{uuid4().hex[:12]}@test.com"
    res = client.post(
        "/v1/auth/users",
        json={"email": email, "password": "password123", "display_name": f"{label} bidder"},
        headers={"Authorization": ""},
    )
    assert res.status_code in (200, 201), res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_animal_auction_routes_registered():
    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/v1/animal-auction/catalog" in paths
    assert "/v1/animal-auction/lots" in paths
    assert "/v1/animal-auction/lots/{lot_id}/bids" in paths


def test_animal_auction_catalog_has_dogs_and_cats(client):
    res = client.get("/v1/animal-auction/catalog")
    assert res.status_code == 200, res.text
    data = res.json()
    lots = data["lots"]
    kinds_found = {lot["species"] for lot in lots}
    assert "dog" in kinds_found
    assert "cat" in kinds_found
    assert kinds_found.issubset(set(kinds()))
    assert all(lot["settlement"] == "acp_escrow_smart_contract" for lot in lots)
    assert all(len(lot["contract_hash"]) == 64 for lot in lots)
    assert any(lot["id"] == "dog-german-shepherd" for lot in lots)
    assert any(lot["id"] == "cat-maine-coon" for lot in lots)
    shepherd = next(lot for lot in lots if lot["id"] == "dog-german-shepherd")
    assert shepherd["starting_acp"] == "8500"
    assert Decimal(shepherd["current_acp"]) >= Decimal(shepherd["starting_acp"])
    assert all(lot.get("high_bidder_user_id") is None for lot in lots)
    assert all(lot.get("seller_user_id") is None for lot in lots)


def test_animal_auction_bid_updates_price(client):
    headers = _register_user(client)
    catalog = client.get("/v1/animal-auction/catalog")
    assert catalog.status_code == 200, catalog.text
    lot = next(item for item in catalog.json()["lots"] if item["id"] == "dog-labrador")
    first_amount = lot["min_next_acp"] if int(lot["bid_count"] or 0) else lot["current_acp"]
    first = client.post(
        "/v1/animal-auction/lots/dog-labrador/bids",
        json={"amount_acp": first_amount},
        headers=headers,
    )
    assert first.status_code == 201, first.text
    body = first.json()
    assert Decimal(body["amount_acp"]) == Decimal(first_amount)
    assert Decimal(body["lot"]["current_acp"]) == Decimal(first_amount)
    assert body["lot"]["bid_count"] >= 1
    assert len(body["contract_hash"]) == 64

    too_low = client.post(
        "/v1/animal-auction/lots/dog-labrador/bids",
        json={"amount_acp": first_amount},
        headers=headers,
    )
    assert too_low.status_code == 400

    nxt = body["lot"]["min_next_acp"]
    second = client.post(
        "/v1/animal-auction/lots/dog-labrador/bids",
        json={"amount_acp": nxt},
        headers=headers,
    )
    assert second.status_code == 201, second.text
    assert Decimal(second.json()["lot"]["current_acp"]) == Decimal(nxt)


def test_animal_auction_user_can_list_and_cannot_self_bid(client):
    seller = _register_user(client, "seller")
    buyer = _register_user(client, "buyer")
    created = client.post(
        "/v1/animal-auction/lots",
        json={
            "species": "dog",
            "name": "Rook",
            "breed": "Border Collie",
            "age_months": 12,
            "blurb": "Licensed kennel collie, microchipped, ready for ACP escrow transfer.",
            "starting_acp": "4100",
            "license_acknowledged": True,
        },
        headers=seller,
    )
    assert created.status_code == 201, created.text
    lot = created.json()
    assert lot["listed_by_user"] is True
    assert lot["species"] == "dog"
    assert lot["starting_acp"] == "4100"
    assert lot["settlement"] == "acp_escrow_smart_contract"

    self_bid = client.post(
        f"/v1/animal-auction/lots/{lot['id']}/bids",
        json={"amount_acp": "4100"},
        headers=seller,
    )
    assert self_bid.status_code == 400

    buy = client.post(
        f"/v1/animal-auction/lots/{lot['id']}/bids",
        json={"amount_acp": "4100"},
        headers=buyer,
    )
    assert buy.status_code == 201, buy.text
    assert Decimal(buy.json()["lot"]["current_acp"]) == Decimal("4100")


def test_animal_auction_list_requires_license(client):
    headers = _register_user(client, "nolicense")
    res = client.post(
        "/v1/animal-auction/lots",
        json={
            "species": "cat",
            "name": "Mist",
            "breed": "Domestic Shorthair",
            "blurb": "Indoor cat looking for a new home via contract.",
            "starting_acp": "800",
            "license_acknowledged": False,
        },
        headers=headers,
    )
    assert res.status_code == 400


def test_animal_auction_list_requires_auth(client):
    res = client.post(
        "/v1/animal-auction/lots",
        json={
            "species": "dog",
            "name": "Unauth",
            "breed": "Mix",
            "blurb": "Should not list without a session.",
            "starting_acp": "500",
            "license_acknowledged": True,
        },
        headers={"Authorization": ""},
    )
    assert res.status_code in (401, 403)


def test_animal_auction_rejects_markup_and_ceiling(client):
    headers = _register_user(client, "xss")
    markup = client.post(
        "/v1/animal-auction/lots",
        json={
            "species": "dog",
            "name": "<script>alert(1)</script>",
            "breed": "Mix",
            "blurb": "Licensed kennel companion ready for escrow transfer.",
            "starting_acp": "500",
            "license_acknowledged": True,
        },
        headers=headers,
    )
    assert markup.status_code == 400

    huge = client.post(
        "/v1/animal-auction/lots",
        json={
            "species": "cat",
            "name": "Mist",
            "breed": "Domestic Shorthair",
            "blurb": "Indoor cat looking for a new home via contract.",
            "starting_acp": "1000000000001",
            "license_acknowledged": True,
        },
        headers=headers,
    )
    assert huge.status_code == 400


def test_animal_auction_rejects_unsafe_lot_id(client):
    headers = _register_user(client, "path")
    res = client.post(
        "/v1/animal-auction/lots/dog.labrador/bids",
        json={"amount_acp": "6200"},
        headers=headers,
    )
    assert res.status_code == 404


def test_animal_auction_bid_requires_auth(client):
    res = client.post(
        "/v1/animal-auction/lots/cat-maine-coon/bids",
        json={"amount_acp": "4800"},
        headers={"Authorization": ""},
    )
    assert res.status_code in (401, 403)
