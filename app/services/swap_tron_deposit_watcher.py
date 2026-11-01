"""USDT TRC-20 deposit watcher for ACP swap desk (shadow-first).

Read-only: observes confirmed transfers into the shared deposit address and
audits candidate matches. Non-shadow mode fails closed pending claim controls.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
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
    return expected.is_finite() and observed.is_finite() and expected > 0 and observed > 0 and expected == observed


async def _load_checkpoint(session: AsyncSession, scope: str) -> BridgeWatcherCheckpoint:
    key = CHECKPOINT_KEY + "_" + hashlib.sha256(scope.encode()).hexdigest()[:16]
    row = await session.get(BridgeWatcherCheckpoint, key)
    if row is None:
        row = BridgeWatcherCheckpoint(chain_key=key, last_block_height=0)
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
    if _normalize_addr(transfer.to_address) != _normalize_addr(deposit_address):
        return None
    candidates: list[AcpSwapOrder] = []
    for order in orders:
        if order.status not in ("awaiting_deposit", "pending_review"):
            continue
        if _normalize_addr(order.deposit_trc20_address) != _normalize_addr(deposit_address):
            continue
        if order.tron_txid and order.tron_txid.strip().lower() != transfer.txid.strip().lower():
            continue
        created = getattr(order, "created_at", None)
        if created is not None:
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if transfer.block_timestamp_ms < int(created.timestamp() * 1000):
                continue
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
    # Query the actual key, not an arbitrary last-300 audit window.
    # These are observation records only; they never authorize live claims.
    observed = await session.execute(
        select(BridgeAuditEvent.id).where(
            BridgeAuditEvent.event_type.in_((EVENT_SHADOW, EVENT_CLAIM)),
            BridgeAuditEvent.payload_json["txid"].as_string() == needle,
        ).limit(1)
    )
    return observed.scalar_one_or_none() is not None


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



def _open_provider_request(request, *, timeout):
    """Allow HTTPS only and never forward provider credentials through redirects."""
    import urllib.error
    import urllib.request
    from urllib.parse import urlsplit
    parsed = urlsplit(request.full_url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise urllib.error.URLError("Invalid HTTPS provider endpoint")

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise urllib.error.URLError("Provider redirects are disabled")

    return urllib.request.build_opener(NoRedirect).open(request, timeout=timeout)


def default_transfer_fetcher(deposit_address: str, since_ms: int) -> list[ObservedTronTransfer]:
    """Read all confirmed pages in a bounded window; incomplete fetches fail closed."""
    import json
    import urllib.error
    import urllib.request

    settings = get_settings()
    base = (getattr(settings, "tron_grid_api_url", None) or "https://api.trongrid.io").rstrip("/")
    api_key = (getattr(settings, "tron_grid_api_key", None) or "").strip()
    usdt_contract = (getattr(settings, "usdt_trc20_contract", None) or "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t").strip()
    if not deposit_address:
        return []

    from urllib.parse import quote, urlencode

    # Fixed query window across pages; never follow provider-supplied URLs with
    # API credentials. A failed/incomplete page must leave the checkpoint intact.
    params = {"only_to": "true", "only_confirmed": "true", "limit": 200,
              "order_by": "block_timestamp,asc", "contract_address": usdt_contract,
              "min_timestamp": max(0, since_ms),
              "max_timestamp": int(datetime.now(timezone.utc).timestamp() * 1000)}
    headers = {"Accept": "application/json", "User-Agent": "ancap-swap-deposit-watcher/1.0"}
    if api_key:
        headers["TRON-PRO-API-KEY"] = api_key
    out: list[ObservedTronTransfer] = []
    fingerprints: set[str] = set()
    deadline = time.monotonic() + 45
    for _ in range(100):
        url = f"{base}/v1/accounts/{quote(deposit_address, safe='')}/transactions/trc20?{urlencode(params)}"
        req = urllib.request.Request(url, headers=headers)
        try:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Tron pagination deadline exceeded")
            with _open_provider_request(req, timeout=min(20, remaining)) as resp:
                raw = resp.read(8_000_001)
                if len(raw) > 8_000_000:
                    raise ValueError("Provider response too large")
                body = json.loads(raw.decode("utf-8"))
            if not isinstance(body, dict) or body.get("success") is False or not isinstance(body.get("data"), list):
                raise ValueError("Invalid provider response")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            # Do not log remote response/error text or credentials.
            raise RuntimeError("Tron deposit fetch failed; checkpoint unchanged") from exc
        for item in body["data"]:
            try:
                token = item.get("token_info") or {}
                # Enforce token identity and decimals even if the provider ignores filters.
                if token.get("address") != usdt_contract or str(token.get("decimals")) != "6":
                    raise ValueError("Unexpected token")
                if item.get("type") != "Transfer":
                    continue
                txid = str(item.get("transaction_id") or "").strip().lower()
                to_addr = str(item.get("to") or "").strip()
                raw_value = str(item.get("value") or "")
                if not raw_value.isascii() or not raw_value.isdigit() or len(raw_value) > 78:
                    raise ValueError("Invalid transfer value")
                if int(raw_value) >= 2**256:
                    raise ValueError("Transfer value exceeds uint256")
                with localcontext() as context:
                    context.prec = 90
                    amount = Decimal(raw_value) / Decimal(1_000_000)
                ts = int(item.get("block_timestamp") or 0)
                if len(txid) != 64 or any(c not in "0123456789abcdef" for c in txid) or not amount.is_finite() or amount <= 0 or ts <= 0:
                    raise ValueError("Invalid transfer")
                if to_addr != deposit_address:
                    continue
                if ts < int(params["min_timestamp"]) or ts > int(params["max_timestamp"]):
                    raise ValueError("Transfer outside query window")
                out.append(ObservedTronTransfer(txid, amount, to_addr, ts))
            except (AttributeError, TypeError, ValueError, InvalidOperation) as exc:
                raise RuntimeError("Invalid Tron transfer response; checkpoint unchanged") from exc
        fingerprint = (body.get("meta") or {}).get("fingerprint")
        if not fingerprint:
            # A full page without continuation is not proof the range is complete.
            if len(body["data"]) >= 200:
                raise RuntimeError("Incomplete Tron pagination; checkpoint unchanged")
            return out
        if not isinstance(fingerprint, str) or fingerprint in fingerprints:
            raise RuntimeError("Invalid Tron pagination; checkpoint unchanged")
        fingerprints.add(fingerprint)
        params["fingerprint"] = fingerprint
    raise RuntimeError("Tron pagination budget exceeded; checkpoint unchanged")


async def tick_swap_tron_deposits(
    session: AsyncSession,
    *,
    fetch_transfers: TransferFetcher | None = None,
) -> dict[str, Any]:
    """Job tick: shadow-match USDT TRC-20 deposits to open swap orders.

    Modes:
    - disabled (ff off): skipped
    - shadow: audit only, never mutate order status
    - all non-shadow modes: rejected until durable claim reconciliation exists
    """
    settings = get_settings()
    if not bool(getattr(settings, "ff_swap_deposit_watcher", False)):
        return {"skipped": True, "reason": "ff_swap_deposit_watcher_disabled"}

    mode = (getattr(settings, "swap_deposit_watcher_mode", None) or "shadow").strip().lower()
    if mode != "shadow":
        # Unique amount on a shared address is not sufficient ownership proof.
        # Live claims require durable event identity, DB uniqueness/locking and
        # independently verified ownership/reconciliation before enablement.
        return {"ok": False, "error": "shadow_only_until_claim_reconciliation_verified"}

    deposit_address = _normalize_addr(getattr(settings, "usdt_trc20_deposit_address", None))
    if not deposit_address:
        return {"ok": False, "error": "usdt_trc20_deposit_address_unset"}

    checkpoint = await _load_checkpoint(session, deposit_address + ":" + str(getattr(settings, "usdt_trc20_contract", "USDT")))
    since_ms = int(checkpoint.last_block_height or 0)
    fetcher = fetch_transfers or default_transfer_fetcher
    # Replay a bounded overlap for provider indexing lag; audit dedupe is persistent.
    try:
        transfers = list(await asyncio.to_thread(fetcher, deposit_address, max(0, since_ms - 86_400_000)))
    except Exception:
        return {"ok": False, "error": "transfer_fetch_failed", "cursor_ms": since_ms}
    orders = await _open_awaiting_orders(session)

    seen = 0
    matched = 0
    claimed = 0
    ambiguous = 0
    duplicates = 0
    max_ts = since_ms
    batch_txids: set[str] = set()

    for transfer in sorted(transfers, key=lambda t: t.block_timestamp_ms):
        seen += 1
        if transfer.block_timestamp_ms > max_ts:
            max_ts = transfer.block_timestamp_ms
        if transfer.txid in batch_txids or await _already_seen_txid(session, transfer.txid):
            duplicates += 1
            continue

        batch_txids.add(transfer.txid)
        order = match_transfer_to_order(transfer, orders, deposit_address)
        if order is None:
            # Count multi-candidate amount collisions as ambiguous when any amount hits.
            hits = [
                o
                for o in orders
                if _amounts_match(_to_dec(o.usdt_trc20_amount), transfer.amount_usdt)
                and _normalize_addr(o.deposit_trc20_address)
                == _normalize_addr(deposit_address)
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

        await _record_event(session, event_type=EVENT_SHADOW, payload=payload)

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
