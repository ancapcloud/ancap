"""Starlink installation desk — catalog, quote, workflow SKUs."""
from decimal import Decimal


def test_starlink_catalog(client):
    r = client.get("/v1/starlink-install/catalog")
    assert r.status_code == 200, r.text
    body = r.json()
    note = body["compliance_note"].lower()
    assert "not an official starlink" in note or "not an official" in note
    assert "jobcenter" in note or "avgs" in note
    assert body["legal_href"] == "/legal/starlink-install"
    assert body.get("official_reseller") is False
    assert body.get("jobcenter_guarantee") is False
    assert body["service_fee_eur"] == "3"

    ids = {s["id"] for s in body["services"]}
    for expected in (
        "starlink-standard",
        "starlink-roof",
        "starlink-business",
        "starlink-network",
        "starlink-mobile",
        "starlink-relocate",
        "starlink-troubleshoot",
    ):
        assert expected in ids

    regions = {x["id"] for x in body["regions"]}
    assert "de-nrw" in regions
    assert "de" in regions

    standard = next(s for s in body["services"] if s["id"] == "starlink-standard")
    assert standard["price_eur"] == "150"
    assert standard["workflow_slug"] == "starlink-standard"
    assert "de-nrw" in standard["regions"]


def test_starlink_quote_standard(client):
    r = client.post(
        "/v1/starlink-install/quote",
        json={"service_id": "starlink-standard", "region": "de-nrw", "payment_currency": "ACP"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert Decimal(body["installation_fee_eur"]) == Decimal("150")
    assert Decimal(body["service_fee_eur"]) == Decimal("3")
    assert Decimal(body["total_eur"]) == Decimal("153")
    assert Decimal(body["total_usdt"]) == Decimal("153")
    assert body["payment_currency"] == "ACP"
    assert Decimal(body["amount_acp"]) > 0
    assert Decimal(body["amount_wacp"]) == Decimal(body["amount_acp"]) * 10
    assert body["workflow_slug"] == "starlink-standard"
    assert "Germany" in body["provider_location"] or "NRW" in body["provider_location"]


def test_starlink_quote_unknown_service(client):
    r = client.post("/v1/starlink-install/quote", json={"service_id": "nope"})
    assert r.status_code == 400


def test_starlink_quote_region_mismatch(client):
    r = client.post(
        "/v1/starlink-install/quote",
        json={"service_id": "starlink-network", "region": "eu-eea-uk"},
    )
    assert r.status_code == 400


def test_starlink_workflow_templates_catalogued():
    from app.services.workflow_execution import WORKFLOW_TEMPLATES

    slugs = {t.slug for t in WORKFLOW_TEMPLATES}
    assert "starlink-install-intake" in slugs
    assert "starlink-standard" in slugs
    assert "starlink-roof" in slugs
    star = [t for t in WORKFLOW_TEMPLATES if t.category == "StarlinkInstall"]
    assert len(star) >= 7
    prices = {t.slug: t.price.amount for t in star}
    assert prices["starlink-install-intake"] == "153"
    assert prices["starlink-standard"] == "153"
    assert prices["starlink-network"] == "53"
    for t in star:
        assert "ACP" in t.accepted_currencies
        assert "wACP" in t.accepted_currencies
