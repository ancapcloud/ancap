from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import DbSession, require_platform_admin
from app.config import get_settings
from app.schemas.flows import FlowRunRequest, FlowRunResponse
from app.scenarios.runner import run_flow

router = APIRouter(prefix="/flows", tags=["Flows"])


@router.post("/run", response_model=FlowRunResponse)
async def run_flow_endpoint(
    body: FlowRunRequest,
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
):
    """Run a demo scenario flow (operator-only).

    Scenario flows mint ledger balances and reset the ledger invariant halt, so they are
    restricted to platform operators and disabled in production by default.
    """
    settings = get_settings()
    if settings.environment == "production" and not settings.flows_runner_enabled_in_production:
        raise HTTPException(status_code=403, detail="Scenario runner is disabled in production")
    return await run_flow(body.flow_id, session, seed=body.seed, params=body.params)
