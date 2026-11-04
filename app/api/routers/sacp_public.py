"""Public + intent sACP HTTP surface — docs/STABLECOIN_SACP_SPEC.md."""

from __future__ import annotations

import hmac

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db
from app.schemas.sacp import (
    SacpAdminBindRequest,
    SacpMintIntentRequest,
    SacpOperationPublic,
    SacpPublicStatusResponse,
    SacpRedeemIntentRequest,
    SacpReserveProofResponse,
    SacpSnapshotRequest,
)
from app.services import sacp as sacp_svc

router = APIRouter(prefix="/sacp", tags=["sACP"])


def _require_operator(secret: str | None) -> None:
    expected = (get_settings().bridge_operator_secret or "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Operator secret not configured")
    if not secret or not hmac.compare_digest(secret.strip().encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid operator secret")


@router.get("/status", response_model=SacpPublicStatusResponse)
async def status():
    return SacpPublicStatusResponse(**sacp_svc.public_status())


@router.get("/reserve-proof", response_model=SacpReserveProofResponse)
async def reserve_proof(session: AsyncSession = Depends(get_db)):
    return SacpReserveProofResponse(**(await sacp_svc.reserve_proof(session)))


@router.post("/intents/mint", response_model=SacpOperationPublic)
async def create_mint_intent(body: SacpMintIntentRequest, session: AsyncSession = Depends(get_db)):
    op = await sacp_svc.create_mint_intent(
        session,
        acp_amount=body.acp_amount,
        user_bsc_address=body.user_bsc_address,
        correlation_id=body.correlation_id,
    )
    await session.commit()
    return SacpOperationPublic(**sacp_svc.serialize_operation(op))


@router.post("/intents/redeem", response_model=SacpOperationPublic)
async def create_redeem_intent(body: SacpRedeemIntentRequest, session: AsyncSession = Depends(get_db)):
    op = await sacp_svc.create_redeem_intent(
        session,
        sacp_amount=body.sacp_amount,
        user_acp_address=body.user_acp_address,
        correlation_id=body.correlation_id,
    )
    await session.commit()
    return SacpOperationPublic(**sacp_svc.serialize_operation(op))


@router.get("/intents/{operation_id}", response_model=SacpOperationPublic)
async def get_intent(operation_id: str, session: AsyncSession = Depends(get_db)):
    op = await sacp_svc.get_operation(session, operation_id)
    return SacpOperationPublic(**sacp_svc.serialize_operation(op))


@router.post("/admin/intents/{operation_id}/bind", response_model=SacpOperationPublic)
async def admin_bind(
    operation_id: str,
    body: SacpAdminBindRequest,
    session: AsyncSession = Depends(get_db),
    x_bridge_operator_secret: str | None = Header(default=None, alias="X-Bridge-Operator-Secret"),
):
    _require_operator(x_bridge_operator_secret)
    op = await sacp_svc.admin_bind(
        session,
        operation_id,
        acp_tx_hash=body.acp_tx_hash,
        bsc_tx_hash=body.bsc_tx_hash,
        collateral_ref_hex=body.collateral_ref_hex,
        note=body.note,
    )
    await session.commit()
    return SacpOperationPublic(**sacp_svc.serialize_operation(op))


@router.post("/admin/snapshots", response_model=SacpReserveProofResponse)
async def admin_snapshot(
    body: SacpSnapshotRequest,
    session: AsyncSession = Depends(get_db),
    x_bridge_operator_secret: str | None = Header(default=None, alias="X-Bridge-Operator-Secret"),
):
    _require_operator(x_bridge_operator_secret)
    await sacp_svc.record_snapshot(
        session,
        reserve_balance_acp_smallest=body.reserve_balance_acp_smallest,
        sacp_total_supply_wei=body.sacp_total_supply_wei,
        notes=body.notes or ["admin snapshot"],
    )
    await session.commit()
    return SacpReserveProofResponse(**(await sacp_svc.reserve_proof(session)))
