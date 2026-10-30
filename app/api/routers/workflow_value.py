from fastapi import APIRouter, Depends, Query, Response
from app.api.deps import DbSession, require_auth
from app.schemas.workflow_value import AssessmentCreate, AssessmentHistory, AssessmentPublic, AssessmentState, AssessedResultPublic, ValueSummary
from app.services import workflow_value
from uuid import UUID
from app.api.deps import require_platform_admin
from app.schemas.workflow_costs import CostEvidenceCreate, CostEvidenceReceipt, ReconciledRunCosts
from app.services import workflow_costs

router = APIRouter(prefix="/workflow-store", tags=["Private Workflow Value"])


@router.post("/admin/cost-evidence", response_model=CostEvidenceReceipt, status_code=201)
async def record_cost_evidence(body: CostEvidenceCreate, session: DbSession, response: Response,
                               reviewer_id: str = Depends(require_platform_admin)):
    response.headers["Cache-Control"] = "private, no-store"
    return await workflow_costs.record_cost_evidence(session, reviewer_id, body)


@router.get("/admin/cost-evidence/{evidence_id}", response_model=CostEvidenceReceipt)
async def get_cost_evidence(evidence_id: UUID, session: DbSession, response: Response,
                             reviewer_id: str = Depends(require_platform_admin)):
    response.headers["Cache-Control"] = "private, no-store"
    return await workflow_costs.get_cost_evidence(evidence_id, session)


@router.get("/admin/runs/{run_id}/costs", response_model=ReconciledRunCosts)
async def get_run_costs(run_id: UUID, session: DbSession, response: Response,
                        reviewer_id: str = Depends(require_platform_admin)):
    response.headers["Cache-Control"] = "private, no-store"
    return await workflow_costs.stored_run_costs(session, run_id)


@router.get("/value", response_model=ValueSummary)
async def get_value_summary(session: DbSession, response: Response, days: int = Query(30, ge=1, le=90), owner_id: str = Depends(require_auth)):
    response.headers["Cache-Control"] = "private, no-store"
    return await workflow_value.value_summary(session, owner_id, days)


@router.get("/runs/{run_id}/assessment", response_model=AssessmentState)
async def get_assessment(run_id: str, session: DbSession, response: Response, owner_id: str = Depends(require_auth)):
    response.headers["Cache-Control"] = "private, no-store"
    return await workflow_value.assessment_state(session, owner_id, run_id)


@router.post("/runs/{run_id}/assessment", response_model=AssessmentPublic, status_code=201)
async def submit_assessment(run_id: str, body: AssessmentCreate, session: DbSession, response: Response, owner_id: str = Depends(require_auth)):
    response.headers["Cache-Control"] = "private, no-store"
    return await workflow_value.create_assessment(session, owner_id, run_id, body)


@router.get("/runs/{run_id}/assessments", response_model=AssessmentHistory)
async def get_assessment_history(run_id: str, session: DbSession, response: Response, owner_id: str = Depends(require_auth)):
    response.headers["Cache-Control"] = "private, no-store"
    return await workflow_value.assessment_history(session, owner_id, run_id)


@router.get("/assessments/{assessment_id}/result", response_model=AssessedResultPublic)
async def get_assessed_result(assessment_id: str, session: DbSession, response: Response, owner_id: str = Depends(require_auth)):
    response.headers["Cache-Control"] = "private, no-store"
    return await workflow_value.assessed_result(session, owner_id, assessment_id)
