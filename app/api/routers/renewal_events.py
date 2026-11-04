"""API router for ROP-04 renewal events."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.renewal_events import RenewalEventCreate, RenewalEventUpdate, RenewalEventResponse
from app.services.renewal_events import RenewalEventsService


router = APIRouter(
    tags=["renewal-events"],
)


@router.post(
    "/",
    response_model=RenewalEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a renewal event",
    description="Create a new renewal event for ROP-04 economics and renewal tracking.",
)
async def create_renewal_event(
    event_data: RenewalEventCreate,
    db: Session = Depends(get_db),
):
    """Create a new renewal event."""
    service = RenewalEventsService(db)
    event = service.create_event(
        project_id=event_data.project_id,
        client_id=event_data.client_id,
        subscription_id=event_data.subscription_id,
        renewal_type=event_data.renewal_type,
        due_date=event_data.due_date,
        amount_due=event_data.amount_due,
        currency=event_data.currency,
        status=event_data.status,
        payment_intent_id=event_data.payment_intent_id,
        metadata=event_data.metadata,
    )
    return RenewalEventResponse.model_validate(event)


@router.get(
    "/{event_id}",
    response_model=RenewalEventResponse,
    summary="Get a renewal event",
    description="Retrieve a renewal event by ID.",
)
async def get_renewal_event(
    event_id: str,
    db: Session = Depends(get_db),
):
    """Get a renewal event by ID."""
    service = RenewalEventsService(db)
    event = service.get_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Renewal event {event_id} not found",
        )
    return RenewalEventResponse.model_validate(event)


@router.get(
    "/",
    response_model=list[RenewalEventResponse],
    summary="List renewal events",
    description="List renewal events with optional filters.",
)
async def list_renewal_events(
    project_id: Optional[str] = None,
    client_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List renewal events with optional filters."""
    service = RenewalEventsService(db)
    events = service.list_events(
        project_id=project_id,
        client_id=client_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [RenewalEventResponse.model_validate(e) for e in events]


@router.patch(
    "/{event_id}",
    response_model=RenewalEventResponse,
    summary="Update a renewal event",
    description="Update fields of an existing renewal event.",
)
async def update_renewal_event(
    event_id: str,
    updates: RenewalEventUpdate,
    db: Session = Depends(get_db),
):
    """Update a renewal event."""
    service = RenewalEventsService(db)
    event = service.update_event(
        id=event_id,
        actual_renewal_date=updates.actual_renewal_date,
        status=updates.status,
        payment_intent_id=updates.payment_intent_id,
        metadata=updates.metadata,
    )
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Renewal event {event_id} not found",
        )
    return RenewalEventResponse.model_validate(event)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a renewal event",
    description="Delete a renewal event by ID.",
)
async def delete_renewal_event(
    event_id: str,
    db: Session = Depends(get_db),
):
    """Delete a renewal event."""
    service = RenewalEventsService(db)
    if not service.delete_event(event_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Renewal event {event_id} not found",
        )
    return None
