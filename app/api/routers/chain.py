"""L3: On-chain anchoring API."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.api.deps import DbSession, get_agent_id_from_api_key, get_current_user_id
from app.config import get_settings
from app.schemas.chain import AnchorCreateRequest, AnchorPublic
from app.db.models import ChainAnchor
from app.services.chain_anchor import get_anchor_driver
from sqlalchemy import select

router = APIRouter(prefix="/chain", tags=["Chain anchors (L3)"])


async def _require_user_or_agent(
    user_id: Annotated[str | None, Depends(get_current_user_id)],
    agent_id: Annotated[str | None, Depends(get_agent_id_from_api_key)],
) -> str:
    """Anchor writes require an authenticated user or an agent API key."""
    caller = user_id or agent_id
    if not caller:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required (Bearer token or X-API-Key)",
        )
    return caller


@router.post("/anchor", response_model=AnchorPublic, status_code=201)
async def create_anchor(
    body: AnchorCreateRequest,
    session: DbSession,
    caller_id: Annotated[str, Depends(_require_user_or_agent)],
):
    """Submit payload hash for on-chain anchoring. Driver: mock | acp | ethereum | solana (config: chain_anchor_driver + *_rpc_url)."""
    _ = caller_id
    settings = get_settings()
    driver = get_anchor_driver(settings.chain_anchor_driver or "mock")
    if driver is None:
        raise HTTPException(
            status_code=501,
            detail=f"Chain driver '{settings.chain_anchor_driver}' not implemented; use mock, acp, ethereum, or solana",
        )
    try:
        rec = await driver(
            session,
            chain_id=body.chain_id,
            payload_type=body.payload_type,
            payload_hash=body.payload_hash,
            payload_json=body.payload_json,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return AnchorPublic(
        id=str(rec.id),
        chain_id=rec.chain_id,
        tx_hash=rec.tx_hash,
        payload_type=rec.payload_type,
        payload_hash=rec.payload_hash,
        anchored_at=rec.anchored_at,
    )


@router.get("/anchors", response_model=list[AnchorPublic])
async def list_anchors(
    session: DbSession,
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    payload_type: str | None = Query(None),
    chain_id: str | None = Query(None),
):
    q = select(ChainAnchor).order_by(ChainAnchor.created_at.desc()).limit(limit + 1)
    if cursor:
        try:
            q = q.where(ChainAnchor.id < UUID(cursor))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid pagination cursor") from None
    if payload_type:
        q = q.where(ChainAnchor.payload_type == payload_type)
    if chain_id:
        q = q.where(ChainAnchor.chain_id == chain_id)
    r = await session.execute(q)
    rows = r.scalars().all()
    return [
        AnchorPublic(
            id=str(rec.id),
            chain_id=rec.chain_id,
            tx_hash=rec.tx_hash,
            payload_type=rec.payload_type,
            payload_hash=rec.payload_hash,
            anchored_at=rec.anchored_at,
        )
        for rec in rows[:limit]
    ]
