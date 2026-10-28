"""Reputation 2.0: GET snapshot+trust, GET events with opaque cursor, POST recompute."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy import select, or_, and_, desc

from app.schemas.reputation import (
    ReputationGetResponse,
    ReputationSnapshotOut,
    TrustScoreOut,
    ReputationEventsListResponse,
    ReputationEventOut,
    ReputationRecomputeRequest,
)
from app.api.deps import DbSession, require_platform_admin
from app.db.models import ReputationSnapshot, TrustScore, ReputationEvent
from app.utils.cursor import CursorKeys, encode_cursor, decode_cursor
from app.config import get_settings

router = APIRouter(prefix="/reputation", tags=["Reputation"])


def _cursor_keys() -> CursorKeys:
    return CursorKeys(secret=get_settings().cursor_secret)


@router.get("", response_model=ReputationGetResponse)
async def get_reputation(
    session: DbSession,
    subject_type: str = Query(..., pattern="^(user|agent|strategy_version|listing|vertical|pool)$"),
    subject_id: str = Query(..., min_length=1, max_length=64),
    window: str = Query("90d", pattern=r"^\d+d$"),
    algo_version: str = Query("rep2-v1"),
    include_trust: bool = Query(True),
    trust_algo_version: str = Query("trust2-v1"),
):
    """Return latest snapshot for (subject, window, algo_version) and optionally trust for same window."""
    subject_uuid = UUID(subject_id) if len(subject_id) == 36 else None
    if subject_uuid is None:
        raise HTTPException(status_code=400, detail="subject_id must be a valid UUID")
    q = (
        select(ReputationSnapshot)
        .where(
            ReputationSnapshot.subject_type == subject_type,
            ReputationSnapshot.subject_id == subject_uuid,
            ReputationSnapshot.window == window,
            ReputationSnapshot.algo_version == algo_version,
        )
        .order_by(desc(ReputationSnapshot.computed_at))
        .limit(1)
    )
    r = await session.execute(q)
    snap = r.scalar_one_or_none()
    if not snap:
        raise HTTPException(status_code=404, detail="Reputation snapshot not found")

    trust_out = None
    if include_trust:
        qt = (
            select(TrustScore)
            .where(
                TrustScore.subject_type == subject_type,
                TrustScore.subject_id == subject_uuid,
                TrustScore.window == window,
                TrustScore.algo_version == trust_algo_version,
            )
            .order_by(desc(TrustScore.computed_at))
            .limit(1)
        )
        rt = await session.execute(qt)
        trust = rt.scalar_one_or_none()
        if trust:
            trust_out = TrustScoreOut(
                subject_type=trust.subject_type,
                subject_id=str(trust.subject_id),
                window=trust.window,
                algo_version=trust.algo_version,
                trust_score=float(trust.trust_score),
                components=trust.components or {},
                inputs_hash=trust.inputs_hash or "",
                computed_at=trust.computed_at,
            )

    return ReputationGetResponse(
        snapshot=ReputationSnapshotOut(
            subject_type=snap.subject_type,
            subject_id=str(snap.subject_id),
            window=snap.window,
            algo_version=snap.algo_version,
            score=float(snap.score),
            components=snap.components or {},
            inputs_hash=snap.inputs_hash or "",
            computed_at=snap.computed_at,
        ),
        trust=trust_out,
    )


@router.get("/events", response_model=ReputationEventsListResponse)
async def list_reputation_events(
    session: DbSession,
    subject_type: str = Query(..., pattern="^(user|agent|strategy_version|listing|vertical|pool)$"),
    subject_id: str = Query(..., min_length=1, max_length=64),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
):
    """Cursor pagination: sort = created_at desc, id desc. cursor = opaque token."""
    keys = _cursor_keys()
    cursor_tuple = decode_cursor(keys, cursor) if cursor else None
    if cursor and cursor_tuple is None:
        raise HTTPException(status_code=400, detail="Invalid cursor")

    subject_uuid = UUID(subject_id) if len(subject_id) == 36 else None
    if subject_uuid is None:
        raise HTTPException(status_code=400, detail="subject_id must be a valid UUID")

    base = select(ReputationEvent).where(
        ReputationEvent.subject_type == subject_type,
        ReputationEvent.subject_id == subject_uuid,
    )
    if cursor_tuple:
        last_created_at, last_id = cursor_tuple
        base = base.where(
            or_(
                ReputationEvent.created_at < last_created_at,
                and_(
                    ReputationEvent.created_at == last_created_at,
                    ReputationEvent.id < UUID(last_id),
                ),
            )
        )

    q = base.order_by(desc(ReputationEvent.created_at), desc(ReputationEvent.id)).limit(limit + 1)
    r = await session.execute(q)
    rows = r.scalars().all()

    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        rows = rows[:limit]
        next_cursor = encode_cursor(keys, last.created_at, str(last.id))

    return ReputationEventsListResponse(
        items=[
            ReputationEventOut(
                id=str(e.id),
                subject_type=e.subject_type,
                subject_id=str(e.subject_id),
                actor_type=e.actor_type,
                actor_id=str(e.actor_id) if e.actor_id else None,
                event_type=e.event_type,
                value=float(e.value) if e.value is not None else 0.0,
                meta=e.meta or {},
                created_at=e.created_at,
            )
            for e in rows
        ],
        next_cursor=next_cursor,
    )


@router.post("/recompute", status_code=202)
async def recompute_reputation(
    body: ReputationRecomputeRequest,
    session: DbSession,
    _admin_user_id: str = Depends(require_platform_admin),
):
    """Trigger recompute for a subject. If subject_type and subject_id provided, runs worker synchronously."""
    from app.jobs.reputation_recompute import recompute_for_subject

    window = body.window or "90d"
    if body.subject_type and body.subject_id:
        try:
            await recompute_for_subject(session, body.subject_type, UUID(body.subject_id), commit=False)
            return {
                "status": "accepted",
                "window": window,
                "subject_type": body.subject_type,
                "subject_id": body.subject_id,
                "message": "Recomputed.",
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Recompute failed: {e!s}")
    return {
        "status": "accepted",
        "window": window,
        "message": "Provide subject_type and subject_id to recompute one subject, or run job in background.",
    }
