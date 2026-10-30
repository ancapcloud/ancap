"""Confirm ACP payouts for rACP redemptions."""
from __future__ import annotations

import logging
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import RacpRedemption
from app.services.acp_amounts import rpc_amount_units
from app.services.acp_rpc import acp_rpc_headers
from app.services.racp_redeem_watcher import append_transition

logger = logging.getLogger(__name__)


async def _json_rpc(
    client: httpx.AsyncClient,
    rpc_url: str,
    method: str,
    params: dict | None = None,
) -> dict[str, Any]:
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    r = await client.post(rpc_url, json=body, headers=acp_rpc_headers())
    r.raise_for_status()
    return r.json()


async def _payout_units_for_beneficiary(
    client: httpx.AsyncClient,
    rpc_url: str,
    txid: str,
    beneficiary: str,
) -> dict[str, Any] | None:
    normalized = str(txid or "").strip().lower()
    if normalized.startswith("dryrun-"):
        return {"txid": normalized, "payout_units": None, "confirmations": 999, "dry_run": True}
    payload = await _json_rpc(
        client, rpc_url, "getrawtransaction", {"txid": normalized, "verbose": 1}
    )
    if payload.get("error"):
        return None
    result = payload.get("result") or {}
    decoded = result.get("decoded") if isinstance(result, dict) else None
    if not isinstance(decoded, dict):
        return None
    target = beneficiary.strip()
    payout_units = sum(
        rpc_amount_units(vout.get("amount"))
        for vout in (decoded.get("vout") or [])
        if str(vout.get("recipient_address") or "").strip() == target
    )
    return {
        "txid": normalized,
        "payout_units": payout_units,
        "confirmations": int(decoded.get("confirmations") or 0),
    }


async def tick_racp_acp_confirm(session: AsyncSession) -> dict[str, Any]:
    settings = get_settings()
    if not settings.racp_redeem_enabled:
        return {"skipped": True, "reason": "racp_redeem_disabled"}

    rpc = (settings.acp_rpc_url or "").strip()
    if not rpc and not settings.racp_redeem_dry_run:
        return {"skipped": True, "reason": "no_acp_rpc"}

    needed = max(1, int(settings.racp_redeem_acp_confirmations or 1))
    rows = (
        await session.execute(
            select(RacpRedemption)
            .where(
                RacpRedemption.status == "ACP_PAYOUT_SENT",
                RacpRedemption.acp_tx_hash.is_not(None),
            )
            .order_by(RacpRedemption.created_at.asc())
            .limit(50)
        )
    ).scalars().all()

    confirmed = 0
    async with httpx.AsyncClient(timeout=20.0) as client:
        for row in rows:
            txid = str(row.acp_tx_hash or "")
            beneficiary = str(row.user_acp_address or "").strip()
            expected = int(row.amount_acp_smallest or 0)
            if not txid or not beneficiary:
                continue
            if txid.startswith("dryrun-"):
                await append_transition(
                    session,
                    row,
                    "COMPLETED",
                    metadata={"txid": txid, "dry_run": True},
                )
                confirmed += 1
                continue
            if not rpc:
                continue
            try:
                meta = await _payout_units_for_beneficiary(client, rpc, txid, beneficiary)
            except Exception as exc:
                logger.warning("racp acp confirm failed tx=%s err=%s", txid, exc)
                continue
            if not meta:
                continue
            if int(meta.get("payout_units") or 0) != expected:
                continue
            if int(meta.get("confirmations") or 0) < needed:
                continue
            await append_transition(
                session,
                row,
                "COMPLETED",
                metadata={
                    "txid": txid,
                    "confirmations": int(meta.get("confirmations") or 0),
                },
            )
            confirmed += 1

    await session.flush()
    return {"ok": True, "confirmed": confirmed, "considered": len(rows)}
