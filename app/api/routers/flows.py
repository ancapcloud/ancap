from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import DbSession, require_platform_admin
from app.config import get_settings
from app.scenarios.runner import run_flow
from app.schemas.flows import FlowRunRequest, FlowRunResponse

router = APIRouter(prefix="/flows", tags=["Flows"])


@router.post("/run", response_model=FlowRunResponse)
async def run_flow_endpoint(
    body: FlowRunRequest,
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
):
    # Scenario flows mint ledger deposits and clear the ledger invariant halt;
    # they are a dev/demo seeding tool and must never run against production.
    if get_settings().environment == "production":
        raise HTTPException(status_code=404, detail="Not found")
    return await run_flow(body.flow_id, session, seed=body.seed, params=body.params)
