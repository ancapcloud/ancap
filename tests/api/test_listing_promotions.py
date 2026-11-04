"""Sponsored marketplace placement (paid listing promotion)."""
import uuid
from decimal import Decimal

import pytest

from app.config import get_settings
from tests.conftest import unique_name
from tests.test_listings_orders import _strategy_with_listing

pytestmark = pytest.mark.usefixtures("platform_admin")


def _fund_agent(client, agent_id: str, amount: str = "5000", currency: str = "ACP"):
    r = client.post(
        "/v1/ledger/deposit",
        json={"account_owner_type": "agent", "account_owner_id": agent_id, "amount": {"amount": amount, "currency": currency}},
        headers={"Idempotency-Key": unique_name("idk_promo_dep")},
    )
    assert r.status_code in (200, 201), r.text


def _agent_balance(client, agent_id: str, currency: str = "ACP") -> Decimal:
    r = client.get("/v1/ledger/balance", params={"owner_type": "agent", "owner_id": agent_id})
    assert r.status_code == 200, r.text
    for item in r.json().get("balances", []):
        if item["currency"] == currency:
            return Decimal(item["amount"])
    return Decimal(0)


@pytest.fixture
def promo_settings(monkeypatch):
    monkeypatch.setenv("LISTING_PROMOTION_DAILY_FEE", "100")
    monkeypatch.setenv("LISTING_PROMOTION_MAX_DAYS", "30")
    monkeypatch.setenv("LISTING_PROMOTION_SLOTS_PER_CATEGORY", "3")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_pricing_is_public(client, promo_settings):
    r = client.get("/v1/listings/promotions/pricing", headers={"Authorization": ""})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["enabled"] is True
    assert body["daily_fee"] == {"amount": "100", "currency": "ACP"}
    assert body["max_days"] == 30


def test_owner_buys_placement_and_listing_leads_marketplace(client, promo_settings):
    agent_id, _sid, listing_id = _strategy_with_listing(client)
    _fund_agent(client, agent_id)
    before = _agent_balance(client, agent_id)

    r = client.post(f"/v1/listings/{listing_id}/promotions", json={"days": 3})
    assert r.status_code == 201, r.text
    promo = r.json()
    assert promo["amount"] == {"amount": "300", "currency": "ACP"}
    assert promo["ledger_event_id"]
    assert _agent_balance(client, agent_id) == before - Decimal(300)

    market = client.get("/v1/listings/marketplace/listings", params={"limit": 5})
    assert market.status_code == 200, market.text
    first = market.json()["items"][0]
    assert first["id"] == listing_id
    assert first["is_sponsored"] is True
    assert first["sponsored_until"]

    # Explicit sorts stay organic: sponsorship does not buy "cheapest" or "best rated".
    cheap = client.get("/v1/listings/marketplace/listings", params={"limit": 100, "sort": "price_asc"})
    prices = [Decimal(i["price"]["amount"]) for i in cheap.json()["items"]]
    assert prices == sorted(prices)


def test_extension_chains_after_current_window(client, promo_settings):
    agent_id, _sid, listing_id = _strategy_with_listing(client)
    _fund_agent(client, agent_id)
    first = client.post(f"/v1/listings/{listing_id}/promotions", json={"days": 2}).json()
    second = client.post(f"/v1/listings/{listing_id}/promotions", json={"days": 2})
    assert second.status_code == 201, second.text
    assert second.json()["starts_at"] == first["ends_at"]

    history = client.get(f"/v1/listings/{listing_id}/promotions")
    assert history.status_code == 200, history.text
    assert len(history.json()["items"]) == 2
    assert history.json()["active_until"] == second.json()["ends_at"]


def test_cannot_book_beyond_max_window(client, promo_settings):
    agent_id, _sid, listing_id = _strategy_with_listing(client)
    _fund_agent(client, agent_id, "100000")
    assert client.post(f"/v1/listings/{listing_id}/promotions", json={"days": 20}).status_code == 201
    r = client.post(f"/v1/listings/{listing_id}/promotions", json={"days": 20})
    assert r.status_code == 422, r.text


