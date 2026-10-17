"""USDT TRC-20 deposit watcher for ACP swap desk (shadow-first).

Read-only: observes transfers into the shared deposit address, matches open
``AcpSwapOrder`` rows, and either audits (shadow) or advances to
``pending_review`` (still no ACP payout / no Tron spend keys).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Iterable, Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import AcpSwapOrder, BridgeAuditEvent, BridgeWatcherCheckpoint

logger = logging.getLogger(__name__)

CHECKPOINT_KEY = "tron_usdt_swap"
EVENT_SHADOW = "swap_deposit_shadow"
EVENT_CLAIM = "swap_deposit_pending_review"
AMOUNT_TOLERANCE = Decimal("0.000001")


@dataclass(frozen=True)
class ObservedTronTransfer:
    txid: str
    amount_usdt: Decimal
    to_address: str
    block_timestamp_ms: int
    memo: str | None = None


TransferFetcher = Callable[[str, int], Sequence[ObservedTronTransfer]]


def _to_dec(raw: Any) -> Decimal:
    try:
        return Decimal(str(raw or "0"))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _normalize_addr(addr: str | None) -> str:
    return (addr or "").strip()


def _amounts_match(expected: Decimal, observed: Decimal) -> bool:
    return abs(expected - observed) <= AMOUNT_TOLERANCE


async def _load_checkpoint(session: AsyncSession) -> BridgeWatcherCheckpoint:
    row = await session.get(BridgeWatcherCheckpoint, CHECKPOINT_KEY)
    if row is None:
        row = BridgeWatcherCheckpoint(chain_key=CHECKPOINT_KEY, last_block_height=0)
        session.add(row)
        await session.flush()
    return row


async def _open_awaiting_orders(session: AsyncSession) -> list[AcpSwapOrder]:
    result = await session.execute(
        select(AcpSwapOrder).where(AcpSwapOrder.status.in_(("awaiting_deposit", "pending_review")))
    )
    return list(result.scalars().all())


def match_transfer_to_order(
    transfer: ObservedTronTransfer,
    orders: Iterable[AcpSwapOrder],
    deposit_address: str,
) -> AcpSwapOrder | None:
    """Return a unique open order match by deposit address + amount (+ optional memo)."""
    if _normalize_addr(transfer.to_address).lower() != _normalize_addr(deposit_address).lower():
        return None
    candidates: list[AcpSwapOrder] = []
    for order in orders:
        if order.status not in ("awaiting_deposit", "pending_review"):
            continue
        if order.tron_txid and order.tron_txid.strip().lower() == transfer.txid.strip().lower():
            return order
        if not _amounts_match(_to_dec(order.usdt_trc20_amount), transfer.amount_usdt):
            continue
        if transfer.memo and order.deposit_reference:
            if transfer.memo.strip() != order.deposit_reference.strip():
                continue
        candidates.append(order)
    if len(candidates) == 1:
        return candidates[0]
    return None


async def _already_seen_txid(session: AsyncSession, txid: str) -> bool:
    needle = (txid or "").strip()
    if not needle:
        return False
    claimed = await session.execute(
        select(AcpSwapOrder.id).where(AcpSwapOrder.tron_txid == needle).limit(1)
    )
    if claimed.scalar_one_or_none() is not None:
        return True
    # Portable filter (works on SQLite test DBs without JSONB path ops).
    recent = await session.execute(
        select(BridgeAuditEvent)
        .where(BridgeAuditEvent.event_type.in_((EVENT_SHADOW, EVENT_CLAIM)))
        .order_by(BridgeAuditEvent.created_at.desc())
        .limit(300)
    )
    for ev in recent.scalars().all():
        payload = ev.payload_json or {}
        if str(payload.get("txid") or "").strip() == needle:
            return True
    return False


async def _record_event(
    session: AsyncSession,
    *,
    event_type: str,
    payload: dict[str, Any],
) -> None:
    session.add(
        BridgeAuditEvent(
            id=str(uuid4()),
            operation_id=None,
            event_type=event_type,
            payload_json=payload,
        )
    )


def default_transfer_fetcher(deposit_address: str, since_ms: int) -> list[ObservedTronTransfer]:
    """Fetch TRC-20 USDT transfers via TronGrid when configured; else empty (desk fallback)."""
    import json
    import urllib.error
    import urllib.request

    settings = get_settings()
    base = (getattr(settings, "tron_grid_api_url", None) or "https://api.trongrid.io").rstrip("/")
    api_key = (getattr(settings, "tron_grid_api_key", None) or "").strip()
    usdt_contract = (getattr(settings, "usdt_trc20_contract", None) or "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t").strip()
    if not deposit_address:
        return []

    url = (
        f"{base}/v1/accounts/{deposit_address}/transactions/trc20"
        f"?only_to=true&limit=50&contract_address={usdt_contract}"
        f"&min_timestamp={max(0, since_ms)}"
    )
    headers = {"Accept": "application/json", "User-Agent": "ancap-swap-deposit-watcher/1.0"}
    if api_key:
        headers["TRON-PRO-API-KEY"] = api_key
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("tron_deposit_fetch_failed: %s", exc)
        return []

    out: list[ObservedTronTransfer] = []
    for item in body.get("data") or []:
        try:
            txid = str(item.get("transaction_id") or "").strip()
            to_addr = str(item.get("to") or "").strip()
            raw_value = item.get("value")
            decimals = int(item.get("token_info", {}).get("decimals") or 6)
            amount = _to_dec(raw_value) / (Decimal(10) ** decimals)
            ts = int(item.get("block_timestamp") or 0)
            if not txid or amount <= 0:
                continue
            out.append(
                ObservedTronTransfer(
                    txid=txid,
                    amount_usdt=amount,
                    to_address=to_addr,
                    block_timestamp_ms=ts,
                )
            )
        except (TypeError, ValueError, InvalidOperation):
            continue
    return out


async def tick_swap_tron_deposits(
    session: AsyncSession,
    *,
    fetch_transfers: TransferFetcher | None = None,
) -> dict[str, Any]:
    """Job tick: shadow-match USDT TRC-20 deposits to open swap orders.

    Modes:
    - disabled (ff off): skipped
    - shadow: audit only, never mutate order status
    - pending_review: claim unique match onto order (desk still pays ACP)
    """
    settings = get_settings()
    if not bool(getattr(settings, "ff_swap_deposit_watcher", False)):
        return {"skipped": True, "reason": "ff_swap_deposit_watcher_disabled"}

    mode = (getattr(settings, "swap_deposit_watcher_mode", None) or "shadow").strip().lower()
    if mode not in ("shadow", "pending_review"):
        mode = "shadow"

    deposit_address = _normalize_addr(getattr(settings, "usdt_trc20_deposit_address", None))
    if not deposit_address:
        return {"ok": False, "error": "usdt_trc20_deposit_address_unset"}

    checkpoint = await _load_checkpoint(session)
    since_ms = int(checkpoint.last_block_height or 0)
    fetcher = fetch_transfers or default_transfer_fetcher
    transfers = list(fetcher(deposit_address, since_ms))
    orders = await _open_awaiting_orders(session)

    seen = 0
    matched = 0
    claimed = 0
    ambiguous = 0
    duplicates = 0
    max_ts = since_ms

    for transfer in sorted(transfers, key=lambda t: t.block_timestamp_ms):
        seen += 1
        if transfer.block_timestamp_ms > max_ts:
            max_ts = transfer.block_timestamp_ms
        if await _already_seen_txid(session, transfer.txid):
            duplicates += 1
            continue

        order = match_transfer_to_order(transfer, orders, deposit_address)
        if order is None:
            # Count multi-candidate amount collisions as ambiguous when any amount hits.
            hits = [
                o
                for o in orders
                if _amounts_match(_to_dec(o.usdt_trc20_amount), transfer.amount_usdt)
                and _normalize_addr(o.deposit_trc20_address).lower()
                == _normalize_addr(deposit_address).lower()
            ]
            if len(hits) > 1:
                ambiguous += 1
                await _record_event(
                    session,
                    event_type=EVENT_SHADOW,
                    payload={
                        "txid": transfer.txid,
                        "amount_usdt": format(transfer.amount_usdt, "f"),
                        "matched_order_id": None,
                        "reason": "ambiguous_amount_match",
                        "mode": mode,
                    },
                )
            else:
                await _record_event(
                    session,
                    event_type=EVENT_SHADOW,
                    payload={
                        "txid": transfer.txid,
                        "amount_usdt": format(transfer.amount_usdt, "f"),
                        "matched_order_id": None,
                        "reason": "unmatched",
                        "mode": mode,
                    },
                )
            continue

        matched += 1
        payload = {
            "txid": transfer.txid,
            "amount_usdt": format(transfer.amount_usdt, "f"),
            "matched_order_id": str(order.id),
            "deposit_reference": order.deposit_reference,
            "mode": mode,
            "reason": "matched",
        }

        if mode == "shadow" or order.status == "pending_review":
            await _record_event(session, event_type=EVENT_SHADOW, payload=payload)
            continue

        # pending_review claim — idempotent status flip only; no ACP transfer.
        if order.status == "awaiting_deposit" and not order.tron_txid:
            order.tron_txid = transfer.txid
            order.status = "pending_review"
            order.updated_at = datetime.now(timezone.utc)
            claimed += 1
            await _record_event(session, event_type=EVENT_CLAIM, payload=payload)
        else:
            await _record_event(session, event_type=EVENT_SHADOW, payload={**payload, "reason": "already_claimed"})

    if max_ts > since_ms:
        checkpoint.last_block_height = max_ts
        checkpoint.updated_at = datetime.now(timezone.utc)

    await session.flush()
    return {
        "ok": True,
        "mode": mode,
        "deposit_address": deposit_address,
        "since_ms": since_ms,
        "cursor_ms": int(checkpoint.last_block_height or 0),
        "seen": seen,
        "matched": matched,
        "claimed": claimed,
        "ambiguous": ambiguous,
        "duplicates": duplicates,
        "open_orders": len(orders),
    }
