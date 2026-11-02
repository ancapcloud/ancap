"""Deployment acceptance tests for Research Operations (ROP-01)."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    """Test client with mocked database."""
    return TestClient(app, raise_server_exceptions=True)


class TestResearchOpsDeployment:
    """ROP-01 deployment acceptance tests for CI/production verification."""

    def test_research_endpoint_health(self, client):
        """Verify research endpoint responds with expected status (auth required)."""
        response = client.get("/workflow-ops/projects/test/research")
        assert response.status_code == 401

    def test_source_registration_health(self, client):
        """Verify source registration endpoint responds with expected status."""
        response = client.post(
            "/workflow-ops/projects/test/research/sources",
            headers={"Authorization": "Bearer ***"},
            json={"url": "https://example.com"}
        )
        assert response.status_code == 401

    def test_source_check_health(self, client):
        """Verify source check endpoint responds with expected status."""
        response = client.post(
            "/workflow-ops/projects/test/research/sources/uuid/check",
            headers={"Authorization": "Bearer ***"}
        )
        assert response.status_code == 401

    def test_source_snapshots_health(self, client):
        """Verify source snapshots endpoint responds with expected status."""
        response = client.get(
            "/workflow-ops/projects/test/research/sources/uuid/snapshots",
            headers={"Authorization": "Bearer ***"}
        )
        assert response.status_code == 401

    def test_research_brief_health(self, client):
        """Verify research brief endpoint responds with expected status."""
        response = client.get("/workflow-ops/projects/test/research/brief")
        assert response.status_code == 401
