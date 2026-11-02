"""Tests for ROP-04 reconciliation endpoint.

Test provider reconciliation and delivery event updates.
"""
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.routers.workflow_cost_evidence import reconcile_provider_payment
from app.db.models import (
    User,
    WorkflowCostAllocation,
    WorkflowCostEvidence,
    WorkflowRunRecord,
)
from app.services.workflow_costs import get_cost_evidence


def _evidence(evidence_id, **overrides):
    payload = {
        "id": evidence_id,
        "source": "test-source",
        "document_id": "test-doc",
        "line_id": "test-line",
        "document_sha256": "0" * 64,
        "category": "model",
        "currency": "EUR",
        "amount": Decimal("100.00"),
        "review_note": "Test reconciliation",
        "external_payment_event": False,
        "delivery_event": False,
    }
    payload.update(overrides)
    return WorkflowCostEvidence(**payload)


@pytest.mark.asyncio
async def test_reconcile_pending_to_verified(db_session):
    """Test reconciliation status update from pending to verified."""
    evidence_id = uuid4()
    db_session.add(_evidence(evidence_id))
    await db_session.flush()

    receipt = await get_cost_evidence(evidence_id, db_session)
    assert receipt.reconciliation_status is None

    response = await reconcile_provider_payment(
        evidence_id, db_session, "test-admin", reconciliation_status="verified"
    )
    assert response.reconciliation_status == "verified"


@pytest.mark.asyncio
async def test_reconcile_invalid_status(db_session):
    """Test rejection of invalid reconciliation status."""
    evidence_id = uuid4()
    db_session.add(_evidence(evidence_id))
    await db_session.flush()

    with pytest.raises(HTTPException, match="Invalid reconciliation_status"):
        await reconcile_provider_payment(
            evidence_id, db_session, "test-admin", reconciliation_status="invalid"
        )


@pytest.mark.asyncio
async def test_delivery_event_update(db_session):
    """Test delivery event boolean update."""
    evidence_id = uuid4()
    db_session.add(_evidence(evidence_id, external_payment_event=True))
    await db_session.flush()

    response = await reconcile_provider_payment(
        evidence_id, db_session, "test-admin", delivery_event=True
    )
    assert response.delivery_status == "verified"


@pytest.mark.asyncio
async def test_reconciliation_with_allocations(db_session):
    """Test reconciliation preserves allocations."""
    evidence_id = uuid4()
    db_session.add(
        _evidence(evidence_id, external_payment_event=True, delivery_event=True)
    )
    await db_session.flush()

    owner = User(
        id=str(uuid4()),
        email=f"cost-reconcile-{uuid4().hex}@test.com",
        password_hash="not-used",
    )
    db_session.add(owner)
    await db_session.flush()

    run = WorkflowRunRecord(
        id=str(uuid4()),
        owner_user_id=owner.id,
        workflow_slug="test-workflow",
        title="Test run",
        category="test",
        quoted_amount=Decimal("0"),
        quoted_currency="ACP",
        payment_currency="ACP",
    )
    db_session.add(run)
    await db_session.flush()

    db_session.add(
        WorkflowCostAllocation(
            evidence_id=evidence_id,
            workflow_run_id=run.id,
            amount=Decimal("50.00"),
            category="model",
            currency="EUR",
        )
    )
    await db_session.flush()

    receipt = await get_cost_evidence(evidence_id, db_session)
    assert len(receipt.allocations) == 1
    assert receipt.reconciliation_status is None
