"""L2: Funds and allocations API."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession
from app.db.models import Fund, FundAllocation, Pool, Evaluation
from app.schemas.funds import (
    FundCreateRequest,
    FundPublic,
    FundAllocationCreateRequest,
    FundAllocationPublic,
    FundPerformanceResponse,
    FundPerformanceItem,
)
from app.schemas.common import Pagination
from sqlalchemy import select, desc

router = APIRouter(prefix="/funds", tags=["Funds"])


@router.post("", response_model=FundPublic, status_code=201)
async def create_fund(body: FundCreateRequest, session: DbSession):
    """Create a fund (portfolio linked to a pool)."""
    pool = await session.get(Pool, UUID(body.pool_id))
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    owner_id = UUID(body.owner_agent_id) if body.owner_agent_id else None
    row = Fund(
        name=body.name,
        owner_agent_id=owner_id,
        pool_id=pool.id,
    )
    session.add(row)
    await session.flush()
    return FundPublic(
        id=str(row.id),
        name=row.name,
        owner_agent_id=str(row.owner_agent_id) if row.owner_agent_id else None,
        pool_id=str(row.pool_id),
        created_at=row.created_at,
    )


@router.get("", response_model=Pagination[FundPublic])
async def list_funds(
    session: DbSession,
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = None,
):
    q = select(Fund).order_by(desc(Fund.created_at)).limit(limit + 1)
    if cursor:
        try:
            q = q.where(Fund.id < UUID(cursor))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid pagination cursor") from None
    r = await session.execute(q)
    rows = r.scalars().all()
    next_cursor = str(rows[-1].id) if len(rows) > limit else None
    items = rows[:limit]
    return Pagination(
        items=[
            FundPublic(
                id=str(x.id),
                name=x.name,
                owner_agent_id=str(x.owner_agent_id) if x.owner_agent_id else None,
                pool_id=str(x.pool_id),
                created_at=x.created_at,
            )
            for x in items
        ],
        next_cursor=next_cursor,
    )


@router.get("/{fund_id}", response_model=FundPublic)
async def get_fund(fund_id: UUID, session: DbSession):
    f = await session.get(Fund, fund_id)
    if not f:
        raise HTTPException(status_code=404, detail="Fund not found")
    return FundPublic(
        id=str(f.id),
        name=f.name,
        owner_agent_id=str(f.owner_agent_id) if f.owner_agent_id else None,
        pool_id=str(f.pool_id),
        created_at=f.created_at,
    )


@router.post("/{fund_id}/allocate", response_model=FundAllocationPublic, status_code=201)
async def add_allocation(fund_id: UUID, body: FundAllocationCreateRequest, session: DbSession):
    """Add or update allocation of a strategy version in the fund (weight 0..1)."""
    fund = await session.get(Fund, fund_id)
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    try:
        sv_id = UUID(body.strategy_version_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid strategy_version_id")
    # Optional: check strategy_version exists
    from app.db.models import StrategyVersion
    sv = await session.get(StrategyVersion, sv_id)
    if not sv:
        raise HTTPException(status_code=404, detail="Strategy version not found")
    row = FundAllocation(
        fund_id=fund_id,
        strategy_version_id=sv_id,
        weight=body.weight,
    )
    session.add(row)
    await session.flush()
    return FundAllocationPublic(
        id=str(row.id),
        fund_id=str(row.fund_id),
        strategy_version_id=str(row.strategy_version_id),
        weight=float(row.weight),
        created_at=row.created_at,
    )


@router.get("/{fund_id}/performance", response_model=FundPerformanceResponse)
async def get_fund_performance(fund_id: UUID, session: DbSession):
    """Return fund allocations with evaluation summary per strategy version."""
    fund = await session.get(Fund, fund_id)
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    q = select(FundAllocation).where(FundAllocation.fund_id == fund_id).order_by(FundAllocation.created_at.desc())
    r = await session.execute(q)
    allocs = r.scalars().all()
    eval_summary = []
    for a in allocs:
        eq = select(Evaluation).where(Evaluation.strategy_version_id == a.strategy_version_id).limit(1)
        er = await session.execute(eq)
        ev = er.scalar_one_or_none()
        eval_summary.append(
            FundPerformanceItem(
                strategy_version_id=str(a.strategy_version_id),
                weight=float(a.weight),
                score=float(ev.score) if ev else None,
                sample_size=ev.sample_size if ev else None,
            )
        )
    return FundPerformanceResponse(
        fund_id=str(fund_id),
        allocations=[
            FundAllocationPublic(
                id=str(x.id),
                fund_id=str(x.fund_id),
                strategy_version_id=str(x.strategy_version_id),
                weight=float(x.weight),
                created_at=x.created_at,
            )
            for x in allocs
        ],
        evaluation_summary=eval_summary,
    )
