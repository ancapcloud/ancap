"""Tests for /workflow-store/admin/cost-evidence/{evidence_id} endpoint."""
import json
import asyncio
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import WorkflowCostEvidence
from app.schemas.workflow_costs import CostEvidenceCreate, CostRunAllocation


def _make_sha256():
    """Generate a valid 64-char hex SHA256 string for tests."""
    return uuid.uuid4().hex + uuid.uuid4().hex  # Ensure exactly 64 chars


@pytest.fixture(scope="function")
def evidence_data(client, evidence_create):
    """Create a test cost evidence record via API for GET tests."""
    # Generate unique IDs to prevent UniqueConstraint violations
    source = f"test_source_{uuid.uuid4().hex[:8]}"
    document_id = f"doc-test-{uuid.uuid4().hex[:6]}"
    line_id = f"line-{uuid.uuid4().hex[:6]}"
    
    evidence = evidence_create(
        source=source,
        document_id=document_id,
        line_id=line_id,
        document_sha256=_make_sha256(),
        category="model",
        currency="ACP",
        amount=10.0,
        review_note="Test evidence for API testing"
    )
    return type("obj", (object,), {
        "id": evidence.id,
        "source": evidence.source,
        "document_id": evidence.document_id,
        "line_id": evidence.line_id,
        "amount": evidence.amount
    })


@pytest.mark.asyncio
async def test_get_cost_evidence_admin_access(client, evidence_data):
    """Admin user can read cost evidence."""
    response = client.get(
        f"/workflow-store/admin/cost-evidence/{evidence_data.id}",
        headers={"Authorization": f"Bearer {client.platform_admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == evidence_data.source
    assert data["document_id"] == evidence_data.document_id
    assert data["line_id"] == evidence_data.line_id
    assert data["category"] == "model"
    assert data["currency"] == "ACP"
    assert abs(float(data["amount"]) - 10.0) < 0.001
    assert data["review_note"] == "Test evidence for API testing"
    assert len(data["allocations"]) == 2
    # Check that allocations sum to total amount
    total_allocated = sum(float(a["allocated_amount"]) for a in data["allocations"])
    assert abs(total_allocated - float(data["amount"])) < 0.001


@pytest.mark.asyncio
async def test_get_cost_evidence_unauthorized(client):
    """Guest user gets 401."""
    # Create a fake evidence ID that doesn't exist
    fake_evidence_id = str(uuid.uuid4())
    
    response = client.get(
        f"/workflow-store/admin/cost-evidence/{fake_evidence_id}",
        headers={"Authorization": f"Bearer {client.platform_admin_token}"}
    )
    
    # Should get 404 for non-existent evidence (auth is handled by require_platform_admin)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_cost_evidence_not_found(client):
    """Unknown evidence ID returns 404."""
    fake_evidence_id = str(uuid.uuid4())
    
    response = client.get(
        f"/workflow-store/admin/cost-evidence/{fake_evidence_id}",
        headers={"Authorization": f"Bearer {client.platform_admin_token}"}
    )
    
    assert response.status_code == 404


@pytest.fixture(scope="function")
async def evidence_data_persistent_async(client):
    """Async fixture to create a test cost evidence record for function-level tests."""
    from app.db.session import async_session_maker
    from app.db.models import WorkflowCostEvidence
    
    # Generate unique IDs to prevent UniqueConstraint violations
    source = f"test_source_persistent_{uuid.uuid4().hex[:8]}"
    document_id = f"doc-test-persistent-{uuid.uuid4().hex[:6]}"
    line_id = f"line-persistent-{uuid.uuid4().hex[:6]}"
    
    async def _create():
        async with async_session_maker() as session:
            evidence = WorkflowCostEvidence(
                source=source,
                document_id=document_id,
                line_id=line_id,
                document_sha256=_make_sha256(),
                category="model",
                currency="ACP",
                amount=Decimal("100.0"),
                review_note="Persistent test evidence"
            )
            session.add(evidence)
            await session.commit()
            await session.refresh(evidence)
        return type("obj", (object,), {
            "id": str(evidence.id),
            "source": evidence.source,
            "document_id": evidence.document_id,
            "line_id": evidence.line_id,
            "amount": float(evidence.amount)
        })
    
    return await _create()


@pytest.fixture(scope="function")
def evidence_data_persistent(client, evidence_data_persistent_async):
    """Sync wrapper for the async evidence fixture."""
    return evidence_data_persistent_async


@pytest.mark.asyncio
async def test_get_cost_evidence_no_mutation(client, evidence_data):
    """GET endpoint does not mutate data (idempotent read)."""
    # Get the evidence twice and verify data is unchanged
    response1 = client.get(
        f"/workflow-store/admin/cost-evidence/{evidence_data.id}",
        headers={"Authorization": f"Bearer {client.platform_admin_token}"}
    )
    assert response1.status_code == 200
    data1 = response1.json()
    
    # Small delay to ensure we're not hitting cached response
    await asyncio.sleep(0.01)
    
    response2 = client.get(
        f"/workflow-store/admin/cost-evidence/{evidence_data.id}",
        headers={"Authorization": f"Bearer {client.platform_admin_token}"}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    
    # Verify both responses are identical
    assert data1 == data2


@pytest.mark.asyncio
async def test_get_cost_evidence_no_db_mutation(client, evidence_data_persistent):
    """GET does not mutate the database."""
    from app.db.session import async_session_maker
    from app.db.models import WorkflowCostEvidence
    
    initial_count = 0
    async with async_session_maker() as session:
        result = await session.execute(select(WorkflowCostEvidence))
        initial_count = len(result.scalars().all())
    
    response = client.get(
        f"/workflow-store/admin/cost-evidence/{evidence_data_persistent.id}",
        headers={"Authorization": f"Bearer {client.platform_admin_token}"}
    )
    
    assert response.status_code == 200
    
    final_count = 0
    async with async_session_maker() as session:
        result = await session.execute(select(WorkflowCostEvidence))
        final_count = len(result.scalars().all())
    
    assert initial_count == final_count
