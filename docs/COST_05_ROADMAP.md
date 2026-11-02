# COST-05 — Actual Cost Attribution Implementation

## Task Description
Implement actual cost attribution with provider billing and manual-work evidence. This includes:
- Model/data/infrastructure costs
- Retry costs
- Review/support costs
- Payment fees
- Separate estimates for each category

## Acceptance Criteria
- Service layer in `app/services/workflow_costs.py` provides cost attribution functions
- Admin endpoint `POST /v1/workflow-store/admin/cost-evidence/{id}/attribute` for cost attribution
- Proper validation of currency separation and no double-counting creator payouts
- Tests verify precision, category separation, and concurrent write handling
- Migration for cost attribution tracking (if needed)

## Implementation Plan
1. Create cost attribution service functions in `app/services/workflow_costs.py`
2. Add admin endpoint in `app/api/routers/workflow_cost_evidence.py`
3. Update Pydantic schemas in `app/schemas/workflow_costs.py`
4. Register router in `app/main.py`
5. Create tests in `tests/api/test_workflow_cost_attribution.py`
6. Run targeted tests and commit changes

## Files to Modify
- `app/services/workflow_costs.py` - add attribution functions
- `app/api/routers/workflow_cost_evidence.py` - add attribution endpoint
- `app/schemas/workflow_costs.py` - update response schemas
- `app/main.py` - register new router
- `tests/api/test_workflow_cost_attribution.py` - create tests

## Estimated Time
8-12 minutes (3-5 files)
