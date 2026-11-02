"""FLORA flower auction: any form, qty 1…∞, ACP escrow + Black Beauty ad lot."""
from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.main import app
from app.services.flora_auction import kinds


def _register_user(client, label="flora"):
    email = f"{label}_{uuid4().hex[:12]}@test.com"
    res = client.post(
        "/v1/auth/users",
        json={"email": email, "password": "password123", "display_name": f"{label} bidder"},
        headers={"Authorization": ""},
    )
    assert res.status_code in (200, 201), res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_flora_auction_routes_registered():
    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/v1/flora-auction/catalog" in paths
    assert "/v1/flora-auction/lots" in paths
    assert "/v1/flora-auction/lots/{lot_id}/bids" in paths


def test_flora_auction_catalog_has_black_beauty_and_forms(client):
    res = client.get("/v1/flora-auction/catalog")
    assert res.status_code == 200, res.text
    data = res.json()
    lots = data["lots"]
    forms_found = {lot["form"] for lot in lots}
    assert "hybrid_literacy" in forms_found
    assert "cut" in forms_found
    assert forms_found.issubset(set(kinds()))
    assert data["hero_image_href"] == "/flora/black-beauty.jpg"
    assert all(lot["settlement"] == "acp_escrow_smart_contract" for lot in lots)
    assert all(len(lot["contract_hash"]) == 64 for lot in lots)
    assert any(lot["id"] == "flower-black-beauty" for lot in lots)
    beauty = next(lot for lot in lots if lot["id"] == "flower-black-beauty")
    assert beauty["starting_acp"] == "12000"
    assert beauty["quantity"] == 1000000
    assert beauty["image_href"] == "/flora/black-beauty.jpg"
    assert Decimal(beauty["current_acp"]) >= Decimal(beauty["starting_acp"])


def test_flora_auction_bid_updates_price(client):
    headers = _register_user(client)
    catalog = client.get("/v1/flora-auction/catalog")
    assert catalog.status_code == 200, catalog.text
    lot = next(item for item in catalog.json()["lots"] if item["id"] == "flower-rose-red-dozen")
    first_amount = lot["min_next_acp"] if int(lot["bid_count"] or 0) else lot["current_acp"]
    first = client.post(
        "/v1/flora-auction/lots/flower-rose-red-dozen/bids",
        json={"amount_acp": first_amount},
        headers=headers,
    )
    assert first.status_code == 201, first.text
    body = first.json()
    assert Decimal(body["amount_acp"]) == Decimal(first_amount)
    assert Decimal(body["lot"]["current_acp"]) == Decimal(first_amount)
    assert body["lot"]["bid_count"] >= 1
    assert body.get("deal_cipher_id")
    assert body.get("deal_content_hash")

    too_low = client.post(
        "/v1/flora-auction/lots/flower-rose-red-dozen/bids",
        json={"amount_acp": first_amount},
        headers=headers,
    )
    assert too_low.status_code == 400

    nxt = body["lot"]["min_next_acp"]
    second = client.post(
        "/v1/flora-auction/lots/flower-rose-red-dozen/bids",
        json={"amount_acp": nxt},
        headers=headers,
    )
    assert second.status_code == 201, second.text
    assert Decimal(second.json()["lot"]["current_acp"]) == Decimal(nxt)


def test_flora_auction_user_can_list_unlimited_and_cannot_self_bid(client):
    seller = _register_user(client, "seller")
    buyer = _register_user(client, "buyer")
    created = client.post(
        "/v1/flora-auction/lots",
        json={
            "form": "bouquet",
            "name": "Peony cascade",
            "variety": "Sarah Bernhardt",
            "quantity": None,
            "blurb": "Unlimited peony bouquet restock flag via florist partner escrow.",
            "starting_acp": "950",
            "license_acknowledged": True,
        },
        headers=seller,
    )
    assert created.status_code == 201, created.text
    lot = created.json()
    assert lot["listed_by_user"] is True
    assert lot["form"] == "bouquet"
    assert lot["quantity"] is None
    assert lot["starting_acp"] == "950"
    assert lot["settlement"] == "acp_escrow_smart_contract"

    self_bid = client.post(
        f"/v1/flora-auction/lots/{lot['id']}/bids",
        json={"amount_acp": "950"},
        headers=seller,
    )
    assert self_bid.status_code == 400

    buy = client.post(
        f"/v1/flora-auction/lots/{lot['id']}/bids",
        json={"amount_acp": "950"},
        headers=buyer,
    )
    assert buy.status_code == 201, buy.text
    assert Decimal(buy.json()["lot"]["current_acp"]) == Decimal("950")


def test_flora_auction_list_finite_qty(client):
    headers = _register_user(client, "qty")
    res = client.post(
        "/v1/flora-auction/lots",
        json={
            "form": "cut",
            "name": "White lily stems",
            "variety": "Casa Blanca",
            "quantity": 24,
            "blurb": "Twenty-four cut lily stems for event floristry escrow.",
            "starting_acp": "360",
            "license_acknowledged": True,
        },
        headers=headers,
    )
    assert res.status_code == 201, res.text
    assert res.json()["quantity"] == 24


def test_flora_auction_list_requires_license(client):
    headers = _register_user(client, "nolicense")
    res = client.post(
        "/v1/flora-auction/lots",
        json={
            "form": "seed",
            "name": "Sunflower pack",
            "variety": "Mammoth",
            "blurb": "Seed pack that should require license acknowledgement.",
            "starting_acp": "40",
            "license_acknowledged": False,
        },
        headers=headers,
    )
    assert res.status_code == 400


def test_flora_auction_list_requires_auth(client):
    res = client.post(
        "/v1/flora-auction/lots",
        json={
            "form": "potted",
            "name": "Unauth",
            "variety": "Mix",
            "blurb": "Should not list without a session.",
            "starting_acp": "100",
            "license_acknowledged": True,
        },
        headers={"Authorization": ""},
    )
    assert res.status_code in (401, 403)


def test_flora_auction_rejects_markup_and_ceiling(client):
    headers = _register_user(client, "xss")
    markup = client.post(
        "/v1/flora-auction/lots",
        json={
            "form": "cut",
            "name": "<script>alert(1)</script>",
            "variety": "Mix",
            "blurb": "Licensed florist stems ready for escrow transfer.",
            "starting_acp": "100",
            "license_acknowledged": True,
        },
        headers=headers,
    )
    assert markup.status_code == 400

    huge = client.post(
        "/v1/flora-auction/lots",
        json={
            "form": "bouquet",
            "name": "Huge",
            "variety": "Mix",
            "blurb": "Should reject ceiling overflow on starting price.",
            "starting_acp": "1000000000001",
            "license_acknowledged": True,
        },
        headers=headers,
    )
    assert huge.status_code == 400


def test_flora_auction_bid_requires_auth(client):
    res = client.post(
        "/v1/flora-auction/lots/flower-black-beauty/bids",
        json={"amount_acp": "12000"},
        headers={"Authorization": ""},
    )
    assert res.status_code in (401, 403)
