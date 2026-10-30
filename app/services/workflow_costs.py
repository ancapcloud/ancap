"""Pure reconciliation foundation. Callers must authenticate and verify evidence.

No provider usage estimate or default-zero usage row is accepted implicitly.
Retries belong to their original run and have distinct provider evidence lines.
"""
from collections import defaultdict
from decimal import Decimal, localcontext
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models import WorkflowCostAllocation, WorkflowCostEvidence, WorkflowRunRecord
from app.api.deps import DbSession

from app.schemas.workflow_costs import COST_CATEGORIES, ReconciledCostAllocation, ReconciledRunCosts


async def record_cost_evidence(session, reviewer_id: str, body):
    """Insert a complete source-line distribution once; no append/update API.

    Source uniqueness arbitrates concurrent submissions in PostgreSQL. A nested
    transaction prevents failed inserts from poisoning the request transaction.
    """
    from app.schemas.workflow_costs import CostEvidenceReceipt
    run_ids = sorted({a.workflow_run_id for a in body.allocations})
    async with session.begin_nested():
        # Serialize with run deletion and retain a consistent referenced set.
        found = {str(value) for value in (await session.execute(select(WorkflowRunRecord.id).where(
            WorkflowRunRecord.id.in_(run_ids)).order_by(WorkflowRunRecord.id).with_for_update())).scalars()}
        if found != {str(value) for value in run_ids}:
            raise HTTPException(status_code=404, detail="Workflow run not found")
        row = WorkflowCostEvidence(**body.model_dump(exclude={"allocations"}), recorded_by_user_id=UUID(reviewer_id))
        try:
            session.add(row)
            await session.flush()
            session.add_all([WorkflowCostAllocation(evidence_id=row.id, workflow_run_id=a.workflow_run_id,
                amount=a.allocated_amount) for a in body.allocations])
            await session.flush()
        except IntegrityError as exc:
            if getattr(exc.orig, "sqlstate", None) == "23505":
                raise HTTPException(status_code=409, detail="Source line already recorded; no changes applied") from exc
            raise
        return CostEvidenceReceipt(id=row.id, recorded_by_user_id=row.recorded_by_user_id)


async def get_cost_evidence(evidence_id: UUID, session: DbSession):
    """Retrieve a single cost evidence record by ID.

    Admin-only endpoint for viewing saved cost evidence records.
    Returns the full evidence record with all allocations.
    """
    from app.schemas.workflow_costs import CostEvidenceReceipt, ReconciledCostAllocation
    
    evidence = (await session.execute(select(WorkflowCostEvidence).where(
        WorkflowCostEvidence.id == evidence_id))).scalar_one_or_none()
    if evidence is None:
        raise HTTPException(status_code=404, detail="Cost evidence not found")
    
    # Fetch allocations for this evidence
    allocations = (await session.execute(select(WorkflowCostAllocation).where(
        WorkflowCostAllocation.evidence_id == evidence_id))).scalars().all()
    
    # Convert to response schema with full details
    receipt = CostEvidenceReceipt(
        id=evidence.id,
        source=evidence.source,
        document_id=evidence.document_id,
        line_id=evidence.line_id,
        document_sha256=evidence.document_sha256,
        category=evidence.category,
        currency=evidence.currency,
        amount=evidence.amount,
        review_note=evidence.review_note,
        recorded_by_user_id=evidence.recorded_by_user_id
    )
    
    # Include allocations in the response with full details
    receipt.allocations = [ReconciledCostAllocation(
        workflow_run_id=a.workflow_run_id,
        evidence_line_id=str(a.evidence_line_id),
        evidence_amount=a.evidence_amount,
        allocated_amount=a.allocated_amount,
        category=a.category,
        currency=a.currency
    ) for a in allocations]
    
    return receipt


async def stored_run_costs(session, run_id: UUID):
    if (await session.execute(select(WorkflowRunRecord.id).where(WorkflowRunRecord.id == run_id))).scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    rows = (await session.execute(select(WorkflowCostEvidence, WorkflowCostAllocation).join(
        WorkflowCostAllocation, WorkflowCostAllocation.evidence_id == WorkflowCostEvidence.id).where(
        WorkflowCostAllocation.workflow_run_id == run_id))).all()
    # Each immutable line was validated as a complete allocation batch on insert.
    return reconcile_run_costs([run_id], [ReconciledCostAllocation(workflow_run_id=run_id,
        category=e.category, evidence_line_id=str(e.id), evidence_amount=e.amount,
        allocated_amount=a.amount, currency=e.currency) for e, a in rows])[0]


def reconcile_run_costs(run_ids: list[UUID], allocations: list[ReconciledCostAllocation]) -> list[ReconciledRunCosts]:
    """Reject duplicate or over-allocated evidence before calculating any totals.

Pass the full allocation set for each evidence line, including allocations to
unselected runs, so selecting a subset cannot hide an over-allocation.
Coverage means categories have evidence, not that billing was independently audited.
"""
    lines = {}
    seen = set()
    totals = defaultdict(lambda: defaultdict(Decimal))
    categories = defaultdict(set)
    # Numeric(36,18) addition must not silently round at Decimal's default precision.
    with localcontext() as context:
        context.prec = 80
        for allocation in allocations:
            key = (allocation.evidence_line_id, allocation.workflow_run_id)
            if key in seen:
                raise ValueError("Duplicate evidence allocation")
            seen.add(key)
            identity = (allocation.currency, allocation.evidence_amount, allocation.category)
            previous, allocated = lines.get(allocation.evidence_line_id, (identity, Decimal(0)))
            if previous != identity:
                raise ValueError("Conflicting evidence line")
            allocated += allocation.allocated_amount
            if allocated > allocation.evidence_amount:
                raise ValueError("Evidence line over-allocated")
            lines[allocation.evidence_line_id] = (identity, allocated)
            totals[allocation.workflow_run_id][allocation.currency] += allocation.allocated_amount
            categories[allocation.workflow_run_id].add(allocation.category)
        return [ReconciledRunCosts(
            workflow_run_id=run_id,
            totals_by_currency=dict(sorted(totals[run_id].items())),
            evidenced_categories=[c for c in COST_CATEGORIES if c in categories[run_id]],
            missing_categories=[c for c in COST_CATEGORIES if c not in categories[run_id]],
            coverage_complete=set(COST_CATEGORIES) == categories[run_id],
        ) for run_id in dict.fromkeys(run_ids)]
