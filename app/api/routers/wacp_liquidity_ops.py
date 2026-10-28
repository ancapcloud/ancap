"""Internal operator ledger for wACP V3 liquidity deployments."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.api.routers.bridge_rail import _require_bridge_operator_secret
from app.config import get_settings
from app.db.models import WacpLiquidityStage, WacpTreasuryAllocation, WacpV3Position
from app.schemas.wacp_liquidity import (
    WacpLiquidityStageCreate,
    WacpLiquidityStageResponse,
    WacpTreasuryAllocationCreate,
    WacpTreasuryAllocationResponse,
    WacpV3PositionCreate,
    WacpV3PositionResponse,
)

router = APIRouter(prefix="/internal/wacp-liquidity", tags=["wACP Liquidity Ops"])

def _stage_response(row: WacpLiquidityStage) -> WacpLiquidityStageResponse:
    return WacpLiquidityStageResponse(
        id=str(row.id),
        stage_id=row.stage_id,
        operator_label=row.operator_label,
        mint_wacp_wei=str(row.mint_wacp_wei) if row.mint_wacp_wei is not None else None,
        approval_json=dict(row.approval_json or {}),
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
        allocations=[
            WacpTreasuryAllocationResponse(
                id=str(a.id),
                bucket=a.bucket,
                fraction=float(a.fraction) if a.fraction is not None else None,
                wacp_wei=str(a.wacp_wei) if a.wacp_wei is not None else None,
                usdt_wei=str(a.usdt_wei) if a.usdt_wei is not None else None,
                notes=a.notes,
                created_at=a.created_at,
            )
            for a in row.allocations or []
        ],
        positions=[
            WacpV3PositionResponse(
                id=str(p.id),
                pool_address=p.pool_address,
                position_token_id=p.position_token_id,
                tick_lower=p.tick_lower,
                tick_upper=p.tick_upper,
                amount0_wei=str(p.amount0_wei) if p.amount0_wei is not None else None,
                amount1_wei=str(p.amount1_wei) if p.amount1_wei is not None else None,
                mint_tx_hash=p.mint_tx_hash,
                pool_url=p.pool_url,
                created_at=p.created_at,
            )
            for p in row.positions or []
        ],
    )


async def _get_stage(session: AsyncSession, stage_key: str) -> WacpLiquidityStage:
    stmt = (
        select(WacpLiquidityStage)
        .where(WacpLiquidityStage.stage_id == stage_key)
        .options(selectinload(WacpLiquidityStage.allocations), selectinload(WacpLiquidityStage.positions))
    )
    row = await session.scalar(stmt)
    if row is None:
        raise HTTPException(status_code=404, detail="Stage not found")
    return row


@router.get("/stages/{stage_id}", response_model=WacpLiquidityStageResponse)
async def get_stage(
    stage_id: str,
    session: DbSession,
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
):
    _require_bridge_operator_secret(get_settings().bridge_operator_secret, x_bridge_operator_secret)
    row = await _get_stage(session, stage_id)
    return _stage_response(row)


@router.get("/stages", response_model=list[WacpLiquidityStageResponse])
async def list_stages(
    session: DbSession,
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
    limit: int = 20,
):
    _require_bridge_operator_secret(get_settings().bridge_operator_secret, x_bridge_operator_secret)
    stmt = (
        select(WacpLiquidityStage)
        .order_by(WacpLiquidityStage.created_at.desc())
        .limit(min(limit, 100))
        .options(selectinload(WacpLiquidityStage.allocations), selectinload(WacpLiquidityStage.positions))
    )
    rows = (await session.scalars(stmt)).all()
    return [_stage_response(r) for r in rows]


@router.post("/stages", response_model=WacpLiquidityStageResponse)
async def create_stage(
    body: WacpLiquidityStageCreate,
    session: DbSession,
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
):
    _require_bridge_operator_secret(get_settings().bridge_operator_secret, x_bridge_operator_secret)
    existing = await session.scalar(
        select(WacpLiquidityStage).where(WacpLiquidityStage.stage_id == body.stage_id)
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="stage_id already exists")
    now = datetime.now(UTC)
    row = WacpLiquidityStage(
        stage_id=body.stage_id,
        operator_label=body.operator_label,
        mint_wacp_wei=body.mint_wacp_wei,
        approval_json=body.approval_json,
        status=body.status,
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _stage_response(row)


@router.post("/stages/{stage_id}/allocations", response_model=WacpTreasuryAllocationResponse)
async def add_allocation(
    stage_id: str,
    body: WacpTreasuryAllocationCreate,
    session: DbSession,
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
):
    _require_bridge_operator_secret(get_settings().bridge_operator_secret, x_bridge_operator_secret)
    stage = await _get_stage(session, stage_id)
    row = WacpTreasuryAllocation(
        stage_id=stage.id,
        bucket=body.bucket,
        fraction=body.fraction,
        wacp_wei=body.wacp_wei,
        usdt_wei=body.usdt_wei,
        notes=body.notes,
    )
    session.add(row)
    stage.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(row)
    return WacpTreasuryAllocationResponse(
        id=str(row.id),
        bucket=row.bucket,
        fraction=float(row.fraction) if row.fraction is not None else None,
        wacp_wei=str(row.wacp_wei) if row.wacp_wei is not None else None,
        usdt_wei=str(row.usdt_wei) if row.usdt_wei is not None else None,
        notes=row.notes,
        created_at=row.created_at,
    )


@router.post("/stages/{stage_id}/positions", response_model=WacpV3PositionResponse)
async def record_position(
    stage_id: str,
    body: WacpV3PositionCreate,
    session: DbSession,
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
):
    _require_bridge_operator_secret(get_settings().bridge_operator_secret, x_bridge_operator_secret)
    stage = await _get_stage(session, stage_id)
    row = WacpV3Position(
        stage_id=stage.id,
        pool_address=body.pool_address,
        position_token_id=body.position_token_id,
        tick_lower=body.tick_lower,
        tick_upper=body.tick_upper,
        amount0_wei=body.amount0_wei,
        amount1_wei=body.amount1_wei,
        mint_tx_hash=body.mint_tx_hash,
        pool_url=body.pool_url,
    )
    session.add(row)
    stage.status = "deployed"
    stage.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(row)
    return WacpV3PositionResponse(
        id=str(row.id),
        pool_address=row.pool_address,
        position_token_id=row.position_token_id,
        tick_lower=row.tick_lower,
        tick_upper=row.tick_upper,
        amount0_wei=str(row.amount0_wei) if row.amount0_wei is not None else None,
        amount1_wei=str(row.amount1_wei) if row.amount1_wei is not None else None,
        mint_tx_hash=row.mint_tx_hash,
        pool_url=row.pool_url,
        created_at=row.created_at,
    )
