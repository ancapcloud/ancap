"""Tests for Research Operations admin endpoints.

This module tests the admin-only GET /v1/workflow-store/admin/cost-evidence/{evidence_id}
endpoint for operator verification of cost evidence records.
"""
import pytest
from decimal import Decimal
from uuid import uuid4

from app.db.models import WorkflowCostEvidence


def test_get_cost_evidence_admin_not_found(client):
    """Test 404 for non-existent evidence."""
    response = client.get("/v1/workflow-store/admin/cost-evidence/invalid-uuid")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_get_cost_evidence_admin_unauthorized(client):
    """Test 401 for unauthenticated requests."""
    # Ensure client is not authenticated by passing empty auth header
    response = client.get("/v1/workflow-store/admin/cost-evidence/" + str(uuid4()), headers={"Authorization": ""})
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


def test_get_cost_evidence_admin_success(client):
    """Test successful admin read of cost evidence with real data."""
    # Create a test evidence record via direct DB insert (safe for tests)
    from sqlalchemy import text
    
    with client as c:
        # Get the database session from the fixture's override
        from app.db.session import async_session_maker
        
        with async_session_maker() as session:
            # Create evidence directly in DB
            evidence = WorkflowCostEvidence(
                source="test-source-123",
                document_id="doc-001",
                line_id="line-001",
                document_sha256="a" * 64,
                category="model",
                currency="USD",
                amount=Decimal("10.00"),
                review_note="Test evidence for operator verification",
                recorded_by_user_id=None,
            )
            session.add(evidence)
            session.commit()
            
            # Get the actual UUID from the database
            result = session.execute(text("SELECT id FROM workflow_cost_evidence WHERE source = :source"), {"source": "test-source-123"})
            row = result.fetchone()
            evidence_id = str(row[0]) if row else None
        
        # Now test the endpoint - it should return 200 with evidence data
        response = client.get(f"/v1/workflow-store/admin/cost-evidence/{evidence_id}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify the response contains expected fields
        assert data["id"] == evidence_id
        assert data["source"] == "test-source-123"
        assert data["document_id"] == "doc-001"
        assert data["line_id"] == "line-001"
        assert data["category"] == "model"
        assert data["currency"] == "USD"
        assert data["amount"] == 10.0
        assert data["verification_basis"] == "operator_attested"


def test_get_cost_evidence_admin_empty_source(client):
    """Test that endpoint handles empty source gracefully."""
    response = client.get("/v1/workflow-store/admin/cost-evidence/")
    # Should return 422 (validation error) or 404
    assert response.status_code in (404, 422)


def test_get_cost_evidence_admin_with_real_data(client):
    """Test successful admin read with real evidence data."""
    from sqlalchemy import text
    
    with client as c:
        with async_session_maker() as session:
            evidence = WorkflowCostEvidence(
                source="test-source-456",
                document_id="doc-002",
                line_id="line-002",
                document_sha256="b" * 64,
                category="compute",
                currency="USD",
                amount=Decimal("25.50"),
                review_note="Second test evidence",
                recorded_by_user_id=None,
            )
            session.add(evidence)
            session.commit()
            
            # Get the actual ID
            result = session.execute(text("SELECT id FROM workflow_cost_evidence WHERE source = :source"), {"source": "test-source-456"})
            row = result.fetchone()
            evidence_id = str(row[0]) if row else None
        
        if evidence_id:
            # Test successful retrieval
            response = client.get(f"/v1/workflow-store/admin/cost-evidence/{evidence_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == evidence_id
            assert data["source"] == "test-source-456"
            assert data["verification_basis"] == "operator_attested"
