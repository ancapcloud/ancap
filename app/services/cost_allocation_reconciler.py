"""Evidence-allocation reconciler for workflow cost attribution."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import WorkflowCostAllocation, WorkflowCostEvidence, WorkflowRunRecord
from app.db.session import async_session_maker


async def reconcile_workflow_cost_allocations(
    evidence_id: str,
    workflow_run_ids: list[str],
    *,
    session: AsyncSession | None = None,
) -> dict[str, Any]:
    """Distribute evidence.amount across workflow runs by quoted_amount (else equally)."""

    async def _run(db: AsyncSession) -> dict[str, Any]:
        evidence = await db.get(WorkflowCostEvidence, evidence_id)
        if not evidence:
            return {"error": "Evidence not found", "allocations": []}

        total_amount = float(evidence.amount)
        allocations: list[dict[str, Any]] = []
        if workflow_run_ids:
            rows = (
                await db.execute(
                    select(WorkflowRunRecord).where(WorkflowRunRecord.id.in_(workflow_run_ids))
                )
            ).scalars().all()
            runs_by_id = {str(row.id): float(row.quoted_amount or 0) for row in rows}
            total_quoted = sum(runs_by_id.values())
            for run_id in workflow_run_ids:
                quoted_amount = runs_by_id.get(str(run_id), 0.0)
                if total_quoted > 0:
                    share = (quoted_amount / total_quoted) * total_amount
                else:
                    share = total_amount / len(workflow_run_ids)
                allocation = WorkflowCostAllocation(
                    evidence_id=UUID(str(evidence_id)),
                    workflow_run_id=UUID(str(run_id)),
                    amount=share,
                )
                db.add(allocation)
                allocations.append({"workflow_run_id": str(run_id), "amount": str(share)})

        evidence.allocations = allocations
        await db.flush()
        return {
            "evidence_id": str(evidence_id),
            "total_amount": str(total_amount),
            "allocations": allocations,
            "status": "reconciled",
        }

    if session is not None:
        return await _run(session)
    async with async_session_maker() as owned:
        result = await _run(owned)
        await owned.commit()
        return result


async def get_allocation_summary(
    evidence_id: str,
    *,
    session: AsyncSession | None = None,
) -> dict[str, Any]:
    """Get summary of allocations for a cost evidence record."""

    async def _run(db: AsyncSession) -> dict[str, Any]:
        evidence = await db.get(WorkflowCostEvidence, evidence_id)
        if not evidence:
            return {"error": "Evidence not found", "allocations": []}

        rows = (
            await db.execute(
                select(WorkflowCostAllocation).where(
                    WorkflowCostAllocation.evidence_id == evidence_id
                )
            )
        ).scalars().all()
        allocations = [
            {"workflow_run_id": str(row.workflow_run_id), "amount": str(row.amount)}
            for row in rows
        ]
        return {
            "evidence_id": str(evidence_id),
            "total_allocated": sum(float(a["amount"]) for a in allocations) if allocations else 0.0,
            "allocation_count": len(allocations),
            "allocations": allocations,
        }

    if session is not None:
        return await _run(session)
    async with async_session_maker() as owned:
        return await _run(owned)
