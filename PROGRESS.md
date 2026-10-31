# PROGRESS.md — 2026-10-30

## COST-03 — admin cost evidence endpoint — completed
- Implemented GET /v1/workflow-store/admin/cost-evidence/{evidence_id} for operator-attested source verification.
- Files changed: workflow_value.py (router), models.py (WorkflowCostEvidence model), workflow_costs.py (schemas/services), test_workflow_cost_evidence_api.py (tests).
- Commands: git add 5 files; git commit "feat(cost): implement admin cost evidence endpoint with verification".
- Tests: 5 targeted tests passed (access control, atomicity, 404/401 handling, allocations retrieval, cache-control headers).
- Commit: d97fbf23 on master.
- Limitations: isolated PostgreSQL used for API tests; fixtures may drop schema.

## ROP-03 — research operations quality fixtures — completed (basic)
- Implemented endpoints for bounded collection pilot: upload_quality_fixtures, get_quality_fixture, remove_quality_fixture.
- Files changed: app/services/research_ops.py, app/api/routers/research_ops.py, PROGRESS.md.
- Commit: cc78727d on master.
- Status: Basic fixture CRUD implemented with simplified in-memory storage; ready for DB integration and testing.
- Database Integration:
  - Added QualityFixture model to app/db/models.py
  - Created migration file 002_add_quality_fixtures_table.py
  - Migration defines quality_fixtures table with UUID primary key, fixture metadata, test cases/results JSONB columns, status tracking
- Next: Run migration, update service layer to use database instead of in-memory storage, write integration tests.

## Privacy Receive Snapshot — completed (local commit)
- Implemented _privacy_receive_snapshot() in wallet_acp.py for live UTXO aggregation on privacy receive addresses.
- Added privacy_receive_acp field to frontend types and updated acpBalanceDisplay.ts/test.ts.
- Commit: a0fed9ae feat(privacy): add privacy receive snapshot UTXO aggregation and frontend display.
- Status: Local commit on master, ahead of origin/master by 5 commits.

## Run Summary
- **Git status:** working tree clean (untracked test files excluded).
- **Git branch:** `master` — ahead of `origin/master` by 5 commits.
- **Git hash:** `a0fed9ae`
- **Next:** ROP-03 database integration (migration 002) or continue Research Operations P0 per docs/RESEARCH_OPERATIONS_PILOT_ROADMAP.md.
