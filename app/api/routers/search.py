from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc, text

from app.api.deps import DbSession
from app.db.models import Agent, Strategy, WorkflowRunRecord, Listing


router = APIRouter(prefix="/search", tags=["Search"])


class SearchResultItem(BaseModel):
    type: str
    id: str
    title: str
    slug: str | None = None
    description: str | None = None
    category: str | None = None
    status: str | None = None
    owner_user_id: str | None = None
    created_at: str | None = None
    rank: float = 0.0


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    total: int
    by_type: dict[str, int]


def _fts_sanitize(query: str) -> str:
    import re
    sanitized = re.sub(r"[():&|!<>'\"]", " ", query)
    sanitized = " ".join(sanitized.split())
    return sanitized


async def _search_agents(session: DbSession, query: str, limit: int, offset: int) -> list:
    safe_q = _fts_sanitize(query)
    try:
        stmt = (
            select(Agent, func.ts_rank(Agent.search_vector, func.to_tsquery("english", safe_q)).label("rank"))
            .where(Agent.search_vector.op("@@")(func.plainto_tsquery("english", safe_q)))
            .order_by(desc(text("rank")))
            .limit(limit)
            .offset(offset)
        )
        r = await session.execute(stmt)
        return list(r.all())
    except Exception:
        stmt = (
            select(Agent, text("0 as rank"))
            .where(Agent.display_name.ilike(f"%{safe_q}%"))
            .limit(limit)
            .offset(offset)
        )
        r = await session.execute(stmt)
        return list(r.all())


async def _search_strategies(session: DbSession, query: str, limit: int, offset: int) -> list:
    safe_q = _fts_sanitize(query)
    try:
        stmt = (
            select(Strategy, func.ts_rank(Strategy.search_vector, func.to_tsquery("english", safe_q)).label("rank"))
            .where(Strategy.search_vector.op("@@")(func.plainto_tsquery("english", safe_q)))
            .order_by(desc(text("rank")))
            .limit(limit)
            .offset(offset)
        )
        r = await session.execute(stmt)
        return list(r.all())
    except Exception:
        stmt = (
            select(Strategy, text("0 as rank"))
            .where(Strategy.name.ilike(f"%{safe_q}%"))
            .limit(limit)
            .offset(offset)
        )
        r = await session.execute(stmt)
        return list(r.all())


async def _search_workflow_runs(session: DbSession, query: str, limit: int, offset: int) -> list:
    safe_q = _fts_sanitize(query)
    try:
        stmt = (
            select(WorkflowRunRecord, func.ts_rank(WorkflowRunRecord.search_vector, func.to_tsquery("english", safe_q)).label("rank"))
            .where(WorkflowRunRecord.search_vector.op("@@")(func.plainto_tsquery("english", safe_q)))
            .order_by(desc(text("rank")))
            .limit(limit)
            .offset(offset)
        )
        r = await session.execute(stmt)
        return list(r.all())
    except Exception:
        stmt = (
            select(WorkflowRunRecord, text("0 as rank"))
            .where(WorkflowRunRecord.title.ilike(f"%{safe_q}%"))
            .limit(limit)
            .offset(offset)
        )
        r = await session.execute(stmt)
        return list(r.all())


async def _search_listings(session: DbSession, query: str, limit: int, offset: int) -> list:
    safe_q = _fts_sanitize(query)
    try:
        # Listings don't have search_vector; join with Strategy
        stmt = (
            select(Listing, Strategy, func.ts_rank(Strategy.search_vector, func.to_tsquery("english", safe_q)).label("rank"))
            .join(Strategy, Listing.strategy_id == Strategy.id)
            .where(Strategy.search_vector.op("@@")(func.plainto_tsquery("english", safe_q)))
            .order_by(desc(text("rank")))
            .limit(limit)
            .offset(offset)
        )
        r = await session.execute(stmt)
        return list(r.all())
    except Exception:
        stmt = (
            select(Listing, Strategy, text("0 as rank"))
            .join(Strategy, Listing.strategy_id == Strategy.id)
            .where(Strategy.name.ilike(f"%{safe_q}%"))
            .limit(limit)
            .offset(offset)
        )
        r = await session.execute(stmt)
        return list(r.all())


