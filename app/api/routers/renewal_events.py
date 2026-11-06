"""ROP-04 admin API: due renewal events and measured renewal cohorts."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.deps import DbSession, require_platform_admin
from app.schemas.renewal_events import (
    RenewalCohortSummary,
    RenewalEventCreate,
    RenewalEventListResponse,
    RenewalEventResponse,
    RenewalEventStatusUpdate,
    RenewalStatus,
)
from app.services import renewal_events as renewal_service

router = APIRouter(prefix="/renewal-events", tags=["renewal-events"])


def _public(row) -> RenewalEventResponse:
    return RenewalEventResponse(
        id=str(row.id),
        project_id=row.project_id,
        client_id=row.client_id,
        subscription_id=row.subscription_id,
        renewal_type=row.renewal_type,
        due_at=row.due_at,
        renewed_at=row.renewed_at,
        amount_due=renewal_service.format_amount(row.amount_due),
        currency=row.currency,
        status=row.status,
        payment_reference=row.payment_reference,
        note=row.note,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.post("", response_model=RenewalEventResponse, status_code=status.HTTP_201_CREATED)
async def create_renewal_event(
    body: RenewalEventCreate,
    session: DbSession,
    response: Response,
    admin_user_id: str = Depends(require_platform_admin),
):
    response.headers["Cache-Control"] = "private, no-store"
    try:
        row = await renewal_service.create_event(
            session,
            project_id=body.project_id,
            client_id=body.client_id,
            subscription_id=body.subscription_id,
            renewal_type=body.renewal_type,
            due_at=body.due_at,
            amount_due=body.amount_due,
            currency=body.currency,
            note=body.note,
            recorded_by_user_id=admin_user_id,
        )
    except renewal_service.RenewalConflict:
        raise HTTPException(status_code=409, detail="Renewal event already recorded for this due date")
    return _public(row)


@router.get("", response_model=RenewalEventListResponse)
async def list_renewal_events(
    session: DbSession,
    response: Response,
    project_id: str | None = Query(None, max_length=255),
    client_id: str | None = Query(None, max_length=255),
    status_filter: RenewalStatus | None = Query(None, alias="status"),
    due_from: datetime | None = None,
    due_to: datetime | None = None,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _admin: str = Depends(require_platform_admin),
):
    response.headers["Cache-Control"] = "private, no-store"
    rows, total = await renewal_service.list_events(
        session,
        project_id=project_id,
        client_id=client_id,
        status=status_filter,
        due_from=due_from,
        due_to=due_to,
        limit=limit,
        offset=offset,
    )
    return RenewalEventListResponse(events=[_public(r) for r in rows], total=total, limit=limit, offset=offset)


@router.get("/cohort", response_model=RenewalCohortSummary)
async def renewal_cohort(
    session: DbSession,
    response: Response,
    due_from: datetime,
    due_to: datetime,
    project_id: str | None = Query(None, max_length=255),
    _admin: str = Depends(require_platform_admin),
):
    response.headers["Cache-Control"] = "private, no-store"
    if due_from.tzinfo is None or due_to.tzinfo is None:
        raise HTTPException(status_code=422, detail="due_from and due_to must include a timezone")
    if due_to <= due_from:
        raise HTTPException(status_code=422, detail="due_to must be after due_from")
    if (due_to - due_from).days > 731:
        raise HTTPException(status_code=422, detail="Cohort window is limited to two years")
    return await renewal_service.cohort_summary(session, due_from=due_from, due_to=due_to, project_id=project_id)


@router.get("/{event_id}", response_model=RenewalEventResponse)
async def get_renewal_event(
    event_id: str,
    session: DbSession,
    response: Response,
    _admin: str = Depends(require_platform_admin),
):
    response.headers["Cache-Control"] = "private, no-store"
    row = await _load(session, event_id)
    return _public(row)


@router.post("/{event_id}/status", response_model=RenewalEventResponse)
async def update_renewal_status(
    event_id: str,
    body: RenewalEventStatusUpdate,
    session: DbSession,
    response: Response,
    _admin: str = Depends(require_platform_admin),
):
    response.headers["Cache-Control"] = "private, no-store"
    _validate_uuid(event_id)
    try:
        row = await renewal_service.update_status(
            session,
            event_id,
            status=body.status,
            renewed_at=body.renewed_at,
            payment_reference=body.payment_reference,
            note=body.note,
        )
    except renewal_service.InvalidTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if row is None:
        raise HTTPException(status_code=404, detail="Renewal event not found")
    return _public(row)


def _validate_uuid(event_id: str) -> None:
    from uuid import UUID

    try:
        UUID(event_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Renewal event not found")


async def _load(session, event_id: str):
    _validate_uuid(event_id)
    row = await renewal_service.get_event(session, event_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Renewal event not found")
    return row
