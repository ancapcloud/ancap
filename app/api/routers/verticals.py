from uuid import UUID

from fastapi import APIRouter, Query, HTTPException

from app.schemas import (
    VerticalProposeRequest,
    VerticalPublic,
    VerticalWithSpec,
    VerticalReviewRequest,
    VerticalStatus,
    Pagination,
)
from app.api.deps import DbSession
from app.db.models import Vertical, VerticalSpec, VerticalStatusEnum
from sqlalchemy import select

router = APIRouter(prefix="/verticals", tags=["Verticals"])


@router.get("", response_model=Pagination[VerticalPublic])
async def list_verticals(
    session: DbSession,
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
):
    q = select(Vertical).order_by(Vertical.created_at.desc()).limit(limit + 1)
    if cursor:
        try:
            q = q.where(Vertical.id < UUID(cursor))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid pagination cursor") from None
    r = await session.execute(q)
    rows = r.scalars().all()
    next_cursor = str(rows[-1].id) if len(rows) > limit else None
    items = rows[:limit]
    return Pagination(
        items=[
            VerticalPublic(
                id=str(v.id),
                name=v.name,
                status=VerticalStatus(v.status.value),
                owner_agent_id=str(v.owner_agent_id) if v.owner_agent_id else None,
                created_at=v.created_at,
            )
            for v in items
        ],
        next_cursor=next_cursor,
    )


@router.post("/propose", response_model=VerticalPublic, status_code=201)
async def propose_vertical(body: VerticalProposeRequest, session: DbSession):
    vertical = Vertical(
        name=body.name,
        status=VerticalStatusEnum.proposed,
        owner_agent_id=None,
    )
    session.add(vertical)
    await session.flush()
    spec = VerticalSpec(vertical_id=vertical.id, spec_json=body.spec.model_dump(mode="json"))
    session.add(spec)
    await session.refresh(vertical)
    return VerticalPublic(
        id=str(vertical.id),
        name=vertical.name,
        status=VerticalStatus(vertical.status.value),
        owner_agent_id=str(vertical.owner_agent_id) if vertical.owner_agent_id else None,
        created_at=vertical.created_at,
    )


@router.get("/{vertical_id}", response_model=VerticalWithSpec)
async def get_vertical(vertical_id: UUID, session: DbSession):
    q = select(Vertical).where(Vertical.id == vertical_id)
    r = await session.execute(q)
    vertical = r.scalar_one_or_none()
    if not vertical:
        raise HTTPException(status_code=404, detail="Vertical not found")
    qs = select(VerticalSpec).where(VerticalSpec.vertical_id == vertical_id).order_by(VerticalSpec.created_at.desc()).limit(1)
    rs = await session.execute(qs)
    spec_row = rs.scalar_one_or_none()
    from app.schemas.verticals import VerticalSpec as VerticalSpecSchema
    spec = VerticalSpecSchema.model_validate(spec_row.spec_json) if spec_row else None
    return VerticalWithSpec(
        id=str(vertical.id),
        name=vertical.name,
        status=VerticalStatus(vertical.status.value),
        owner_agent_id=str(vertical.owner_agent_id) if vertical.owner_agent_id else None,
        created_at=vertical.created_at,
        spec=spec or VerticalSpecSchema(allowed_actions=[], required_resources=[], metrics=[], risk_spec={}),
    )


@router.post("/{vertical_id}/review", response_model=VerticalPublic)
async def review_vertical(vertical_id: UUID, body: VerticalReviewRequest, session: DbSession):
    q = select(Vertical).where(Vertical.id == vertical_id)
    r = await session.execute(q)
    vertical = r.scalar_one_or_none()
    if not vertical:
        raise HTTPException(status_code=404, detail="Vertical not found")
    if body.decision == "approve":
        vertical.status = VerticalStatusEnum.active
    else:
        vertical.status = VerticalStatusEnum.rejected
    await session.flush()
    await session.refresh(vertical)
    return VerticalPublic(
        id=str(vertical.id),
        name=vertical.name,
        status=VerticalStatus(vertical.status.value),
        owner_agent_id=str(vertical.owner_agent_id) if vertical.owner_agent_id else None,
        created_at=vertical.created_at,
    )
