"""Tests for ROP-04 renewal events API."""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.db.models import RenewalEvent
from app.schemas.renewal_events import RenewalEventCreate, RenewalEventUpdate


@pytest.fixture
def renewal_event_data():
    """Test data for renewal event creation."""
    return RenewalEventCreate(
        project_id="test-project-1",
        client_id="client_123",
        subscription_id="sub_456",
        renewal_type="monthly",
        due_date=datetime.utcnow() + timedelta(days=30),
        amount_due=Decimal("99.99"),
        currency="EUR",
        status="pending",
        metadata={"source": "webhook"},
    )


@pytest.fixture
def renewal_event_update_data():
    """Test data for renewal event update."""
    return RenewalEventUpdate(
        actual_renewal_date=datetime.utcnow(),
        status="paid",
        payment_intent_id="pi_test123",
    )


class TestRenewalEventsAPI:
    """Tests for renewal events API endpoints."""
    
    def test_create_renewal_event(self, client, renewal_event_data):
        """Test creating a new renewal event."""
        response = client.post(
            "/v1/renewal-events/",
            json=renewal_event_data.model_dump(by_alias=True),
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == renewal_event_data.project_id
        assert data["client_id"] == renewal_event_data.client_id
        assert data["renewal_type"] == renewal_event_data.renewal_type
        assert data["amount_due"] == renewal_event_data.amount_due
        assert data["currency"] == renewal_event_data.currency
        assert data["status"] == renewal_event_data.status
    
    def test_get_renewal_event(self, client, renewal_event_data):
        """Test getting a renewal event by ID."""
        # First create an event
        create_response = client.post(
            "/v1/renewal-events/",
            json=renewal_event_data.model_dump(by_alias=True),
        )
        event_id = create_response.json()["id"]
        
        # Then get it
        response = client.get(f"/v1/renewal-events/{event_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == event_id
    
    def test_list_renewal_events(self, client, renewal_event_data):
        """Test listing renewal events."""
        # Create multiple events
        for i in range(3):
            client.post(
                "/v1/renewal-events/",
                json={
                    **renewal_event_data.model_dump(by_alias=True),
                    "project_id": f"test-project-{i}",
                },
            )
        
        # List them
        response = client.get("/v1/renewal-events/")
        
        assert response.status_code == 200
        events = response.json()
        assert len(events) == 3
    
    def test_update_renewal_event(self, client, renewal_event_data, renewal_event_update_data):
        """Test updating a renewal event."""
        # Create an event
        create_response = client.post(
            "/v1/renewal-events/",
            json=renewal_event_data.model_dump(by_alias=True),
        )
        event_id = create_response.json()["id"]
        
        # Update it
        update_response = client.patch(
            f"/v1/renewal-events/{event_id}",
            json=renewal_event_update_data.model_dump(by_alias=True),
        )
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["status"] == renewal_event_update_data.status
    
    def test_delete_renewal_event(self, client, renewal_event_data):
        """Test deleting a renewal event."""
        # Create an event
        create_response = client.post(
            "/v1/renewal-events/",
            json=renewal_event_data.model_dump(by_alias=True),
        )
        event_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/v1/renewal-events/{event_id}")
        
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(f"/v1/renewal-events/{event_id}")
        assert get_response.status_code == 404