def _agent_result(row) -> SearchResultItem:
    agent, rank = row
    return SearchResultItem(
        type="agent",
        id=str(agent.id),
        title=agent.display_name or "",
        slug=None,
        description=None,
        category=None,
        status=agent.status.value if agent.status else None,
        owner_user_id=str(agent.owner_user_id) if agent.owner_user_id else None,
        created_at=agent.created_at.isoformat() if agent.created_at else None,
        rank=float(rank) if rank else 0.0,
    )


def _strategy_result(row) -> SearchResultItem:
    strategy, rank = row
    return SearchResultItem(
        type="strategy",
        id=str(strategy.id),
        title=strategy.name or "",
        slug=strategy.name.lower().replace(" ", "-") if strategy.name else None,
        description=strategy.description if strategy.description else None,
        category=None,
        status=strategy.status.value if strategy.status else None,
        owner_user_id=None,
        created_at=strategy.created_at.isoformat() if strategy.created_at else None,
        rank=float(rank) if rank else 0.0,
    )


def _workflow_result(row) -> SearchResultItem:
    wf, rank = row
    return SearchResultItem(
        type="workflow",
        id=str(wf.id),
        title=wf.title or "",
        slug=wf.workflow_slug if hasattr(wf, "workflow_slug") else None,
        description=None,
        category=wf.category if hasattr(wf, "category") else None,
        status=wf.status if hasattr(wf, "status") else None,
        owner_user_id=str(wf.owner_user_id) if wf.owner_user_id else None,
        created_at=wf.created_at.isoformat() if wf.created_at else None,
        rank=float(rank) if rank else 0.0,
    )


def _listing_result(row) -> SearchResultItem:
    listing, strategy, rank = row
    return SearchResultItem(
        type="listing",
        id=str(listing.id),
        title=strategy.name if strategy else "",
        slug=strategy.name.lower().replace(" ", "-") if strategy and strategy.name else None,
        description=strategy.description if strategy and strategy.description else None,
        category=None,
        status=listing.status.value if listing.status else None,
        owner_user_id=None,
        created_at=listing.created_at.isoformat() if listing.created_at else None,
        rank=float(rank) if rank else 0.0,
    )


@router.get("", response_model=SearchResponse)
async def search_all(
    session: DbSession,
    q: str = Query(..., min_length=1, max_length=200),
    type: str | None = Query(default=None, description="agent, strategy, workflow, listing"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Full-text search across agents, strategies, workflow runs, and listings.

    Requires migration 048_add_search_vectors. Falls back to ILIKE if FTS
    columns are not yet available.
    """
    results: list[SearchResultItem] = []
    by_type: dict[str, int] = {}

    if type is None or type == "agent":
        rows = await _search_agents(session, q, limit, offset)
        items = [_agent_result(r) for r in rows]
        results.extend(items)
        by_type["agent"] = len(items)

    if type is None or type == "strategy":
        rows = await _search_strategies(session, q, limit, offset)
        items = [_strategy_result(r) for r in rows]
        results.extend(items)
        by_type["strategy"] = len(items)

    if type is None or type == "workflow":
        rows = await _search_workflow_runs(session, q, limit, offset)
        items = [_workflow_result(r) for r in rows]
        results.extend(items)
        by_type["workflow"] = len(items)

    if type is None or type == "listing":
        rows = await _search_listings(session, q, limit, offset)
        items = [_listing_result(r) for r in rows]
        results.extend(items)
        by_type["listing"] = len(items)

    results.sort(key=lambda x: x.rank, reverse=True)
    total = sum(by_type.values())

    return SearchResponse(query=q, results=results, total=total, by_type=by_type)
