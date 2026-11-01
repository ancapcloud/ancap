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


@pytest.mark.parametrize("changes", [
    {"deposit_trc20_address": "TOther"},
    {"deposit_trc20_address": DEPOSIT.lower()},
    {"tron_txid": "already-used-elsewhere"},
    {"usdt_trc20_amount": Decimal("NaN")},
    {"usdt_trc20_amount": Decimal("25.000001")},
])
def test_match_rejects_wrong_order_address_claim_or_amount(changes):
    transfer = ObservedTronTransfer("new-tx", Decimal("25"), DEPOSIT, 1000)
    assert match_transfer_to_order(transfer, [_order(**changes)], DEPOSIT) is None


def test_existing_txid_does_not_bypass_amount_validation():
    transfer = ObservedTronTransfer("existing", Decimal("1"), DEPOSIT, 1000)
    assert match_transfer_to_order(transfer, [_order(tron_txid="existing")], DEPOSIT) is None


def test_fetch_paginates_confirmed_transfers_with_fixed_filters(monkeypatch):
    import json
    from urllib.parse import urlparse, parse_qs
    from app.services.swap_tron_deposit_watcher import default_transfer_fetcher
    contract = "USDT-contract"
    monkeypatch.setattr("app.services.swap_tron_deposit_watcher.get_settings", lambda: SimpleNamespace(
        tron_grid_api_url="https://example.test", tron_grid_api_key="test-key", usdt_trc20_contract=contract))
    def item(tx):
        return {"transaction_id": tx, "to": DEPOSIT, "value": "25000000", "block_timestamp": 1000,
                "type": "Transfer", "token_info": {"address": contract, "decimals": 6}}
    pages = [{"data": [item("a" * 64)], "meta": {"fingerprint": "next page"}}, {"data": [item("b" * 64)]}]
    requests = []
    def urlopen(req, **_):
        requests.append(req)
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(pages.pop(0)).encode()
        return response
    monkeypatch.setattr("app.services.swap_tron_deposit_watcher._open_provider_request", urlopen)
    out = default_transfer_fetcher(DEPOSIT, 0)
    assert [x.txid for x in out] == ["a" * 64, "b" * 64]
    queries = [parse_qs(urlparse(req.full_url).query) for req in requests]
    assert queries[0]["only_confirmed"] == ["true"]
    fingerprint = queries[1].pop("fingerprint")
    assert fingerprint == ["next page"]
    assert queries[0] == queries[1]


@pytest.mark.parametrize("body", [{"success": False, "data": []}, {"data": [{}]}, {"unexpected": []}])
def test_provider_failure_is_not_an_empty_success(monkeypatch, body):
    import json
    from app.services.swap_tron_deposit_watcher import default_transfer_fetcher
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(body).encode()
    monkeypatch.setattr("app.services.swap_tron_deposit_watcher._open_provider_request", lambda *_a, **_k: response)
    with pytest.raises(RuntimeError):
        default_transfer_fetcher(DEPOSIT, 0)


@pytest.mark.asyncio
async def test_failed_fetch_does_not_advance_checkpoint(monkeypatch):
    settings = SimpleNamespace(ff_swap_deposit_watcher=True, swap_deposit_watcher_mode="shadow",
                               usdt_trc20_deposit_address=DEPOSIT)
    monkeypatch.setattr("app.services.swap_tron_deposit_watcher.get_settings", lambda: settings)
    checkpoint = SimpleNamespace(last_block_height=1234)
    session = AsyncMock()
    session.get.return_value = checkpoint
    def fail(*_):
        raise TimeoutError("remote text")
    out = await tick_swap_tron_deposits(session, fetch_transfers=fail)
    assert out["ok"] is False
    assert checkpoint.last_block_height == 1234
    session.execute.assert_not_awaited()


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
    seen_audit.scalar_one_or_none.return_value = None
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
async def test_tick_pending_review_fails_closed(monkeypatch):
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
    seen_audit.scalar_one_or_none.return_value = None
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
    assert out["ok"] is False
    assert "shadow_only" in out["error"]
    assert order.status == "awaiting_deposit"
    assert order.tron_txid is None
    session.execute.assert_not_awaited()


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
        swap_deposit_watcher_mode="shadow",
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


def test_provider_credentials_cannot_follow_redirects_or_file_urls(monkeypatch):
    import urllib.error
    import urllib.request
    from app.services.swap_tron_deposit_watcher import _open_provider_request
    with pytest.raises(urllib.error.URLError):
        _open_provider_request(urllib.request.Request('file:///etc/passwd'), timeout=1)
    class FakeOpener:
        def open(self, request, timeout):
            return redirect.redirect_request(request,None,302,'Found',{},'https://attacker.invalid')
    redirect = None
    def build_opener(handler):
        nonlocal redirect
        redirect = handler()
        return FakeOpener()
    monkeypatch.setattr(urllib.request,'build_opener',build_opener)
    with pytest.raises(urllib.error.URLError):
        _open_provider_request(urllib.request.Request('https://api.trongrid.io'), timeout=1)
