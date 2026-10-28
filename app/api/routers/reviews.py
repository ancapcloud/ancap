"""L2: Reviews and Disputes API — users, agents, and AI service reviews."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession
from app.db.models import Review, Dispute
from app.schemas.reviews import (
    AiReviewCreateRequest,
    ReviewCreateRequest,
    ReviewPublic,
    DisputeCreateRequest,
    DisputePublic,
    DisputeVerdictRequest,
)
from app.schemas.common import Pagination
from sqlalchemy import select, desc

router = APIRouter(prefix="/reviews", tags=["Reviews"])

# Stable platform AI reviewer identity (not a human account).
AI_REVIEWER_ID = UUID("c3000003-0000-4000-8000-000000000001")

_TARGET_PATTERN = "^(agent|strategy|listing|service|partner|literary_lot)$"
_REVIEWER_PATTERN = "^(agent|user|ai)$"


def _public(row: Review) -> ReviewPublic:
    return ReviewPublic(
        id=str(row.id),
        reviewer_type=row.reviewer_type,
        reviewer_id=str(row.reviewer_id),
        target_type=row.target_type,
        target_id=str(row.target_id),
        weight=float(row.weight),
        rating=int(row.rating) if row.rating is not None else None,
        text=row.text,
        run_id=str(row.run_id) if row.run_id else None,
        created_at=row.created_at,
    )


@router.post("", response_model=ReviewPublic, status_code=201)
async def create_review(body: ReviewCreateRequest, session: DbSession):
    """Create a review (weighted by run_ref and reviewer reputation in future)."""
    try:
        reviewer_id = UUID(body.reviewer_id)
        target_id = UUID(body.target_id)
        run_id = UUID(body.run_id) if body.run_id else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID in reviewer_id, target_id or run_id")
    weight = body.weight
    if body.rating is not None:
        weight = min(1.0, max(0.0, body.rating / 5.0))
    row = Review(
        reviewer_type=body.reviewer_type,
        reviewer_id=reviewer_id,
        target_type=body.target_type,
        target_id=target_id,
        weight=weight,
        rating=body.rating,
        text=body.text,
        run_id=run_id,
    )
    session.add(row)
    await session.flush()
    return _public(row)


@router.post("/ai", response_model=ReviewPublic, status_code=201)
async def create_ai_review(body: AiReviewCreateRequest, session: DbSession):
    """Attach a structured AI reviewer note to any reviewable target (services included)."""
    try:
        target_id = UUID(body.target_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid target_id")
    focus = (body.focus or "").strip()
    stars = "★" * body.rating + "☆" * (5 - body.rating)
    text = (
        f"ANCAP AI review ({stars}). Target={body.target_type}. "
        "Checks: compliance note present, partner handoff clarity, ACP settlement framing, "
        "no medical/investment guarantee claims in catalog copy."
    )
    if focus:
        text = f"{text} Focus: {focus}"
    row = Review(
        reviewer_type="ai",
        reviewer_id=AI_REVIEWER_ID,
        target_type=body.target_type,
        target_id=target_id,
        weight=body.rating / 5.0,
        rating=body.rating,
        text=text[:2000],
        run_id=None,
    )
    session.add(row)
    await session.flush()
    return _public(row)


@router.get("", response_model=Pagination[ReviewPublic])
async def list_reviews(
    session: DbSession,
    target_type: str | None = Query(None, pattern=_TARGET_PATTERN),
    target_id: str | None = None,
    reviewer_type: str | None = Query(None, pattern=_REVIEWER_PATTERN),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = None,
):
    """List reviews, optionally by target and reviewer type (user / agent / ai)."""
    q = select(Review).order_by(desc(Review.created_at)).limit(limit + 1)
    if target_type:
        q = q.where(Review.target_type == target_type)
    if reviewer_type:
        q = q.where(Review.reviewer_type == reviewer_type)
    if target_id:
        try:
            q = q.where(Review.target_id == UUID(target_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid target_id")
    if cursor:
        try:
            q = q.where(Review.id < UUID(cursor))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid pagination cursor") from None
    r = await session.execute(q)
    rows = r.scalars().all()
    next_cursor = str(rows[-1].id) if len(rows) > limit else None
    items = rows[:limit]
    return Pagination(
        items=[_public(x) for x in items],
        next_cursor=next_cursor,
    )


# --- Disputes ---
disputes_router = APIRouter(prefix="/disputes", tags=["Disputes"])


@disputes_router.post("", response_model=DisputePublic, status_code=201)
async def create_dispute(body: DisputeCreateRequest, session: DbSession):
    """Open a dispute."""
    row = Dispute(
        subject=body.subject,
        status="open",
        evidence_refs=body.evidence_refs,
    )
    session.add(row)
    await session.flush()
    return DisputePublic(
        id=str(row.id),
        subject=row.subject,
        status=row.status,
        evidence_refs=row.evidence_refs,
        verdict=row.verdict,
        resolved_at=row.resolved_at,
        created_at=row.created_at,
    )


@disputes_router.get("", response_model=Pagination[DisputePublic])
async def list_disputes(
    session: DbSession,
    status: str | None = Query(None, pattern="^(open|resolved|rejected)$"),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = None,
):
    q = select(Dispute).order_by(desc(Dispute.created_at)).limit(limit + 1)
    if status:
        q = q.where(Dispute.status == status)
    if cursor:
        try:
            q = q.where(Dispute.id < UUID(cursor))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid pagination cursor") from None
    r = await session.execute(q)
    rows = r.scalars().all()
    next_cursor = str(rows[-1].id) if len(rows) > limit else None
    items = rows[:limit]
    return Pagination(
        items=[
            DisputePublic(
                id=str(x.id),
                subject=x.subject,
                status=x.status,
                evidence_refs=x.evidence_refs,
                verdict=x.verdict,
                resolved_at=x.resolved_at,
                created_at=x.created_at,
            )
            for x in items
        ],
        next_cursor=next_cursor,
    )


@disputes_router.get("/{dispute_id}", response_model=DisputePublic)
async def get_dispute(dispute_id: UUID, session: DbSession):
    d = await session.get(Dispute, dispute_id)
    if not d:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return DisputePublic(
        id=str(d.id),
        subject=d.subject,
        status=d.status,
        evidence_refs=d.evidence_refs,
        verdict=d.verdict,
        resolved_at=d.resolved_at,
        created_at=d.created_at,
    )


@disputes_router.post("/{dispute_id}/verdict", response_model=DisputePublic)
async def set_dispute_verdict(dispute_id: UUID, body: DisputeVerdictRequest, session: DbSession):
    """Set verdict and resolve/reject dispute."""
    from datetime import datetime, timezone

    d = await session.get(Dispute, dispute_id)
    if not d:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if d.status != "open":
        raise HTTPException(status_code=400, detail="Dispute already resolved or rejected")
    d.verdict = body.verdict
    d.status = body.status
    d.resolved_at = datetime.now(timezone.utc)
    return DisputePublic(
        id=str(d.id),
        subject=d.subject,
        status=d.status,
        evidence_refs=d.evidence_refs,
        verdict=d.verdict,
        resolved_at=d.resolved_at,
        created_at=d.created_at,
    )
