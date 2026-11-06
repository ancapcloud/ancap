"""CI acceptance tests for Research Operations (ROP-01) deployment."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    """Test client with mocked database."""
    return TestClient(app, raise_server_exceptions=True)


class TestResearchOpsCI:
    """ROP-01 CI acceptance tests for deployment verification."""

    def test_research_endpoint_exists(self, client):
        """Verify research endpoint is accessible (auth required)."""
        response = client.get("/workflow-ops/projects/test/research")
        assert response.status_code == 401

    def test_source_endpoint_exists(self, client):
        """Verify source registration endpoint exists."""
        response = client.post(
            "/workflow-ops/projects/test/research/sources",
            headers={"Authorization": "Bearer ***"},
            json={"url": "https://example.com"}
        )
        assert response.status_code == 401

    def test_source_check_endpoint_exists(self, client):
        """Verify source check endpoint exists."""
        response = client.post(
            "/workflow-ops/projects/test/research/sources/uuid/check",
            headers={"Authorization": "Bearer ***"}
        )
        assert response.status_code == 401

    def test_source_snapshots_endpoint_exists(self, client):
        """Verify source snapshots endpoint exists."""
        response = client.get(
            "/workflow-ops/projects/test/research/sources/uuid/snapshots",
            headers={"Authorization": "Bearer ***"}
        )
        assert response.status_code == 401
