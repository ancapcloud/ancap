"""Risk API: limits, kill switch, run status."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import DbSession, require_platform_admin
from app.db.models import RiskPolicy, CircuitBreaker, Run
from app.schemas.risk import (
    RiskLimitsRequest,
    RiskLimitsResponse,
    RiskKillRequest,
    RiskKillResponse,
    RiskStatusResponse,
)
from sqlalchemy import select

router = APIRouter(prefix="/risk", tags=["Risk"])


@router.post("/limits", response_model=RiskLimitsResponse)
async def set_risk_limits(
    body: RiskLimitsRequest,
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
):
    """Set or update risk policy (limits) for a scope. Upserts by (scope_type, scope_id)."""
    try:
        scope_id = UUID(body.scope_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scope_id")
    q = select(RiskPolicy).where(
        RiskPolicy.scope_type == body.scope_type,
        RiskPolicy.scope_id == scope_id,
    ).limit(1)
    r = await session.execute(q)
    row = r.scalar_one_or_none()
    if row:
        row.policy_json = body.policy_json
    else:
        row = RiskPolicy(
            scope_type=body.scope_type,
            scope_id=scope_id,
            policy_json=body.policy_json,
        )
        session.add(row)
    return RiskLimitsResponse(scope_type=body.scope_type, scope_id=body.scope_id)


@router.post("/kill", response_model=RiskKillResponse)
async def risk_kill(
    body: RiskKillRequest,
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
):
    """Set circuit breaker to halted for the given scope (pool, agent, or strategy)."""
    try:
        scope_id = UUID(body.scope_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scope_id")
    q = select(CircuitBreaker).where(
        CircuitBreaker.scope_type == body.scope_type,
        CircuitBreaker.scope_id == scope_id,
    ).limit(1)
    r = await session.execute(q)
    row = r.scalar_one_or_none()
    if row:
        row.state = "halted"
    else:
        row = CircuitBreaker(
            scope_type=body.scope_type,
            scope_id=scope_id,
            state="halted",
        )
        session.add(row)
    return RiskKillResponse(scope_type=body.scope_type, scope_id=body.scope_id)


@router.get("/status/{run_id}", response_model=RiskStatusResponse)
async def get_risk_status(run_id: UUID, session: DbSession):
    """Return run state and whether it was killed by risk (e.g. max_loss_pct, circuit breaker)."""
    run = await session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    killed_by_risk = run.state.value == "killed" and (
        run.failure_reason in ("max_loss_pct", "max_steps", "max_runtime_ms", "max_action_calls")
        or (run.failure_reason or "").startswith("circuit")
    )
    return RiskStatusResponse(
        run_id=str(run.id),
        state=run.state.value,
        killed_by_risk=killed_by_risk,
        failure_reason=run.failure_reason,
    )
