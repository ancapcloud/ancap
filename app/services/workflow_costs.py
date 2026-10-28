"""Pure reconciliation foundation. Callers must authenticate and verify evidence.

No provider usage estimate or default-zero usage row is accepted implicitly.
Retries belong to their original run and have distinct provider evidence lines.
"""
from collections import defaultdict
from decimal import Decimal, localcontext
from uuid import UUID

from app.schemas.workflow_costs import COST_CATEGORIES, ReconciledCostAllocation, ReconciledRunCosts


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
