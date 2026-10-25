"""Pricing regressions; service tests do not require a database or API server."""
import json
from decimal import Decimal
from pathlib import Path

import pytest

from app.config import get_settings
from app.services import market_economy as economy
from app.services.workflow_execution import (
    WORKFLOW_BUNDLES, WORKFLOW_TEMPLATES, WORKFLOW_CREDIT_PACKAGES,
    quote_bundle_amount, quote_credit_package_amount, quote_workflow_amount,
)


@pytest.fixture(autouse=True)
def live_pricing(monkeypatch):
    monkeypatch.setenv("WACP_ORACLE_PIN_DESK", "false")
    get_settings.cache_clear()
    economy.clear_oracle_cache()
    economy._ORACLE.update(at=__import__("time").time(), price="0.000002", source="test")
    yield
    economy.clear_oracle_cache()
    get_settings.cache_clear()


def test_all_catalog_skus_have_explicit_positive_prices_and_frontend_matches():
    for item in [*WORKFLOW_TEMPLATES, *WORKFLOW_BUNDLES]:
        assert economy.catalog_amount_to_usd_sticker(item.price.amount, catalog_slug=item.slug) > 0
    frontend = Path(__file__).resolve().parents[2] / "frontend-app/src/lib/catalogPrices.json"
    assert json.loads(frontend.read_text()) == economy.CATALOG_USD_PRICES


def test_large_legacy_numbers_are_not_retail_prices():
    assert economy.quote_catalog_acp("8900", catalog_slug="aeterna-dna-pheromone-perfume")[1] == Decimal("29")
    assert economy.quote_catalog_acp("1000000", catalog_slug="aeterna-dna-wellness-report")[1] == Decimal("39")
    assert economy.quote_catalog_acp("12000", catalog_slug="counsel-crypto-assets")[1] == Decimal("39")


def test_no_ten_thousand_price_cliff():
    values = [economy.catalog_amount_to_usd_sticker(str(n)) for n in (9999, 10000, 10001)]
    assert values == [Decimal("9999"), Decimal("10000"), Decimal("10001")]


def test_checkout_matches_display_and_bridge_ratio():
    for item in WORKFLOW_TEMPLATES:
        face = economy.catalog_amount_to_usd_sticker(item.price.amount, catalog_slug=item.slug)
        acp = quote_workflow_amount(item, "ACP")
        assert acp * Decimal("0.00002") >= face
        assert acp * Decimal("0.00002") - face < Decimal("0.0000002")
        assert quote_workflow_amount(item, "wACP") == acp * 9


def test_every_bundle_costs_less_than_its_components():
    by_slug = {item.slug: item for item in WORKFLOW_TEMPLATES}
    for bundle in WORKFLOW_BUNDLES:
        total = sum(quote_workflow_amount(by_slug[slug], "ACP") for slug in bundle.workflow_slugs)
        assert Decimal(0) < quote_bundle_amount(bundle, "ACP") < total


def test_credit_balance_is_not_reinterpreted_as_usd():
    for package in WORKFLOW_CREDIT_PACKAGES:
        assert quote_credit_package_amount(package, "ACP") == Decimal(package.price.amount)
        assert quote_credit_package_amount(package, "wACP") == Decimal(package.price.amount) * 9


def test_subscription_periods_offer_savings():
    for slug in ("aeterna-m-receptor-subscription", "aeterna-pulmopure-subscription", "stardust-weather-control-subscription"):
        monthly = Decimal(economy.CATALOG_USD_PRICES[f"{slug}:monthly"])
        quarterly = Decimal(economy.CATALOG_USD_PRICES[f"{slug}:quarterly"])
        annual = Decimal(economy.CATALOG_USD_PRICES[f"{slug}:annual"])
        assert monthly < quarterly < monthly * 3
        assert quarterly < annual < monthly * 12


def test_unknown_sku_fails_instead_of_using_legacy_amount():
    with pytest.raises(KeyError):
        economy.quote_catalog_acp("1000000", catalog_slug="missing-product")


def test_pinned_desk_still_uses_current_product_price(monkeypatch):
    monkeypatch.setenv("WACP_ORACLE_PIN_DESK", "true")
    get_settings.cache_clear()
    acp, sticker, _ = economy.quote_catalog_acp("1000000", catalog_slug="aeterna-dna-wellness-report")
    assert acp == sticker == Decimal("39")
