"""Swap desk Tron deposit watcher — matching + shadow tick behavior."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.swap_tron_deposit_watcher import (
    ObservedTronTransfer,
    match_transfer_to_order,
    tick_swap_tron_deposits,
)

DEPOSIT = "TNAbqPprJmqRa33UoRvYnUsVfDSgrJc3W1"


def _order(**kwargs):
    defaults = dict(
        id=str(uuid4()),
        status="awaiting_deposit",
        usdt_trc20_amount=Decimal("25"),
        deposit_trc20_address=DEPOSIT,
        deposit_reference="REF1",
        tron_txid=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_match_unique_amount():
    orders = [_order(usdt_trc20_amount=Decimal("10")), _order(usdt_trc20_amount=Decimal("25"))]
    transfer = ObservedTronTransfer(
        txid="tx1",
        amount_usdt=Decimal("25"),
        to_address=DEPOSIT,
        block_timestamp_ms=1000,
    )
    matched = match_transfer_to_order(transfer, orders, DEPOSIT)
    assert matched is not None
    assert matched.usdt_trc20_amount == Decimal("25")


def test_match_ambiguous_amount_returns_none():
    orders = [
        _order(usdt_trc20_amount=Decimal("25"), deposit_reference="A"),
        _order(usdt_trc20_amount=Decimal("25"), deposit_reference="B"),
    ]
    transfer = ObservedTronTransfer(
        txid="tx2",
        amount_usdt=Decimal("25"),
        to_address=DEPOSIT,
        block_timestamp_ms=1000,
    )
    assert match_transfer_to_order(transfer, orders, DEPOSIT) is None


def test_match_memo_disambiguates():
    orders = [
        _order(usdt_trc20_amount=Decimal("25"), deposit_reference="A"),
        _order(usdt_trc20_amount=Decimal("25"), deposit_reference="B"),
    ]
    transfer = ObservedTronTransfer(
        txid="tx3",
        amount_usdt=Decimal("25"),
        to_address=DEPOSIT,
        block_timestamp_ms=1000,
        memo="B",
    )
    matched = match_transfer_to_order(transfer, orders, DEPOSIT)
    assert matched is not None
    assert matched.deposit_reference == "B"


def test_match_wrong_address_ignored():
    orders = [_order()]
    transfer = ObservedTronTransfer(
        txid="tx4",
        amount_usdt=Decimal("25"),
        to_address="TOther",
        block_timestamp_ms=1000,
    )
    assert match_transfer_to_order(transfer, orders, DEPOSIT) is None


@pytest.mark.asyncio
async def test_tick_skipped_when_flag_off(monkeypatch):
    settings = SimpleNamespace(ff_swap_deposit_watcher=False)
    monkeypatch.setattr("app.services.swap_tron_deposit_watcher.get_settings", lambda: settings)
    out = await tick_swap_tron_deposits(AsyncMock())
    assert out["skipped"] is True


@pytest.mark.asyncio
async def test_tick_shadow_does_not_claim(monkeypatch):
    order = _order(usdt_trc20_amount=Decimal("12.5"))
    checkpoint = SimpleNamespace(chain_key="tron_usdt_swap", last_block_height=0, updated_at=None)

    session = AsyncMock()
    session.get = AsyncMock(return_value=checkpoint)
    session.add = MagicMock()
    session.flush = AsyncMock()

    execute_results = []

    # open orders
    open_result = MagicMock()
    open_result.scalars.return_value.all.return_value = [order]
    execute_results.append(open_result)

    # already_seen: no swap order with txid, no audit
    seen_order = MagicMock()
    seen_order.scalar_one_or_none.return_value = None
    execute_results.append(seen_order)
    seen_audit = MagicMock()
    seen_audit.scalars.return_value.all.return_value = []
    execute_results.append(seen_audit)

    session.execute = AsyncMock(side_effect=execute_results)

    settings = SimpleNamespace(
        ff_swap_deposit_watcher=True,
        swap_deposit_watcher_mode="shadow",
        usdt_trc20_deposit_address=DEPOSIT,
    )
    monkeypatch.setattr("app.services.swap_tron_deposit_watcher.get_settings", lambda: settings)

    transfers = [
        ObservedTronTransfer(
            txid="abc123",
            amount_usdt=Decimal("12.5"),
            to_address=DEPOSIT,
            block_timestamp_ms=5000,
        )
    ]
    out = await tick_swap_tron_deposits(session, fetch_transfers=lambda *_: transfers)
    assert out["ok"] is True
    assert out["mode"] == "shadow"
    assert out["matched"] == 1
    assert out["claimed"] == 0
    assert order.status == "awaiting_deposit"
    assert order.tron_txid is None
    assert checkpoint.last_block_height == 5000


@pytest.mark.asyncio
async def test_tick_pending_review_claims_once(monkeypatch):
    order = _order(usdt_trc20_amount=Decimal("7"))
    checkpoint = SimpleNamespace(chain_key="tron_usdt_swap", last_block_height=0, updated_at=None)
    session = AsyncMock()
    session.get = AsyncMock(return_value=checkpoint)
    session.add = MagicMock()
    session.flush = AsyncMock()

    open_result = MagicMock()
    open_result.scalars.return_value.all.return_value = [order]
    seen_order = MagicMock()
    seen_order.scalar_one_or_none.return_value = None
    seen_audit = MagicMock()
    seen_audit.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(side_effect=[open_result, seen_order, seen_audit])

    settings = SimpleNamespace(
        ff_swap_deposit_watcher=True,
        swap_deposit_watcher_mode="pending_review",
        usdt_trc20_deposit_address=DEPOSIT,
    )
    monkeypatch.setattr("app.services.swap_tron_deposit_watcher.get_settings", lambda: settings)

    transfers = [
        ObservedTronTransfer(
            txid="claimme",
            amount_usdt=Decimal("7"),
            to_address=DEPOSIT,
            block_timestamp_ms=9000,
        )
    ]
    out = await tick_swap_tron_deposits(session, fetch_transfers=lambda *_: transfers)
    assert out["claimed"] == 1
    assert order.status == "pending_review"
    assert order.tron_txid == "claimme"


@pytest.mark.asyncio
async def test_tick_duplicate_txid_skipped(monkeypatch):
    order = _order(usdt_trc20_amount=Decimal("3"), tron_txid="dup")
    checkpoint = SimpleNamespace(chain_key="tron_usdt_swap", last_block_height=0, updated_at=None)
    session = AsyncMock()
    session.get = AsyncMock(return_value=checkpoint)
    session.add = MagicMock()
    session.flush = AsyncMock()

    open_result = MagicMock()
    open_result.scalars.return_value.all.return_value = [order]
    seen_order = MagicMock()
    seen_order.scalar_one_or_none.return_value = order.id
    session.execute = AsyncMock(side_effect=[open_result, seen_order])

    settings = SimpleNamespace(
        ff_swap_deposit_watcher=True,
        swap_deposit_watcher_mode="pending_review",
        usdt_trc20_deposit_address=DEPOSIT,
    )
    monkeypatch.setattr("app.services.swap_tron_deposit_watcher.get_settings", lambda: settings)

    transfers = [
        ObservedTronTransfer(
            txid="dup",
            amount_usdt=Decimal("3"),
            to_address=DEPOSIT,
            block_timestamp_ms=100,
        )
    ]
    out = await tick_swap_tron_deposits(session, fetch_transfers=lambda *_: transfers)
    assert out["duplicates"] == 1
    assert out["claimed"] == 0
