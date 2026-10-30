"""New BSC exposure closes without changing legacy redemption or ACP accounting."""
import asyncio
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.config import get_settings
from app.schemas.bridge_rail import BridgeIntentAcpToBscCreate
from app.schemas.exchange_office import ExchangeQuoteRequest


@pytest.fixture(autouse=True)
def racp_only(monkeypatch):
    monkeypatch.setenv("EXTERNAL_TOKEN_RACP_ONLY", "true")
    monkeypatch.setenv("BRIDGE_RAIL_ENABLED", "true")
    monkeypatch.setenv("BRIDGE_RAIL_PAUSED", "false")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_catalog_keeps_acp_hub_and_legacy_redemption_only():
    from app.services.exchange_office import build_assets, build_pairs, catalog, quote

    assets = {a.id: a for a in build_assets()}
    assert catalog().hub_asset == "acp"
    assert assets["racp_robinhood"].metadata["primary_external_asset"] is True
    assert not {"wacp_bsc", "sacp_bsc", "usdt_bsc"}.intersection(assets)
    assert not any(p.to_asset in {"wacp_bsc", "sacp_bsc", "usdt_bsc"} for p in build_pairs())
    from app.api.routers.bridge_rail import _quote_bsc_to_acp
    old = _quote_bsc_to_acp("10")
    assert Decimal(old.acp_amount_floor) == Decimal("1")


@pytest.mark.parametrize("src,dst", [("acp", "wacp_bsc"), ("acp", "sacp_bsc"), ("acp", "usdt_bsc"), ("usdt_bsc", "acp")])
def test_new_bsc_exchange_quotes_are_rejected(src, dst):
    from app.services.exchange_office import quote
    with pytest.raises(HTTPException):
        quote(ExchangeQuoteRequest(from_asset=src, to_asset=dst, from_amount="10"))


def test_forward_bridge_rejects_before_any_database_mutation():
    from app.api.routers.bridge_rail import create_intent_acp_to_bsc
    body = BridgeIntentAcpToBscCreate(amount_acp="1", user_bsc_address="0x" + "11" * 20)
    with pytest.raises(HTTPException) as error:
        asyncio.run(create_intent_acp_to_bsc(body, user_id=str(uuid4()), session=None))
    assert error.value.status_code == 409


def test_sacp_mint_closed_without_disabling_redemption(monkeypatch):
    from app.services.sacp import create_mint_intent, public_status
    monkeypatch.setenv("SACP_ENABLED", "true")
    monkeypatch.setenv("SACP_PAUSED", "false")
    get_settings.cache_clear()
    status = public_status()
    assert status["mint_available"] is False
    assert status["redeem_available"] is True
    with pytest.raises(HTTPException) as error:
        asyncio.run(create_mint_intent(None, acp_amount="1", user_bsc_address="0x" + "11" * 20))
    assert error.value.status_code == 409


def test_eur_checkout_uses_operator_rate_without_bsc_oracle(monkeypatch):
    from app.services import market_economy as market
    from app.services.eur_pricing import PRICES
    monkeypatch.setenv("ACP_PER_EUR", "100")
    get_settings.cache_clear()
    async def forbidden():
        raise AssertionError("BSC pricing must not be requested")
    monkeypatch.setattr(market, "get_wacp_usd_oracle", forbidden)
    assert asyncio.run(market.get_checkout_reference()) == (Decimal("0"), "fixed_eur_accounting")
    amount, face, legacy_spot = market.quote_catalog_acp("29", catalog_slug="token-risk-report-pro")
    assert face == Decimal(PRICES["token-risk-report-pro"])
    assert amount == face * 100
    assert legacy_spot == 0
    with pytest.raises(HTTPException):
        market.quote_catalog_acp("29", catalog_slug="token-risk-report-pro", payment_currency="wACP")


def test_public_workflow_catalog_uses_eur_faces_and_internal_acp():
    from app.api.routers.workflow_store import list_workflow_templates
    result = asyncio.run(list_workflow_templates(category=None, q=None))
    assert result.items
    for item in result.items:
        assert item.eur_sticker.currency == "EUR"
        assert item.usd_sticker is None
        assert item.price.currency == "ACP"
        assert Decimal(item.price.amount) == Decimal(item.eur_sticker.amount) * 100
        assert item.accepted_currencies == ["ACP"]


def test_new_credit_package_has_explicit_eur_face_and_snapshotable_acp():
    from app.services.workflow_execution import find_credit_package
    from app.services.stripe_payments import quote_stripe_credit_package_amount
    package = find_credit_package("starter-credits")
    assert package.fiat_price.currency == "EUR"
    assert package.price.currency == package.credit_amount.currency == "ACP"
    assert Decimal(package.price.amount) == Decimal(package.fiat_price.amount) * 100
    assert quote_stripe_credit_package_amount(package, "EUR") == Decimal(package.fiat_price.amount)
    with pytest.raises(HTTPException):
        quote_stripe_credit_package_amount(package, "USD")