def test_non_owner_cannot_promote(client, promo_settings):
    _agent_id, _sid, listing_id = _strategy_with_listing(client)
    other = client.post(
        "/v1/auth/users",
        json={"email": f"promo_{uuid.uuid4().hex[:8]}@example.com", "password": "password123", "display_name": "x"},
        headers={"Authorization": ""},
    )
    headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    r = client.post(f"/v1/listings/{listing_id}/promotions", json={"days": 1}, headers=headers)
    assert r.status_code == 403, r.text
    anon = client.post(f"/v1/listings/{listing_id}/promotions", json={"days": 1}, headers={"Authorization": ""})
    assert anon.status_code == 401, anon.text


def test_insufficient_balance_is_402(client, promo_settings, monkeypatch):
    monkeypatch.setenv("LISTING_PROMOTION_DAILY_FEE", "999999999")
    get_settings.cache_clear()
    _agent_id, _sid, listing_id = _strategy_with_listing(client)
    r = client.post(f"/v1/listings/{listing_id}/promotions", json={"days": 1})
    assert r.status_code == 402, r.text


def test_idempotent_purchase_charges_once(client, promo_settings):
    agent_id, _sid, listing_id = _strategy_with_listing(client)
    _fund_agent(client, agent_id)
    before = _agent_balance(client, agent_id)
    key = unique_name("idk_promo")
    a = client.post(f"/v1/listings/{listing_id}/promotions", json={"days": 1}, headers={"Idempotency-Key": key})
    b = client.post(f"/v1/listings/{listing_id}/promotions", json={"days": 1}, headers={"Idempotency-Key": key})
    assert a.status_code == 201 and b.status_code in (200, 201), (a.text, b.text)
    assert a.json()["id"] == b.json()["id"]
    assert _agent_balance(client, agent_id) == before - Decimal(100)


def test_category_slots_are_limited(client, promo_settings, monkeypatch):
    monkeypatch.setenv("LISTING_PROMOTION_SLOTS_PER_CATEGORY", "1")
    get_settings.cache_clear()
    agent_id, sid, listing_id = _strategy_with_listing(client)
    _fund_agent(client, agent_id)
    assert client.post(f"/v1/listings/{listing_id}/promotions", json={"days": 1}).status_code == 201

    # Second listing in the same category (same strategy -> same vertical).
    strat = client.get(f"/v1/strategies/{sid}").json()
    ver = client.post(
        f"/v1/strategies/{sid}/versions",
        json={"semver": "0.2.0", "workflow": {"vertical_id": strat["vertical_id"], "version": "1.0", "steps": [{"id": "s1", "action": "a", "args": {"x": 1}}]}},
    )
    assert ver.status_code == 201, ver.text
    second = client.post(
        "/v1/listings",
        json={
            "strategy_id": sid,
            "strategy_version_id": ver.json()["id"],
            "fee_model": {"type": "one_time", "one_time_price": {"amount": "10", "currency": "VUSD"}},
            "status": "active",
        },
    )
    assert second.status_code == 201, second.text
    r = client.post(f"/v1/listings/{second.json()['id']}/promotions", json={"days": 1})
    assert r.status_code == 409, r.text


def test_idempotency_key_longer_than_column_is_rejected_cleanly(client, promo_settings):
    agent_id, _sid, listing_id = _strategy_with_listing(client)
    _fund_agent(client, agent_id)
    r = client.post(
        f"/v1/listings/{listing_id}/promotions",
        json={"days": 1},
        headers={"Idempotency-Key": "k" * 129},
    )
    assert r.status_code == 422, r.text


@pytest.mark.asyncio
async def test_promotion_and_withdraw_share_account_spend_lock(_db_schema_ready):
    """A second transaction cannot take the spend lock while a debit holds it."""
    import os

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.pool import NullPool

    from app.services.ledger import lock_account_for_spend

    engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
    key = {"k": f"ledger_spend:{uuid.uuid4()}"}
    probe = text("SELECT pg_try_advisory_xact_lock(hashtext(:k))")
    try:
        async with AsyncSession(engine) as holder, AsyncSession(engine) as other:
            await lock_account_for_spend(holder, key["k"].removeprefix("ledger_spend:"))
            assert (await other.execute(probe, key)).scalar_one() is False
            await other.rollback()
            await holder.rollback()  # releases the transaction-scoped lock
            assert (await other.execute(probe, key)).scalar_one() is True
            await other.rollback()
    finally:
        await engine.dispose()
