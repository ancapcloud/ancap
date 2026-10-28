from datetime import date

from fastapi import APIRouter, Query
from sqlalchemy import select, func

from app.api.deps import DbSession
from app.db.models import LeaderboardSnapshot
from app.schemas import LeaderboardEntryPublic


router = APIRouter(prefix="/leaderboards", tags=["Growth Leaderboards"])


@router.get("/{board_type}", response_model=list[LeaderboardEntryPublic])
async def get_leaderboard(
    board_type: str,
    session: DbSession,
    window: str = Query("all"),
    snapshot_date: date | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    d = snapshot_date
    if d is None:
        r = await session.execute(
            select(func.max(LeaderboardSnapshot.snapshot_date)).where(
                LeaderboardSnapshot.board_type == board_type, LeaderboardSnapshot.window == window
            )
        )
        d = r.scalar_one_or_none()
        if d is None:
            return []

    q = (
        select(LeaderboardSnapshot)
        .where(
            LeaderboardSnapshot.board_type == board_type,
            LeaderboardSnapshot.window == window,
            LeaderboardSnapshot.snapshot_date == d,
        )
        .order_by(LeaderboardSnapshot.rank.asc())
        .limit(limit)
    )
    r2 = await session.execute(q)
    rows = r2.scalars().all()
    return [
        LeaderboardEntryPublic(
            rank=int(x.rank),
            subject_id=str(x.subject_id),
            score=str(x.score),
            components=x.components_json or {},
        )
        for x in rows
    ]

