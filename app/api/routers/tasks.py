
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc

from app.api.deps import DbSession, require_auth
from app.db.models import TaskFeedItem
from app.schemas import TaskFeedItemPublic


router = APIRouter(prefix="/tasks", tags=["Growth Tasks"])


@router.get("/feed", response_model=list[TaskFeedItemPublic])
async def task_feed(
    session: DbSession,
    user_id: str = Depends(require_auth),
    limit: int = Query(50, ge=1, le=200),
):
    q = (
        select(TaskFeedItem)
        .where(TaskFeedItem.status == "open")
        .order_by(desc(TaskFeedItem.score), desc(TaskFeedItem.created_at))
        .limit(limit)
    )
    r = await session.execute(q)
    items = []
    for t in r.scalars().all():
        items.append(
            TaskFeedItemPublic(
                id=str(t.id),
                task_type=t.task_type,
                title=t.title,
                description=t.description,
                reward_currency=t.reward_currency,
                reward_amount=str(t.reward_amount_value) if t.reward_amount_value is not None else None,
                status=t.status,
                score=str(t.score),
                created_at=t.created_at,
                expires_at=t.expires_at,
            )
        )
    return items

