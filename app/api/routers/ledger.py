from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Query, HTTPException, Depends

from app.schemas import (
    DepositRequest,
    WithdrawRequest,
    AllocateRequest,
    LedgerEventPublic,
    LedgerEventType,
    LedgerAccountPublic,
    BalanceResponse,
    Money,
    Pagination,
    BalanceItem,
)
from app.api.deps import DbSession, require_auth, is_platform_admin_user
from app.config import get_settings
from app.db.models import LedgerEvent, LedgerEventTypeEnum, Account, Agent
from app.services.ledger import get_or_create_account, append_event, balance_for_account, is_ledger_invariant_halted
from sqlalchemy import select

router = APIRouter(prefix="/ledger", tags=["Ledger"])


async def _assert_deposit_allowed(session: DbSession, user_id: str) -> None:
    """Production deposits are operator-only. Non-prod keeps the test faucet."""
    settings = get_settings()
    if settings.environment != "production":
        return
    if await is_platform_admin_user(session, user_id):
        return
    raise HTTPException(
        status_code=403,
        detail="Ledger deposit is restricted to platform operators in production",
    )


async def _assert_owner_access(
    session: DbSession,
    user_id: str,
    owner_type: str,
    owner_id: UUID,
) -> None:
    ot = (owner_type or "").strip().lower()
    if ot == "user":
        if str(owner_id) != user_id and not await is_platform_admin_user(session, user_id):
            raise HTTPException(status_code=403, detail="Forbidden account owner")
        return
    if ot == "agent":
        if await is_platform_admin_user(session, user_id):
            return
        agent = await session.get(Agent, owner_id)
        if not agent or str(agent.owner_user_id or "") != user_id:
            raise HTTPException(status_code=403, detail="Forbidden account owner")
        return
    if ot == "pool_treasury":
        from app.db.models import Pool
        pool = await session.get(Pool, owner_id)
        if not pool:
            raise HTTPException(status_code=404, detail="Pool not found")
        # Non-prod keeps open pool access for the ledger faucet / pool tests.
        # Production restricts pool treasury ledger ops to platform operators.
        if get_settings().environment != "production" or await is_platform_admin_user(session, user_id):
            return
        raise HTTPException(status_code=403, detail="Forbidden account owner")
    raise HTTPException(status_code=403, detail="Unsupported owner_type for user access")


@router.get("/accounts", response_model=Pagination[LedgerAccountPublic])
async def list_accounts(
    session: DbSession,
    user_id: str = Depends(require_auth),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    owner_type: str | None = Query(None),
    owner_id: UUID | None = Query(None),
):
    q = select(Account).order_by(Account.created_at.desc()).limit(limit + 1)
    if cursor:
        try:
            q = q.where(Account.id < UUID(cursor))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid pagination cursor") from None
    if owner_id is not None:
        if not owner_type:
            raise HTTPException(status_code=400, detail="owner_type is required when owner_id is provided")
        await _assert_owner_access(session, user_id, owner_type, owner_id)
        q = q.where(Account.owner_type == owner_type, Account.owner_id == owner_id)
    elif owner_type:
        is_admin = await is_platform_admin_user(session, user_id)
        if owner_type.strip().lower() != "user" and not is_admin:
            raise HTTPException(status_code=403, detail="Forbidden account owner filter")
        q = q.where(Account.owner_type == owner_type)
        if owner_type.strip().lower() == "user" and not is_admin:
            q = q.where(Account.owner_id == UUID(user_id))
    else:
        q = q.where((Account.owner_type == "user") & (Account.owner_id == UUID(user_id)))
    r = await session.execute(q)
    rows = r.scalars().all()
    next_cursor = str(rows[-1].id) if len(rows) > limit else None
    items = rows[:limit]
    return Pagination(
        items=[
            LedgerAccountPublic(
                id=str(a.id),
                owner_type=a.owner_type,
                owner_id=str(a.owner_id),
                account_kind=a.account_kind,
                created_at=a.created_at,
            )
            for a in items
        ],
        next_cursor=next_cursor,
    )


