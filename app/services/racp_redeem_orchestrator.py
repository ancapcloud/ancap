"""Payout ACP from exclusive rACP reserve after burn confirmation."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import RacpRedemption, RacpRedemptionTransition
from app.services.racp_decimal import acp_smallest_to_decimal_str
from app.services.racp_redeem_watcher import append_transition

logger = logging.getLogger(__name__)


def _load_racp_reserve_signer() -> tuple[list[str], str]:
    """Load exclusive rACP reserve keystore — never bridge ACP_HOT_* material."""
    from app.api.routers.wallet_acp import _run_walletd

    settings = get_settings()
    expected = (settings.racp_reserve_acp_address or "").strip()
    if not expected:
        raise RuntimeError("RACP_RESERVE_ACP_ADDRESS is not configured")

    path = Path((settings.racp_reserve_keystore_file or "").strip())
    if not path.is_file():
        raise RuntimeError(f"rACP reserve keystore missing: {path}")
    keystore_json = path.read_text(encoding="utf-8").strip()
    if not keystore_json:
        raise RuntimeError("rACP reserve keystore file is empty")

    derived = _run_walletd(["address", "--keystore-json", keystore_json], timeout_s=60)
    address = str(derived.get("address") or "").strip()
    if address != expected:
        raise RuntimeError(
            f"rACP reserve keystore derives {address or 'empty'}, expected {expected}"
        )
    return (["--keystore-json", keystore_json], address)


def _reserve_transfer(acp_address: str, acp_smallest: int) -> dict[str, Any]:
    from app.api.routers.wallet_acp import _require_acp_rpc_url, _run_walletd

    settings = get_settings()
    if settings.racp_redeem_dry_run:
        return {"txid": f"dryrun-racp-{uuid4().hex[:16]}", "dry_run": True}

    signer_args, from_address = _load_racp_reserve_signer()
    rpc_url = _require_acp_rpc_url()
    transfer = _run_walletd(
        [
            "transfer",
            "--rpc",
            rpc_url,
            *signer_args,
            "--to",
            acp_address,
            "--amount-acp",
            acp_smallest_to_decimal_str(acp_smallest),
        ],
        timeout_s=180,
    )
    txid = str(transfer.get("txid") or "").strip()
    if not txid:
        raise RuntimeError(f"rACP reserve transfer returned no txid from {from_address}")
    return transfer


async def tick_racp_orchestrator(session: AsyncSession) -> dict[str, Any]:
    settings = get_settings()
    if not settings.racp_redeem_enabled:
        return {"skipped": True, "reason": "racp_redeem_disabled"}
    if settings.racp_redeem_paused:
        return {"skipped": True, "reason": "racp_redeem_paused"}

    rows = (
        await session.execute(
            select(RacpRedemption)
            .where(
                RacpRedemption.status == "BURN_CONFIRMED",
                RacpRedemption.acp_tx_hash.is_(None),
            )
            .order_by(RacpRedemption.created_at.asc())
            .limit(25)
        )
    ).scalars().all()

    paid = 0
    errors: list[str] = []
    for row in rows:
        try:
            result = _reserve_transfer(
                str(row.user_acp_address),
                int(row.amount_acp_smallest or 0),
            )
            txid = str(result.get("txid") or "").strip()
            if not txid:
                raise RuntimeError("empty payout txid")
            row.acp_tx_hash = txid
            await append_transition(
                session,
                row,
                "ACP_PAYOUT_SENT",
                metadata={"txid": txid, "dry_run": bool(result.get("dry_run"))},
            )
            paid += 1
        except Exception as exc:
            msg = f"{row.id}:{type(exc).__name__}:{exc}"
            errors.append(msg[:200])
            logger.warning("racp payout failed redemption=%s err=%s", row.id, exc)
            session.add(
                RacpRedemptionTransition(
                    id=str(uuid4()),
                    redemption_id=row.id,
                    from_status=row.status,
                    to_status=row.status,
                    metadata_json={"event": "payout_error", "error": str(exc)[:300]},
                )
            )

    await session.flush()
    out: dict[str, Any] = {"ok": not errors, "paid": paid, "considered": len(rows)}
    if errors:
        out["errors"] = errors[:5]
    return out
