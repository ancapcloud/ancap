"""Tests for ROP-04 reconciliation endpoint.

Test provider reconciliation and delivery event updates.
"""
import pytest
from uuid import uuid4
from decimal import Decimal

from app.db.models import WorkflowCostEvidence, WorkflowCostAllocation
from app.schemas.workflow_costs import CostEvidenceCreate, CostEvidenceReceipt


@pytest.mark.asyncio
async def test_reconcile_pending_to_verified(db_session):
    """Test reconciliation status update from pending to verified."""
    evidence_id = uuid4()
    
    # Create test evidence with external_payment_event=False
    evidence = WorkflowCostEvidence(
        source="test-source",
        document_id="test-doc",
        line_id="test-line",
        document_sha256="0" * 64,
        category="model",
        currency="EUR",
        amount=Decimal("100.00"),
        review_note="Test reconciliation",
        external_payment_event=False,
        delivery_event=False,
    )
    db_session.add(evidence)
    await db_session.flush()
    
    # Initially pending
    receipt = await get_cost_evidence(evidence_id, db_session)
    assert receipt.reconciliation_status is None
    
    # Reconcile to verified
    response = await post_reconcile(evidence_id, reconciliation_status="verified")
    assert response.reconciliation_status == "verified"


@pytest.mark.asyncio
async def test_reconcile_invalid_status(db_session):
    """Test rejection of invalid reconciliation status."""
    evidence_id = uuid4()
    
    evidence = WorkflowCostEvidence(
        source="test-source",
        document_id="test-doc",
        line_id="test-line",
        document_sha256="0" * 64,
        category="model",
        currency="EUR",
        amount=Decimal("100.00"),
        review_note="Test reconciliation",
        external_payment_event=False,
        delivery_event=False,
    )
    db_session.add(evidence)
    await db_session.flush()
    
    # Try invalid status
    with pytest.raises(HTTPException, match="Invalid reconciliation_status"):
        await post_reconcile(evidence_id, reconciliation_status="invalid")


@pytest.mark.asyncio
async def test_delivery_event_update(db_session):
    """Test delivery event boolean update."""
    evidence_id = uuid4()
    
    evidence = WorkflowCostEvidence(
        source="test-source",
        document_id="test-doc",
        line_id="test-line",
        document_sha256="0" * 64,
        category="model",
        currency="EUR",
        amount=Decimal("100.00"),
        review_note="Test delivery",
        external_payment_event=True,
        delivery_event=False,
    )
    db_session.add(evidence)
    await db_session.flush()
    
    # Update delivery event
    response = await post_reconcile(evidence_id, delivery_event=True)
    assert response.delivery_status == "verified"


@pytest.mark.asyncio
async def test_reconciliation_with_allocations(db_session):
    """Test reconciliation preserves allocations."""
    evidence_id = uuid4()
    
    evidence = WorkflowCostEvidence(
        source="test-source",
        document_id="test-doc",
        line_id="test-line",
        document_sha256="0" * 64,
        category="model",
        currency="EUR",
        amount=Decimal("100.00"),
        review_note="Test with allocations",
        external_payment_event=True,
        delivery_event=True,
    )
    db_session.add(evidence)
    await db_session.flush()
    
    allocation = WorkflowCostAllocation(
        evidence_id=evidence_id,
        workflow_run_id=uuid4(),
        amount=Decimal("50.00"),
        category="model",
        currency="EUR",
    )
    db_session.add(allocation)
    await db_session.flush()
    
    receipt = await get_cost_evidence(evidence_id, db_session)
    assert len(receipt.allocations) == 1
    assert receipt.reconciliation_status is None