@router.get("/accounts/{account_id}", response_model=LedgerAccountPublic)
async def get_account(account_id: UUID, session: DbSession, user_id: str = Depends(require_auth)):
    acc = await session.get(Account, account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    await _assert_owner_access(session, user_id, acc.owner_type, acc.owner_id)
    return LedgerAccountPublic(
        id=str(acc.id),
        owner_type=acc.owner_type,
        owner_id=str(acc.owner_id),
        account_kind=acc.account_kind,
        created_at=acc.created_at,
    )


@router.post("/deposit", response_model=LedgerEventPublic, status_code=201)
async def deposit(body: DepositRequest, session: DbSession, user_id: str = Depends(require_auth)):
    if await is_ledger_invariant_halted(session):
        raise HTTPException(status_code=503, detail="Ledger invariant violated; operations temporarily blocked")
    await _assert_deposit_allowed(session, user_id)
    owner_id = UUID(body.account_owner_id)
    await _assert_owner_access(
        session,
        user_id,
        body.account_owner_type,
        owner_id,
    )
    acc = await get_or_create_account(session, body.account_owner_type, owner_id)
    value = Decimal(body.amount.amount)
    if value <= 0:
        raise HTTPException(status_code=400, detail="Deposit amount must be positive")
    ev = await append_event(
        session,
        LedgerEventTypeEnum.deposit,
        body.amount.currency,
        value,
        dst_account_id=acc.id,
        metadata={"reference": body.reference} if body.reference else None,
    )
    return LedgerEventPublic(
        id=str(ev.id),
        ts=ev.ts,
        type=LedgerEventType(ev.type.value),
        amount=Money(amount=str(ev.amount_value), currency=ev.amount_currency),
        src_account_id=None,
        dst_account_id=str(ev.dst_account_id),
        metadata=ev.metadata_,
    )


@router.post("/withdraw", response_model=LedgerEventPublic, status_code=201)
async def withdraw(body: WithdrawRequest, session: DbSession, user_id: str = Depends(require_auth)):
    if await is_ledger_invariant_halted(session):
        raise HTTPException(status_code=503, detail="Ledger invariant violated; operations temporarily blocked")
    owner_id = UUID(body.account_owner_id)
    await _assert_owner_access(session, user_id, body.account_owner_type, owner_id)
    acc = await get_or_create_account(session, body.account_owner_type, owner_id)
    value = Decimal(body.amount.amount)
    if value <= 0:
        raise HTTPException(status_code=400, detail="Withdrawal amount must be positive")
    balances = await balance_for_account(session, acc.id, body.amount.currency)
    available = balances.get(body.amount.currency) or Decimal(0)
    if available < value:
        raise HTTPException(status_code=402, detail="Insufficient balance")
    ev = await append_event(
        session,
        LedgerEventTypeEnum.withdraw,
        body.amount.currency,
        value,
        src_account_id=acc.id,
        metadata={"reference": body.reference} if body.reference else None,
    )
    return LedgerEventPublic(
        id=str(ev.id),
        ts=ev.ts,
        type=LedgerEventType(ev.type.value),
        amount=Money(amount=str(ev.amount_value), currency=ev.amount_currency),
        src_account_id=str(ev.src_account_id),
        dst_account_id=None,
        metadata=ev.metadata_,
    )


@router.post("/allocate", response_model=LedgerEventPublic, status_code=201)
async def allocate(body: AllocateRequest, session: DbSession, user_id: str = Depends(require_auth)):
    if await is_ledger_invariant_halted(session):
        raise HTTPException(status_code=503, detail="Ledger invariant violated; operations temporarily blocked")
    from app.db.models import Pool
    q = select(Pool).where(Pool.id == UUID(body.pool_id))
    r = await session.execute(q)
    pool = r.scalar_one_or_none()
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    pool_owner_agent_id = getattr(pool, "owner_agent_id", None)
    if not pool_owner_agent_id:
        raise HTTPException(status_code=403, detail="Pool has no owner; allocate is blocked")
    await _assert_owner_access(session, user_id, "agent", UUID(str(pool_owner_agent_id)))
    pool_acc = await get_or_create_account(session, "pool_treasury", pool.id)
    value = Decimal(body.amount.amount)
    ev = await append_event(
        session,
        LedgerEventTypeEnum.allocate,
        body.amount.currency,
        value,
        src_account_id=pool_acc.id,
        metadata={"strategy_id": body.strategy_id, "run_params": body.run_params},
    )
    return LedgerEventPublic(
        id=str(ev.id),
        ts=ev.ts,
        type=LedgerEventType(ev.type.value),
        amount=Money(amount=str(ev.amount_value), currency=ev.amount_currency),
        src_account_id=str(ev.src_account_id),
        dst_account_id=str(ev.dst_account_id) if ev.dst_account_id else None,
        metadata=ev.metadata_,
    )


@router.get("/events", response_model=Pagination[LedgerEventPublic])
async def list_events(
    session: DbSession,
    user_id: str = Depends(require_auth),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    account_id: UUID | None = Query(None),
    type: LedgerEventType | None = Query(None),
):
    q = select(LedgerEvent).order_by(LedgerEvent.ts.desc()).limit(limit + 1)
    if cursor:
        try:
            q = q.where(LedgerEvent.id < UUID(cursor))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid pagination cursor") from None
    if account_id:
        acc = await session.get(Account, account_id)
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")
        await _assert_owner_access(session, user_id, acc.owner_type, acc.owner_id)
        q = q.where((LedgerEvent.src_account_id == account_id) | (LedgerEvent.dst_account_id == account_id))
    else:
        # Without an explicit account filter, return events that touch any
        # account the user owns directly OR via an agent they own. The previous
        # query only matched `owner_type=user` accounts, so contract payouts and
        # other agent-to-agent events were invisible to the very user who
        # initiated them. We use a subquery on Account so events where BOTH
        # src and dst happen to be owned by the user (e.g. a contract payout
        # between two of their agents) are not duplicated by the OR join.
        owned_agent_ids_subq = select(Agent.id).where(Agent.owner_user_id == UUID(user_id))
        owned_account_ids_subq = (
            select(Account.id)
            .where(
                ((Account.owner_type == "user") & (Account.owner_id == UUID(user_id)))
                | ((Account.owner_type == "agent") & (Account.owner_id.in_(owned_agent_ids_subq)))
            )
        )
        q = q.where(
            (LedgerEvent.src_account_id.in_(owned_account_ids_subq))
            | (LedgerEvent.dst_account_id.in_(owned_account_ids_subq))
        )
    if type:
        q = q.where(LedgerEvent.type == type.value)
    r = await session.execute(q)
    rows = r.scalars().all()
    next_cursor = str(rows[-1].id) if len(rows) > limit else None
    items = rows[:limit]
    return Pagination(
        items=[
            LedgerEventPublic(
                id=str(e.id),
                ts=e.ts,
                type=LedgerEventType(e.type.value),
                amount=Money(amount=str(e.amount_value), currency=e.amount_currency),
                src_account_id=str(e.src_account_id) if e.src_account_id else None,
                dst_account_id=str(e.dst_account_id) if e.dst_account_id else None,
                metadata=e.metadata_,
            )
            for e in items
        ],
        next_cursor=next_cursor,
    )


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    session: DbSession,
    owner_type: str,
    owner_id: UUID,
    user_id: str = Depends(require_auth),
):
    await _assert_owner_access(session, user_id, owner_type, owner_id)
    acc = await get_or_create_account(session, owner_type, owner_id)
    balances = await balance_for_account(session, acc.id)
    return BalanceResponse(
        account_id=str(acc.id),
        balances=[BalanceItem(currency=c, amount=str(v)) for c, v in balances.items()],
    )
