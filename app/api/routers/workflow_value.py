from fastapi import APIRouter, Depends, Query, Response
from app.api.deps import DbSession, require_auth
from app.schemas.workflow_value import AssessmentCreate, AssessmentHistory, AssessmentPublic, AssessmentState, AssessedResultPublic, ValueSummary
from app.services import workflow_value

router = APIRouter(prefix="/workflow-store", tags=["Private Workflow Value"])


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
