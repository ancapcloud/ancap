"""Lunar land trading desk (R13)."""
from __future__ import annotations

from decimal import Decimal

from app.main import app


def test_lunar_routes_registered():
    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/v1/lunar/status" in paths
    assert "/v1/lunar/parcels" in paths
    assert "/v1/lunar/interests" in paths


def test_lunar_status_and_catalog_seed(client, monkeypatch):
    monkeypatch.setenv("FF_LUNAR_LAND", "true")
    from app.config import get_settings

    get_settings.cache_clear()

    status = client.get("/v1/lunar/status", headers={"Authorization": ""})
    assert status.status_code == 200, status.text
    body = status.json()
    assert body["feature_enabled"] is True
    assert body["division"] == "LUNAR_LAND"
    assert body["parcels_listed"] >= 5
    assert "Outer Space Treaty" in body["compliance_note"]
    assert "lnkd.in" in body["lfm_reference"]

    parcels = client.get("/v1/lunar/parcels", headers={"Authorization": ""})
    assert parcels.status_code == 200, parcels.text
    rows = parcels.json()
    assert len(rows) >= 5
    codes = {r["parcel_code"] for r in rows}
    assert "LUN-SHA-001" in codes
    shackleton = next(r for r in rows if r["parcel_code"] == "LUN-SHA-001")
    assert "ice_deposit" in shackleton["lfm_themes"]
    assert Decimal(shackleton["list_price_acp"]) > 0


def test_lunar_interest_requires_consent_and_auth(client, monkeypatch):
    monkeypatch.setenv("FF_LUNAR_LAND", "true")
    from app.config import get_settings

    get_settings.cache_clear()

    parcels = client.get("/v1/lunar/parcels", headers={"Authorization": ""})
    assert parcels.status_code == 200, parcels.text
    parcel_id = parcels.json()[0]["id"]

    unauth = client.post(
        "/v1/lunar/interests",
        json={
            "parcel_id": parcel_id,
            "kind": "inquire",
            "budget_acp": "1000",
            "consent_acknowledged": True,
        },
        headers={"Authorization": ""},
    )
    assert unauth.status_code in (401, 403), unauth.text

    no_consent = client.post(
        "/v1/lunar/interests",
        json={
            "parcel_id": parcel_id,
            "kind": "inquire",
            "budget_acp": "1000",
            "consent_acknowledged": False,
        },
    )
    assert no_consent.status_code == 400, no_consent.text

    ok = client.post(
        "/v1/lunar/interests",
        json={
            "parcel_id": parcel_id,
            "kind": "bid",
            "budget_acp": "150000",
            "notes": "polar ice interest",
            "consent_acknowledged": True,
        },
    )
    assert ok.status_code == 201, ok.text
    created = ok.json()
    assert created["kind"] == "bid"
    assert created["status"] == "open"
    assert Decimal(created["budget_acp"]) == Decimal("150000")

    mine = client.get("/v1/lunar/interests")
    assert mine.status_code == 200, mine.text
    assert any(x["id"] == created["id"] for x in mine.json())
