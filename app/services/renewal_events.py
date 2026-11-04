"""Service layer for ROP-04 renewal events."""

from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional

from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session

from app.db.models import RenewalEvent


class RenewalEventsService:
    """Service class for renewal event operations (ROP-04)."""

    def __init__(self, db: Session):
        self.db = db

    def create_event(
        self,
        project_id: str,
        client_id: str,
        subscription_id: Optional[str] = None,
        renewal_type: str = "monthly",
        due_date: datetime | None = None,
        amount_due: float | None = None,
        currency: str = "USD",
        status: str = "pending",
        payment_intent_id: str | None = None,
        metadata: dict | None = None,
    ) -> RenewalEvent:
        """Create a new renewal event."""
        if due_date is None:
            due_date = datetime.now(timezone.utc).replace(microsecond=0)
        
        event = RenewalEvent(
            id=uuid4(),
            project_id=project_id,
            client_id=client_id,
            subscription_id=subscription_id,
            renewal_type=renewal_type,
            due_date=due_date,
            actual_renewal_date=None,
            amount_due=amount_due or 0.0,
            currency=currency,
            status=status,
            payment_intent_id=payment_intent_id,
            event_metadata=metadata or {},
        )
        
        self.db.add(event)
        self.db.flush()
        return event

    def get_event(self, event_id: str) -> RenewalEvent | None:
        """Get a renewal event by ID."""
        return self.db.get(RenewalEvent, event_id)

    def list_events(
        self,
        project_id: str | None = None,
        client_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RenewalEvent]:
        """List renewal events with optional filters."""
        query = select(RenewalEvent)
        
        if project_id:
            query = query.where(RenewalEvent.project_id == project_id)
        if client_id:
            query = query.where(RenewalEvent.client_id == client_id)
        if status:
            query = query.where(RenewalEvent.status == status)
        
        return self.db.scalars(query.offset(offset).limit(limit)).all()

    def update_event(
        self,
        event_id: str,
        actual_renewal_date: datetime | None = None,
        status: str | None = None,
        payment_intent_id: str | None = None,
        metadata: dict | None = None,
    ) -> RenewalEvent | None:
        """Update a renewal event."""
        event = self.get_event(event_id)
        if not event:
            return None
        
        if actual_renewal_date is not None:
            event.actual_renewal_date = actual_renewal_date
        if status is not None:
            event.status = status
        if payment_intent_id is not None:
            event.payment_intent_id = payment_intent_id
        if metadata is not None:
            event.event_metadata = metadata
        
        self.db.flush()
        return event

    def delete_event(self, event_id: str) -> bool:
        """Delete a renewal event."""
        count = self.db.query(RenewalEvent).filter(RenewalEvent.id == event_id).delete()
        self.db.commit()
        return count > 0
