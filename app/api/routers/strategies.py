from uuid import UUID

from fastapi import APIRouter, Query, HTTPException

from app.schemas import (
    StrategyCreateRequest,
    StrategyPublic,
    StrategyVersionPublic,
    StrategyPublishVersionRequest,
    StrategyStatus,
    Pagination,
)
from app.api.deps import DbSession
from app.db.models import Strategy, StrategyVersion, StrategyStatusEnum
from sqlalchemy import select

router = APIRouter(prefix="/strategies", tags=["Strategies"])


@router.post("", response_model=StrategyPublic, status_code=201)
async def create_strategy(body: StrategyCreateRequest, session: DbSession):
    strategy = Strategy(
        name=body.name,
        vertical_id=UUID(body.vertical_id),
        status=StrategyStatusEnum.draft,
        owner_agent_id=UUID(body.owner_agent_id),
        summary=body.summary,
        description=body.description,
        tags=body.tags,
    )
    session.add(strategy)
    await session.flush()
    await session.refresh(strategy)
    return StrategyPublic(
        id=str(strategy.id),
        name=strategy.name,
        vertical_id=str(strategy.vertical_id),
        status=StrategyStatus(strategy.status.value),
        owner_agent_id=str(strategy.owner_agent_id),
        summary=strategy.summary,
        tags=strategy.tags,
        created_at=strategy.created_at,
    )


@router.get("", response_model=Pagination[StrategyPublic])
async def list_strategies(
    session: DbSession,
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    vertical_id: UUID | None = Query(None),
    owner_agent_id: UUID | None = Query(None),
    status: StrategyStatus | None = Query(None),
    q: str | None = Query(None, max_length=120),
):
    query = select(Strategy).order_by(Strategy.created_at.desc()).limit(limit + 1)
    if cursor:
        try:
            query = query.where(Strategy.id < UUID(cursor))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid pagination cursor") from None
    if vertical_id:
        query = query.where(Strategy.vertical_id == vertical_id)
    if owner_agent_id:
        query = query.where(Strategy.owner_agent_id == owner_agent_id)
    if status:
        query = query.where(Strategy.status == status.value)
    if q:
        query = query.where(Strategy.name.ilike(f"%{q}%"))
    r = await session.execute(query)
    rows = r.scalars().all()
    next_cursor = str(rows[-1].id) if len(rows) > limit else None
    items = rows[:limit]
    return Pagination(
        items=[
            StrategyPublic(
                id=str(s.id),
                name=s.name,
                vertical_id=str(s.vertical_id),
                status=StrategyStatus(s.status.value),
                owner_agent_id=str(s.owner_agent_id),
                summary=s.summary,
                tags=s.tags,
                created_at=s.created_at,
            )
            for s in items
        ],
        next_cursor=next_cursor,
    )


@router.get("/{strategy_id}", response_model=StrategyPublic)
async def get_strategy(strategy_id: UUID, session: DbSession):
    query = select(Strategy).where(Strategy.id == strategy_id)
    r = await session.execute(query)
    strategy = r.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return StrategyPublic(
        id=str(strategy.id),
        name=strategy.name,
        vertical_id=str(strategy.vertical_id),
        status=StrategyStatus(strategy.status.value),
        owner_agent_id=str(strategy.owner_agent_id),
        summary=strategy.summary,
        tags=strategy.tags,
        created_at=strategy.created_at,
    )


@router.get("/{strategy_id}/versions", response_model=Pagination[StrategyVersionPublic])
async def list_versions(
    strategy_id: UUID,
    session: DbSession,
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
):
    query = select(StrategyVersion).where(StrategyVersion.strategy_id == strategy_id).order_by(StrategyVersion.created_at.desc()).limit(limit + 1)
    if cursor:
        try:
            query = query.where(StrategyVersion.id < UUID(cursor))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid pagination cursor") from None
    r = await session.execute(query)
    rows = r.scalars().all()
    next_cursor = str(rows[-1].id) if len(rows) > limit else None
    items = rows[:limit]
    return Pagination(
        items=[
            StrategyVersionPublic(
                id=str(v.id),
                strategy_id=str(v.strategy_id),
                semver=v.semver,
                workflow=v.workflow_json,
                param_schema=v.param_schema,
                changelog=v.changelog,
                created_at=v.created_at,
            )
            for v in items
        ],
        next_cursor=next_cursor,
    )


@router.post("/{strategy_id}/versions", response_model=StrategyVersionPublic, status_code=201)
async def publish_version(strategy_id: UUID, body: StrategyPublishVersionRequest, session: DbSession):
    q = select(Strategy).where(Strategy.id == strategy_id)
    r = await session.execute(q)
    strategy = r.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    workflow_dict = body.workflow.model_dump()
    version = StrategyVersion(
        strategy_id=strategy_id,
        semver=body.semver,
        workflow_json=workflow_dict,
        param_schema=body.param_schema,
        changelog=body.changelog,
        strategy_policy=body.strategy_policy,
    )
    session.add(version)
    await session.flush()
    await session.refresh(version)
    return StrategyVersionPublic(
        id=str(version.id),
        strategy_id=str(version.strategy_id),
        semver=version.semver,
        workflow=version.workflow_json,
        param_schema=version.param_schema,
        changelog=version.changelog,
        created_at=version.created_at,
    )
