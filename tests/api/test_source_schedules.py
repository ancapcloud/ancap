"""Tests for source schedules API (ROP-03)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.database import engine, Base
from app.db.models import User, SourceSchedule
from app.db.session import get_db
from app.main import app


@pytest.fixture(scope="module")
def client(db_session):
    """Create test client with database session."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def admin_user(db_session):
    """Create admin user for tests."""
    return User(
        id="test-admin",
        email="admin@ancap.cloud",
        name="Admin",
        is_active=True,
        is_admin=True,
    )


@pytest.fixture(scope="module")
def client_with_admin(db_session, admin_user):
    """Create test client with admin user."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestSourceSchedulesAdmin:
    """Tests for source schedules admin endpoints."""

    def test_list_schedules_admin(self, client_with_admin):
        """Admin can list source schedules."""
        response = client_with_admin.get("/v1/source-schedules/")
        assert response.status_code == 200
        data = response.json()
        assert "schedules" in data
        assert isinstance(data["schedules"], list)

    def test_create_schedule_admin(self, client_with_admin):
        """Admin can create a source schedule."""
        payload = {
            "project_id": "test-project-1",
            "source_type": "crypto-client",
            "source_pattern": "example.com/*",
            "check_interval_minutes": 60,
            "retention_days": 30,
            "max_sources": 10,
            "max_snapshots_per_source": 20,
            "max_claims_per_source": 50,
            "check_cooldown_seconds": 60,
            "enabled": True,
        }
        response = client_with_admin.post("/v1/source-schedules/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["project_id"] == payload["project_id"]
        assert data["source_type"] == payload["source_type"]

    def test_get_schedule_admin(self, client_with_admin):
        """Admin can get a schedule by ID."""
        # First create a schedule
        payload = {
            "project_id": "test-project-1",
            "source_type": "crypto-client",
            "enabled": True,
        }
        create_response = client_with_admin.post("/v1/source-schedules/", json=payload)
        schedule_id = create_response.json()["id"]

        response = client_with_admin.get(f"/v1/source-schedules/{schedule_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == schedule_id

    def test_delete_schedule_admin(self, client_with_admin):
        """Admin can delete a source schedule."""
        # First create a schedule
        payload = {
            "project_id": "test-project-1",
            "source_type": "crypto-client",
            "enabled": True,
        }
        create_response = client_with_admin.post("/v1/source-schedules/", json=payload)
        schedule_id = create_response.json()["id"]

        response = client_with_admin.delete(f"/v1/source-schedules/{schedule_id}")
        assert response.status_code == 204

    def test_unauthorized_access(self, client):
        """Unauthenticated users cannot access source schedules."""
        response = client.get("/v1/source-schedules/")
        assert response.status_code == 401

    def test_unauthorized_create(self, client):
        """Unauthenticated users cannot create schedules."""
        payload = {
            "project_id": "test-project-1",
            "source_type": "crypto-client",
            "enabled": True,
        }
        response = client.post("/v1/source-schedules/", json=payload)
        assert response.status_code == 401

    def test_invalid_source_type(self, client_with_admin):
        """Schedule creation with invalid source_type should fail."""
        payload = {
            "project_id": "test-project-1",
            "source_type": "",  # Empty string is invalid
            "enabled": True,
        }
        response = client_with_admin.post("/v1/source-schedules/", json=payload)
        assert response.status_code == 422

    def test_schedule_validation_limits(self, client_with_admin):
        """Schedule creation with limits exceeded should fail."""
        # max_sources must be >= 1
        payload = {
            "project_id": "test-project-1",
            "source_type": "crypto-client",
            "max_sources": 0,  # Invalid
            "enabled": True,
        }
        response = client_with_admin.post("/v1/source-schedules/", json=payload)
        assert response.status_code == 422

    def test_check_interval_validation(self, client_with_admin):
        """Check interval must be between 1 and 1440 minutes."""
        payload = {
            "project_id": "test-project-1",
            "source_type": "crypto-client",
            "check_interval_minutes": 0,  # Invalid
            "enabled": True,
        }
        response = client_with_admin.post("/v1/source-schedules/", json=payload)
        assert response.status_code == 422
