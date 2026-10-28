from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.deps import DbSession, require_auth
from app.schemas import (
    FaucetClaimRequest,
    FaucetClaimPublic,
    StarterPackAssignRequest,
    StarterPackAssignmentPublic,
    QuickstartRunRequest,
    RunRequest,
    RunPublic,
)
from app.services.faucet import claim_faucet
from app.services.starter_pack import assign_starter_pack, activate_starter_pack
from app.services.quickstart import provision_quickstart
from app.api.routers.runs import _request_run_impl


router = APIRouter(prefix="/onboarding", tags=["Growth Onboarding"])


@router.post("/faucet/claim", response_model=FaucetClaimPublic, status_code=201)
async def faucet_claim(
    body: FaucetClaimRequest,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    uid = UUID(user_id)
    if body.user_id and UUID(body.user_id) != uid:
        raise HTTPException(status_code=403, detail="Cannot claim for another user")
    claim = await claim_faucet(
        session,
        user_id=uid,
        agent_id=UUID(body.agent_id) if body.agent_id else None,
        currency=body.currency,
        amount_value=Decimal(body.amount),
    )
    return FaucetClaimPublic(
        id=str(claim.id),
        user_id=str(claim.user_id) if claim.user_id else None,
        agent_id=str(claim.agent_id) if claim.agent_id else None,
        currency=claim.currency,
        amount=str(claim.amount_value),
        claim_status=claim.claim_status,
        risk_flags=claim.risk_flags or {},
        ledger_tx_id=str(claim.ledger_tx_id) if claim.ledger_tx_id else None,
        created_at=claim.created_at,
    )


@router.post("/starter-pack/assign", response_model=StarterPackAssignmentPublic, status_code=201)
async def starter_pack_assign(
    body: StarterPackAssignRequest,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    uid = UUID(user_id)
    if body.user_id and UUID(body.user_id) != uid:
        raise HTTPException(status_code=403, detail="Cannot assign for another user")
    a = await assign_starter_pack(
        session,
        user_id=uid,
        agent_id=UUID(body.agent_id) if body.agent_id else None,
        starter_pack_code=body.starter_pack_code,
    )
    # auto-activate to satisfy "1–2 minutes" activation path
    a = await activate_starter_pack(session, assignment_id=a.id)
    return StarterPackAssignmentPublic(
        id=str(a.id),
        starter_pack_id=str(a.starter_pack_id),
        user_id=str(a.user_id) if a.user_id else None,
        agent_id=str(a.agent_id) if a.agent_id else None,
        status=a.status,
        assigned_at=a.assigned_at,
        activated_at=a.activated_at,
    )


@router.post("/quickstart/run", response_model=RunPublic, status_code=201)
async def quickstart_run(
    body: QuickstartRunRequest,
    session: DbSession,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user_id: str = Depends(require_auth),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Missing Idempotency-Key header")
    prov = await provision_quickstart(session, owner_agent_id=UUID(body.owner_agent_id))
    run_body = RunRequest(
        strategy_version_id=str(prov.strategy_version_id),
        pool_id=str(prov.pool_id),
        params={"quickstart": True},
        limits=None,
        dry_run=False,
        contract_id=None,
        contract_milestone_id=None,
        run_mode="mock",
    )
    return await _request_run_impl(
        run_body,
        session,
        idempotency_key,
        user_id,
        skip_owner_agent_access_checks=True,
    )

