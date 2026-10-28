from fastapi import HTTPException
from uuid import UUID

from fastapi import APIRouter, Query

from app.schemas import AccessGrantPublic, Pagination, AccessScope
from app.api.deps import DbSession
from app.db.models import AccessGrant
from sqlalchemy import select

router = APIRouter(prefix="/access", tags=["Access"])


@router.get("/grants", response_model=Pagination[AccessGrantPublic])
async def list_grants(
    session: DbSession,
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    grantee_type: str | None = Query(None),
    grantee_id: UUID | None = Query(None),
):
    q = select(AccessGrant).order_by(AccessGrant.created_at.desc()).limit(limit + 1)
    if cursor:
        try:
            q = q.where(AccessGrant.id < UUID(cursor))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid pagination cursor") from None
    if grantee_type:
        q = q.where(AccessGrant.grantee_type == grantee_type)
    if grantee_id:
        q = q.where(AccessGrant.grantee_id == grantee_id)
    r = await session.execute(q)
    rows = r.scalars().all()
    next_cursor = str(rows[-1].id) if len(rows) > limit else None
    items = rows[:limit]
    return Pagination(
        items=[
            AccessGrantPublic(
                id=str(g.id),
                strategy_id=str(g.strategy_id),
                grantee_type=g.grantee_type,
                grantee_id=str(g.grantee_id),
                scope=AccessScope(g.scope.value),
                expires_at=g.expires_at,
                created_at=g.created_at,
            )
            for g in items
        ],
        next_cursor=next_cursor,
    )
