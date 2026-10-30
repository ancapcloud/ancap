"""rACP → ACP redemption API — exclusive reserve rail."""
from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession, require_platform_admin
from app.config import get_settings
from app.db.models import RacpRedemption
from app.schemas.racp_redeem import (
    RacpRedeemAdminBindPayoutRequest,
    RacpRedeemAdminNoteRequest,
    RacpRedeemPublicStatus,
    RacpRedemptionPublic,
)
from app.services.racp_redeem_status import (
    get_by_onchain_id,
    get_by_tx,
    list_open,
    public_status,
    serialize_redemption,
)
from app.services.racp_redeem_watcher import append_transition

router = APIRouter(prefix="/racp/redeem", tags=["rACP redeem"])


def _require_operator_secret(settings_secret: str | None, provided: str | None) -> None:
    expected = (settings_secret or "").strip()
    got = (provided or "").strip()
    if not expected or not got or not secrets.compare_digest(expected, got):
        raise HTTPException(status_code=401, detail="Invalid operator secret")


@router.get("/status", response_model=RacpRedeemPublicStatus)
async def redeem_status(session: DbSession):
    return await public_status(session)


@router.get("/by-tx/{tx_hash}", response_model=RacpRedemptionPublic)
async def redeem_by_tx(tx_hash: str, session: DbSession):
    row = await get_by_tx(session, tx_hash)
    if row is None:
        raise HTTPException(status_code=404, detail="Redemption not found for tx")
    return serialize_redemption(row)


@router.get("/{redemption_id}", response_model=RacpRedemptionPublic)
async def redeem_by_id(redemption_id: int, session: DbSession):
    row = await get_by_onchain_id(session, redemption_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Redemption not found")
    return serialize_redemption(row)


@router.get("/admin/open", response_model=list[RacpRedemptionPublic])
async def admin_list_open(
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
    x_racp_operator_secret: str | None = Header(None, alias="X-Racp-Operator-Secret"),
):
    s = get_settings()
    _require_operator_secret(s.racp_operator_secret or s.bridge_operator_secret, x_racp_operator_secret)
    rows = await list_open(session)
    return [serialize_redemption(r) for r in rows]


@router.post("/admin/bind-payout", response_model=RacpRedemptionPublic)
async def admin_bind_payout(
    body: RacpRedeemAdminBindPayoutRequest,
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
    x_racp_operator_secret: str | None = Header(None, alias="X-Racp-Operator-Secret"),
):
    s = get_settings()
    _require_operator_secret(s.racp_operator_secret or s.bridge_operator_secret, x_racp_operator_secret)
    row = await session.get(RacpRedemption, body.redemption_uuid)
    if row is None:
        raise HTTPException(status_code=404, detail="Redemption not found")
    if row.status not in {"BURN_CONFIRMED", "DISPUTED"}:
        raise HTTPException(status_code=409, detail=f"Cannot bind payout from status {row.status}")
    txid = body.acp_tx_hash.strip().lower()
    dup = await session.scalar(select(RacpRedemption.id).where(RacpRedemption.acp_tx_hash == txid))
    if dup is not None and str(dup) != str(row.id):
        raise HTTPException(status_code=409, detail="ACP tx already bound to another redemption")
    row.acp_tx_hash = txid
    await append_transition(session, row, "ACP_PAYOUT_SENT", metadata={"txid": txid, "admin": True})
    await session.flush()
    return serialize_redemption(row)


@router.post("/admin/requeue-payout", response_model=RacpRedemptionPublic)
async def admin_requeue_payout(
    body: RacpRedeemAdminNoteRequest,
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
    x_racp_operator_secret: str | None = Header(None, alias="X-Racp-Operator-Secret"),
):
    s = get_settings()
    _require_operator_secret(s.racp_operator_secret or s.bridge_operator_secret, x_racp_operator_secret)
    row = await session.get(RacpRedemption, body.redemption_uuid)
    if row is None:
        raise HTTPException(status_code=404, detail="Redemption not found")
    if row.status not in {"ACP_PAYOUT_SENT", "DISPUTED"}:
        raise HTTPException(status_code=409, detail=f"Cannot requeue from status {row.status}")
    row.acp_tx_hash = None
    if body.notes:
        row.notes = body.notes
    await append_transition(session, row, "BURN_CONFIRMED", metadata={"requeued": True})
    await session.flush()
    return serialize_redemption(row)


@router.post("/admin/mark-disputed", response_model=RacpRedemptionPublic)
async def admin_mark_disputed(
    body: RacpRedeemAdminNoteRequest,
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
    x_racp_operator_secret: str | None = Header(None, alias="X-Racp-Operator-Secret"),
):
    s = get_settings()
    _require_operator_secret(s.racp_operator_secret or s.bridge_operator_secret, x_racp_operator_secret)
    row = await session.get(RacpRedemption, body.redemption_uuid)
    if row is None:
        raise HTTPException(status_code=404, detail="Redemption not found")
    if body.notes:
        row.notes = body.notes
    await append_transition(session, row, "DISPUTED", metadata={"admin": True})
    await session.flush()
    return serialize_redemption(row)
