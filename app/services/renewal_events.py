"""Service layer for ROP-04 renewal events."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy.orm import Session

from app.db.models import RenewalEvent


class RenewalEventsService:
    """Service for managing renewal events (ROP-04)."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_event(
        self,
        project_id: str,
        client_id: str,
        subscription_id: Optional[str] = None,
        renewal_type: str = "monthly",
        due_date: datetime = None,
        amount_due: Decimal = None,
        currency: str = "USD",
        status: str = "pending",
        payment_intent_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> RenewalEvent:
        """Create a new renewal event."""
        if due_date is None:
            due_date = datetime.utcnow()
        if amount_due is None:
            amount_due = Decimal("0")
        
        event = RenewalEvent(
            project_id=project_id,
            client_id=client_id,
            subscription_id=subscription_id,
            renewal_type=renewal_type,
            due_date=due_date,
            actual_renewal_date=None,
            amount_due=amount_due,
            currency=currency,
            status=status,
            payment_intent_id=payment_intent_id,
            metadata=metadata,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def get_event(self, id: str) -> Optional[RenewalEvent]:
        """Get a renewal event by ID."""
        return self.db.query(RenewalEvent).filter(RenewalEvent.id == id).first()
    
    def list_events(
        self,
        project_id: Optional[str] = None,
        client_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[RenewalEvent]:
        """List renewal events with optional filters."""
        query = self.db.query(RenewalEvent)
        
        if project_id:
            query = query.filter(RenewalEvent.project_id == project_id)
        if client_id:
            query = query.filter(RenewalEvent.client_id == client_id)
        if status:
            query = query.filter(RenewalEvent.status == status)
        
        return query.order_by(RenewalEvent.due_date).offset(offset).limit(limit).all()
    
    def update_event(
        self,
        id: str,
        actual_renewal_date: Optional[datetime] = None,
        status: Optional[str] = None,
        payment_intent_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[RenewalEvent]:
        """Update a renewal event."""
        event = self.get_event(id)
        if not event:
            return None
        
        if actual_renewal_date is not None:
            event.actual_renewal_date = actual_renewal_date
        if status is not None:
            event.status = status
        if payment_intent_id is not None:
            event.payment_intent_id = payment_intent_id
        if metadata is not None:
            event.metadata = metadata
        
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def delete_event(self, id: str) -> bool:
        """Delete a renewal event."""
        event = self.get_event(id)
        if not event:
            return False
        self.db.delete(event)
        self.db.commit()
        return True
