from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func

from app.api.deps import DbSession, get_current_user_id
from app.db.models import (
    Agent,
    Contract,
    ContractStatusEnum,
    ContractMilestone,
    ContractMilestoneStatusEnum,
    PaymentModelEnum,
    LedgerEvent,
    LedgerEventTypeEnum,
)
from app.schemas import (
    ContractMilestoneCreateRequest,
    ContractMilestoneUpdateRequest,
    ContractMilestonePublic,
    ContractMilestoneStatus,
    Pagination,
)
from app.services.ledger import get_or_create_account, append_event


router = APIRouter(prefix="/milestones", tags=["ContractMilestones"])


def _to_public(m: ContractMilestone) -> ContractMilestonePublic:
    return ContractMilestonePublic(
        id=str(m.id),
        contract_id=str(m.contract_id),
        title=m.title,
        description=m.description or "",
        order_index=int(m.order_index or 0),
        status=ContractMilestoneStatus(m.status.value),
        amount_value=str(m.amount_value),
        currency=m.currency,
        required_runs=m.required_runs,
        completed_runs=int(m.completed_runs or 0),
        accepted_at=m.accepted_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


async def _get_agent_for_user(session: DbSession, user_id: str | None) -> Agent | None:
    if not user_id:
        return None
    try:
        uid = UUID(user_id)
    except ValueError:
        return None
    r = await session.execute(select(Agent).where(Agent.owner_user_id == uid).limit(1))
    return r.scalar_one_or_none()


async def _user_owns_agent(session: DbSession, user_id: str | None, agent_id: UUID) -> bool:
    if not user_id:
        return False
    try:
        uid = UUID(user_id)
    except ValueError:
        return False
    r = await session.execute(select(Agent.id).where(Agent.id == agent_id, Agent.owner_user_id == uid).limit(1))
    return r.scalar_one_or_none() is not None


async def _sum_milestones_amount(session: DbSession, contract_id: UUID, currency: str) -> Decimal:
    q = select(func.coalesce(func.sum(ContractMilestone.amount_value), 0)).where(
        ContractMilestone.contract_id == contract_id,
        ContractMilestone.currency == currency,
    )
    r = await session.execute(q)
    return Decimal(r.scalar_one() or 0)


@router.post("/contracts/{contract_id}", response_model=ContractMilestonePublic, status_code=201)
async def create_milestone(
    contract_id: UUID,
    body: ContractMilestoneCreateRequest,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Only employer can create milestones (requires auth).
    if not await _user_owns_agent(session, user_id, contract.employer_agent_id):
        raise HTTPException(status_code=403, detail="Only contract employer can create milestones")

    if body.currency != contract.currency:
        raise HTTPException(status_code=400, detail="Milestone currency must match contract currency")

    amount = Decimal(body.amount_value)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Milestone amount_value must be > 0")

    # For fixed contracts, milestones must sum <= fixed_amount_value.
    if contract.payment_model == PaymentModelEnum.fixed:
        if not contract.fixed_amount_value:
            raise HTTPException(status_code=400, detail="Fixed contract requires fixed_amount_value to use milestones")
        current_total = await _sum_milestones_amount(session, contract_id, contract.currency)
        if current_total + amount > Decimal(contract.fixed_amount_value):
            raise HTTPException(status_code=400, detail="Sum of milestones exceeds contract fixed amount")

    m = ContractMilestone(
        contract_id=contract_id,
        title=body.title,
        description=body.description or "",
        order_index=body.order_index,
        status=ContractMilestoneStatusEnum.pending,
        amount_value=amount,
        currency=body.currency,
        required_runs=body.required_runs,
        completed_runs=0,
    )
    session.add(m)
    await session.flush()
    await session.refresh(m)
    return _to_public(m)


@router.get("/contracts/{contract_id}", response_model=Pagination[ContractMilestonePublic])
async def list_milestones(
    contract_id: UUID,
    session: DbSession,
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
):
    q = select(ContractMilestone).where(ContractMilestone.contract_id == contract_id).order_by(
        ContractMilestone.order_index.asc(), ContractMilestone.created_at.asc()
    ).limit(limit + 1)
    if cursor:
        try:
            q = q.where(ContractMilestone.id > UUID(cursor))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid pagination cursor") from None
    r = await session.execute(q)
    rows = r.scalars().all()
    next_cursor = str(rows[-1].id) if len(rows) > limit else None
    items = rows[:limit]
    return Pagination(items=[_to_public(m) for m in items], next_cursor=next_cursor)


@router.get("/{milestone_id}", response_model=ContractMilestonePublic)
async def get_milestone(milestone_id: UUID, session: DbSession):
    m = await session.get(ContractMilestone, milestone_id)
    if not m:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return _to_public(m)


@router.patch("/{milestone_id}", response_model=ContractMilestonePublic)
async def update_milestone(
    milestone_id: UUID,
    body: ContractMilestoneUpdateRequest,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    m = await session.get(ContractMilestone, milestone_id)
    if not m:
        raise HTTPException(status_code=404, detail="Milestone not found")
    contract = await session.get(Contract, m.contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not await _user_owns_agent(session, user_id, contract.employer_agent_id):
        raise HTTPException(status_code=403, detail="Only contract employer can update milestones")

    if body.currency and body.currency != contract.currency:
        raise HTTPException(status_code=400, detail="Milestone currency must match contract currency")

    if body.amount_value is not None:
        new_amount = Decimal(body.amount_value)
        if new_amount <= 0:
            raise HTTPException(status_code=400, detail="Milestone amount_value must be > 0")
        if contract.payment_model == PaymentModelEnum.fixed:
            current_total = await _sum_milestones_amount(session, contract.id, contract.currency)
            # replace old amount with new amount
            replaced_total = current_total - Decimal(m.amount_value) + new_amount
            if contract.fixed_amount_value and replaced_total > Decimal(contract.fixed_amount_value):
                raise HTTPException(status_code=400, detail="Sum of milestones exceeds contract fixed amount")
        m.amount_value = new_amount

    if body.title is not None:
        m.title = body.title
    if body.description is not None:
        m.description = body.description
    if body.order_index is not None:
        m.order_index = body.order_index
    if body.required_runs is not None:
        m.required_runs = body.required_runs
    if body.status is not None:
        m.status = ContractMilestoneStatusEnum(body.status.value)

    m.updated_at = datetime.now(timezone.utc)
    await session.flush()
    await session.refresh(m)
    return _to_public(m)


@router.post("/{milestone_id}/submit", response_model=ContractMilestonePublic)
async def submit_milestone(
    milestone_id: UUID,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    m = await session.get(ContractMilestone, milestone_id)
    if not m:
        raise HTTPException(status_code=404, detail="Milestone not found")
    contract = await session.get(Contract, m.contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.status != ContractStatusEnum.active:
        raise HTTPException(status_code=400, detail="Contract must be active")

    if not await _user_owns_agent(session, user_id, contract.worker_agent_id):
        raise HTTPException(status_code=403, detail="Only contract worker can submit milestone")

    if m.status not in (ContractMilestoneStatusEnum.active, ContractMilestoneStatusEnum.pending, ContractMilestoneStatusEnum.rejected):
        raise HTTPException(status_code=400, detail="Milestone cannot be submitted in current status")
    m.status = ContractMilestoneStatusEnum.submitted
    m.updated_at = datetime.now(timezone.utc)
    await session.flush()
    await session.refresh(m)
    return _to_public(m)


@router.post("/{milestone_id}/accept", response_model=ContractMilestonePublic)
async def accept_milestone(
    milestone_id: UUID,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    m = await session.get(ContractMilestone, milestone_id)
    if not m:
        raise HTTPException(status_code=404, detail="Milestone not found")
    contract = await session.get(Contract, m.contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.status != ContractStatusEnum.active:
        raise HTTPException(status_code=400, detail="Contract must be active")

    if not await _user_owns_agent(session, user_id, contract.employer_agent_id):
        raise HTTPException(status_code=403, detail="Only contract employer can accept milestone")

    if m.status not in (ContractMilestoneStatusEnum.submitted, ContractMilestoneStatusEnum.active):
        raise HTTPException(status_code=400, detail="Milestone must be submitted/active to accept")

    # Fixed partial payout from escrow on accept.
    if contract.payment_model == PaymentModelEnum.fixed:
        if not contract.fixed_amount_value:
            raise HTTPException(status_code=400, detail="Fixed contract missing fixed_amount_value")
        escrow_acc = await get_or_create_account(session, "contract_escrow", contract.id)
        worker_acc = await get_or_create_account(session, "agent", contract.worker_agent_id)

        paid_q = select(func.coalesce(func.sum(LedgerEvent.amount_value), 0)).where(
            LedgerEvent.type == LedgerEventTypeEnum.contract_payout,
            LedgerEvent.dst_account_id == worker_acc.id,
            LedgerEvent.amount_currency == contract.currency,
            LedgerEvent.metadata_.contains({"contract_id": str(contract.id), "milestone_id": str(m.id)}),
        )
        paid_r = await session.execute(paid_q)
        already_paid: Decimal = paid_r.scalar_one()
        target = Decimal(m.amount_value)
        delta_target = target - already_paid
        if delta_target > 0:
            paid_out_q = select(func.coalesce(func.sum(LedgerEvent.amount_value), 0)).where(
                LedgerEvent.type == LedgerEventTypeEnum.contract_payout,
                LedgerEvent.src_account_id == escrow_acc.id,
                LedgerEvent.amount_currency == contract.currency,
                LedgerEvent.metadata_.contains({"contract_id": str(contract.id)}),
            )
            escrowed_q = select(func.coalesce(func.sum(LedgerEvent.amount_value), 0)).where(
                LedgerEvent.type == LedgerEventTypeEnum.contract_escrow,
                LedgerEvent.dst_account_id == escrow_acc.id,
                LedgerEvent.amount_currency == contract.currency,
                LedgerEvent.metadata_.contains({"contract_id": str(contract.id)}),
            )
            paid_out_r = await session.execute(paid_out_q)
            escrowed_r = await session.execute(escrowed_q)
            paid_out_total: Decimal = paid_out_r.scalar_one()
            escrowed_total: Decimal = escrowed_r.scalar_one()
            available = escrowed_total - paid_out_total
            pay_delta = min(available, delta_target)
            if pay_delta > 0:
                await append_event(
                    session,
                    LedgerEventTypeEnum.contract_payout,
                    contract.currency,
                    pay_delta,
                    src_account_id=escrow_acc.id,
                    dst_account_id=worker_acc.id,
                    metadata={
                        "type": "milestone_payout",
                        "contract_id": str(contract.id),
                        "milestone_id": str(m.id),
                        "payment_model": contract.payment_model.value,
                    },
                )

    m.status = ContractMilestoneStatusEnum.paid if contract.payment_model == PaymentModelEnum.fixed else ContractMilestoneStatusEnum.accepted
    m.accepted_at = datetime.now(timezone.utc)
    m.updated_at = datetime.now(timezone.utc)
    await session.flush()
    await session.refresh(m)
    return _to_public(m)


@router.post("/{milestone_id}/reject", response_model=ContractMilestonePublic)
async def reject_milestone(
    milestone_id: UUID,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    m = await session.get(ContractMilestone, milestone_id)
    if not m:
        raise HTTPException(status_code=404, detail="Milestone not found")
    contract = await session.get(Contract, m.contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if not await _user_owns_agent(session, user_id, contract.employer_agent_id):
        raise HTTPException(status_code=403, detail="Only contract employer can reject milestone")
    if m.status not in (ContractMilestoneStatusEnum.submitted, ContractMilestoneStatusEnum.active):
        raise HTTPException(status_code=400, detail="Milestone must be submitted/active to reject")
    m.status = ContractMilestoneStatusEnum.rejected
    m.updated_at = datetime.now(timezone.utc)
    await session.flush()
    await session.refresh(m)
    return _to_public(m)


@router.post("/{milestone_id}/cancel", response_model=ContractMilestonePublic)
async def cancel_milestone(
    milestone_id: UUID,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    m = await session.get(ContractMilestone, milestone_id)
    if not m:
        raise HTTPException(status_code=404, detail="Milestone not found")
    contract = await session.get(Contract, m.contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if not await _user_owns_agent(session, user_id, contract.employer_agent_id):
        raise HTTPException(status_code=403, detail="Only contract employer can cancel milestone")
    if m.status == ContractMilestoneStatusEnum.paid:
        raise HTTPException(status_code=400, detail="Cannot cancel a paid milestone")
    m.status = ContractMilestoneStatusEnum.cancelled
    m.updated_at = datetime.now(timezone.utc)
    await session.flush()
    await session.refresh(m)
    return _to_public(m)

