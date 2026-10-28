from uuid import UUID

from fastapi import APIRouter, Query, HTTPException

from app.schemas import PoolCreateRequest, PoolPublic, Pagination, PoolStatus
from app.api.deps import DbSession
from app.db.models import Agent, Pool, RiskProfileEnum, PoolStatusEnum
from sqlalchemy import select

router = APIRouter(prefix="/pools", tags=["Pools"])


@router.post("", response_model=PoolPublic, status_code=201)
async def create_pool(body: PoolCreateRequest, session: DbSession):
    owner_agent_id = None
    if body.owner_agent_id:
        try:
            owner_agent_id = UUID(body.owner_agent_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid owner_agent_id") from exc
        owner_agent = await session.get(Agent, owner_agent_id)
        if not owner_agent:
            raise HTTPException(status_code=404, detail="Owner agent not found")
    pool = Pool(
        name=body.name,
        owner_agent_id=owner_agent_id,
        risk_profile=RiskProfileEnum(body.risk_profile),
        status=PoolStatusEnum.active,
        rules=body.rules,
        fee_model=body.fee_model,
    )
    session.add(pool)
    await session.flush()
    await session.refresh(pool)
    return PoolPublic(
        id=str(pool.id),
        name=pool.name,
        owner_agent_id=str(pool.owner_agent_id) if pool.owner_agent_id else None,
        risk_profile=pool.risk_profile.value,
        status=PoolStatus(pool.status.value),
        created_at=pool.created_at,
    )


@router.get("", response_model=Pagination[PoolPublic])
async def list_pools(
    session: DbSession,
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    risk_profile: str | None = Query(None),
    status: PoolStatus | None = Query(None),
):
    q = select(Pool).order_by(Pool.created_at.desc()).limit(limit + 1)
    if cursor:
        try:
            q = q.where(Pool.id < UUID(cursor))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid pagination cursor") from None
    if risk_profile:
        q = q.where(Pool.risk_profile == risk_profile)
    if status:
        q = q.where(Pool.status == status.value)
    r = await session.execute(q)
    rows = r.scalars().all()
    next_cursor = str(rows[-1].id) if len(rows) > limit else None
    items = rows[:limit]
    return Pagination(
        items=[
            PoolPublic(
                id=str(p.id),
                name=p.name,
                owner_agent_id=str(p.owner_agent_id) if p.owner_agent_id else None,
                risk_profile=p.risk_profile.value,
                status=PoolStatus(p.status.value),
                created_at=p.created_at,
            )
            for p in items
        ],
        next_cursor=next_cursor,
    )


@router.get("/{pool_id}", response_model=PoolPublic)
async def get_pool(pool_id: UUID, session: DbSession):
    q = select(Pool).where(Pool.id == pool_id)
    r = await session.execute(q)
    pool = r.scalar_one_or_none()
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    return PoolPublic(
        id=str(pool.id),
        name=pool.name,
        owner_agent_id=str(pool.owner_agent_id) if pool.owner_agent_id else None,
        risk_profile=pool.risk_profile.value,
        status=PoolStatus(pool.status.value),
        created_at=pool.created_at,
    )
