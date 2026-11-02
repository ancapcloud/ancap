"""Galaxy / solar-system title auction."""
from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.main import app
from app.services.otc_intake import catalog as otc_catalog
from app.services.space_auction import kinds


def _register_user(client):
    email = f"galaxy_{uuid4().hex[:12]}@test.com"
    res = client.post(
        "/v1/auth/users",
        json={"email": email, "password": "password123", "display_name": "galaxy bidder"},
        headers={"Authorization": ""},
    )
    assert res.status_code in (200, 201), res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_space_auction_routes_registered():
    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/v1/space-auction/catalog" in paths
    assert "/v1/space-auction/lots/{lot_id}/bids" in paths


def test_otc_space_catalog_has_star_planet_satellite_prices():
    c = otc_catalog()
    by_class = {s.object_class: s for s in c.space_objects}
    assert "star" in by_class
    assert "planet" in by_class
    assert "moon" in by_class
    assert "dwarf_planet" in by_class
    assert "asteroid" in by_class
    assert "comet" in by_class
    assert "nebula" in by_class
    assert "galaxy" in by_class
    assert "black_hole" in by_class
    assert "exoplanet" in by_class
    assert "radiation" in by_class
    assert Decimal(by_class["radiation"].indicative_starting_acp) > 0
    assert Decimal(by_class["star"].indicative_starting_acp) > 0
    assert Decimal(by_class["planet"].indicative_starting_acp) > 0
    assert Decimal(by_class["satellite"].indicative_starting_acp) > 0
    assert Decimal(by_class["moon"].indicative_starting_acp) > 0


def test_space_auction_catalog_has_priced_stars_planets_satellites(client):
    res = client.get("/v1/space-auction/catalog")
    assert res.status_code == 200, res.text
    data = res.json()
    lots = data["lots"]
    kinds_found = {lot["kind"] for lot in lots}
    assert kinds_found == set(kinds())
    assert all(Decimal(lot["starting_acp"]) > 0 for lot in lots)
    assert all(Decimal(lot["current_acp"]) >= Decimal(lot["starting_acp"]) for lot in lots)
    assert any(lot["id"] == "star-sol" for lot in lots)
    assert any(lot["id"] == "planet-mars" for lot in lots)
    assert any(lot["id"] == "sat-luna" for lot in lots)
    assert any(lot["id"] == "dwarf-pluto" for lot in lots)
    assert any(lot["id"] == "gal-milky-way" for lot in lots)
    assert any(lot["id"] == "rad-cmb" for lot in lots)
    assert "dwarf_planet" in kinds_found
    assert "asteroid" in kinds_found
    assert "comet" in kinds_found
    assert "nebula" in kinds_found
    assert "galaxy" in kinds_found
    assert "black_hole" in kinds_found
    assert "exoplanet" in kinds_found
    assert "radiation" in kinds_found
    featured_ids = {lot["id"] for lot in data["featured"]}
    assert "planet-earth" in featured_ids
    mars = next(lot for lot in lots if lot["id"] == "planet-mars")
    assert mars["starting_acp"] == "1800000"
    assert Decimal(mars["current_acp"]) >= Decimal(mars["starting_acp"])
    assert all(lot.get("high_bidder_user_id") is None for lot in lots)


def test_space_auction_bid_updates_price(client):
    headers = _register_user(client)
    catalog = client.get("/v1/space-auction/catalog")
    assert catalog.status_code == 200, catalog.text
    mars = next(lot for lot in catalog.json()["lots"] if lot["id"] == "planet-mars")
    first_amount = mars["min_next_acp"] if int(mars["bid_count"] or 0) else mars["current_acp"]
    first = client.post(
        "/v1/space-auction/lots/planet-mars/bids",
        json={"amount_acp": first_amount},
        headers=headers,
    )
    assert first.status_code == 201, first.text
    body = first.json()
    assert Decimal(body["amount_acp"]) == Decimal(first_amount)
    assert Decimal(body["lot"]["current_acp"]) == Decimal(first_amount)
    assert body["lot"]["bid_count"] >= 1

    too_low = client.post(
        "/v1/space-auction/lots/planet-mars/bids",
        json={"amount_acp": first_amount},
        headers=headers,
    )
    assert too_low.status_code == 400

    nxt = body["lot"]["min_next_acp"]
    second = client.post(
        "/v1/space-auction/lots/planet-mars/bids",
        json={"amount_acp": nxt},
        headers=headers,
    )
    assert second.status_code == 201, second.text
    assert Decimal(second.json()["lot"]["current_acp"]) == Decimal(nxt)
    assert second.json()["lot"]["bid_count"] == body["lot"]["bid_count"] + 1


def test_space_auction_unknown_lot(client):
    headers = _register_user(client)
    res = client.post(
        "/v1/space-auction/lots/planet-pluto/bids",
        json={"amount_acp": "1"},
        headers=headers,
    )
    assert res.status_code == 404


def test_space_auction_bid_requires_auth(client):
    res = client.post(
        "/v1/space-auction/lots/sat-luna/bids",
        json={"amount_acp": "4500000"},
        headers={"Authorization": ""},
    )
    assert res.status_code in (401, 403)
