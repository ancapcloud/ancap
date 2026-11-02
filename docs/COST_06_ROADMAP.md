# COST-06 — Provider/Document Reconciliation and External Payment Events

## Task Description
Complete provider/document reconciliation in the existing cost track with external-payment event tracking. This includes:
- Document type classification and provider attribution
- External payment event recording (PSP/bank/order sources)
- Delivery event tracking
- Manual work evidence recording
- Refund handling
- Renewal-due events

## Acceptance Criteria
- Model `WorkflowCostEvidence` includes ROP-04 fields: `provider_id`, `document_type`, `external_payment_event`, `delivery_event`
- Service layer provides reconciliation functions with proper currency separation
- Admin endpoint for cost evidence retrieval and reconciliation
- Tests verify auth (401/403/404), atomic inserts, source uniqueness, run deletion retention
- Migration for external payment event tracking (if needed)

## Implementation Plan
1. Update `app/db/models.py` to add ROP-04 fields to existing cost evidence model
2. Add reconciliation functions in `app/services/workflow_costs.py`
3. Update router in `app/api/routers/workflow_cost_evidence.py` for reconciliation endpoints
4. Update Pydantic schemas in `app/schemas/workflow_costs.py`
5. Register/verify router in `app/main.py`
6. Create tests in `tests/api/test_workflow_cost_reconciliation.py`
7. Run targeted tests and commit changes

## Files to Modify
- `app/db/models.py` - add ROP-04 fields if not present
- `app/services/workflow_costs.py` - add reconciliation functions
- `app/api/routers/workflow_cost_evidence.py` - add reconciliation endpoints
- `app/schemas/workflow_costs.py` - update response schemas
- `app/main.py` - verify router registration
- `tests/api/test_workflow_cost_reconciliation.py` - create tests

## Estimated Time
8-12 minutes (3-5 files)
