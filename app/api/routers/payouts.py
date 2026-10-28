from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from app.api.deps import DbSession, require_auth, require_platform_admin
from app.db.models import PayoutRequest, PayoutRequestStatusEnum
from app.schemas import (
    Money,
    PayoutRequestActionRequest,
    PayoutRequestCreateRequest,
    PayoutRequestPublic,
    PayoutRequestsResponse,
)
from app.services.ledger import append_event, balance_for_account, get_or_create_account, is_ledger_invariant_halted
from app.db.models import LedgerEventTypeEnum

router = APIRouter(tags=["Payouts"])


def _money_to_decimal(money: Money) -> Decimal:
    try:
        value = Decimal(money.amount)
    except Exception as exc:  # pragma: no cover - pydantic already constrains format
        raise HTTPException(status_code=400, detail="Invalid amount") from exc
    return value


def _serialize_payout_request(row: PayoutRequest) -> PayoutRequestPublic:
    return PayoutRequestPublic(
        id=str(row.id),
        user_id=str(row.user_id),
        amount=Money(amount=str(row.amount_value), currency=row.amount_currency),
        status=row.status.value if hasattr(row.status, "value") else str(row.status),
        method=row.method,
        destination=row.destination,
        admin_notes=row.admin_notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
        processed_at=row.processed_at,
    )


async def _get_payout_or_404(session: DbSession, payout_id: str) -> PayoutRequest:
    try:
        parsed_id = UUID(payout_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Payout request not found") from exc
    row = await session.get(PayoutRequest, parsed_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Payout request not found")
    return row


@router.post("/payouts/request", response_model=PayoutRequestPublic, status_code=201)
async def create_payout_request(
    body: PayoutRequestCreateRequest,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    if await is_ledger_invariant_halted(session):
        raise HTTPException(status_code=503, detail="Ledger invariant violated; operations temporarily blocked")

    amount_value = _money_to_decimal(body.amount)
    if amount_value <= 0:
        raise HTTPException(status_code=400, detail="Payout amount must be positive")

    currency = (body.amount.currency or "").strip().upper()
    if currency != "ACP":
        raise HTTPException(status_code=400, detail="Payouts currently support ACP only")

    user_uuid = UUID(user_id)
    user_acc = await get_or_create_account(session, "user", user_uuid)
    balances = await balance_for_account(session, user_acc.id, currency)
    available = balances.get(currency) or Decimal(0)
    if available < amount_value:
        raise HTTPException(status_code=402, detail="Insufficient balance")

    duplicate = (
        await session.execute(
            select(PayoutRequest)
            .where(
                PayoutRequest.user_id == user_uuid,
                PayoutRequest.status.in_([
                    PayoutRequestStatusEnum.pending,
                    PayoutRequestStatusEnum.approved,
                ]),
                PayoutRequest.amount_currency == currency,
                PayoutRequest.amount_value == amount_value,
                PayoutRequest.method == body.method.value,
                PayoutRequest.destination == body.destination,
            )
            .order_by(PayoutRequest.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="Matching payout request is already in progress")

    hold_event = await append_event(
        session,
        LedgerEventTypeEnum.withdraw,
        currency,
        amount_value,
        src_account_id=user_acc.id,
        metadata={
            "type": "creator_payout_request_hold",
            "user_id": user_id,
            "method": body.method.value,
            "destination": body.destination,
        },
    )
    row = PayoutRequest(
        user_id=user_uuid,
        amount_currency=currency,
        amount_value=amount_value,
        status=PayoutRequestStatusEnum.pending,
        method=body.method.value,
        destination=body.destination,
        request_ledger_event_id=hold_event.id,
    )
    session.add(row)
    await session.flush()
    hold_event.metadata_ = {
        **(hold_event.metadata_ or {}),
        "payout_request_id": str(row.id),
    }
    await session.flush()
    await session.refresh(row)
    return _serialize_payout_request(row)


@router.get("/payouts", response_model=PayoutRequestsResponse)
async def list_my_payout_requests(
    session: DbSession,
    user_id: str = Depends(require_auth),
    status_filter: str | None = Query(default=None, alias="status"),
):
    query = select(PayoutRequest).where(PayoutRequest.user_id == UUID(user_id)).order_by(PayoutRequest.created_at.desc())
    if status_filter:
        normalized = status_filter.strip().lower()
        allowed = {item.value for item in PayoutRequestStatusEnum}
        if normalized not in allowed:
            raise HTTPException(status_code=400, detail="Unsupported payout status filter")
        query = query.where(PayoutRequest.status == normalized)
    rows = (await session.execute(query)).scalars().all()
    return PayoutRequestsResponse(items=[_serialize_payout_request(row) for row in rows])


@router.get("/admin/payouts", response_model=PayoutRequestsResponse)
async def list_admin_payout_requests(
    session: DbSession,
    _admin_user_id: str = Depends(require_platform_admin),
    status_filter: str | None = Query(default=None, alias="status"),
):
    query = select(PayoutRequest).order_by(PayoutRequest.created_at.desc())
    if status_filter:
        normalized = status_filter.strip().lower()
        allowed = {item.value for item in PayoutRequestStatusEnum}
        if normalized not in allowed:
            raise HTTPException(status_code=400, detail="Unsupported payout status filter")
        query = query.where(PayoutRequest.status == normalized)
    rows = (await session.execute(query)).scalars().all()
    return PayoutRequestsResponse(items=[_serialize_payout_request(row) for row in rows])


@router.post("/admin/payouts/{payout_id}/approve", response_model=PayoutRequestPublic)
async def approve_payout_request(
    payout_id: str,
    body: PayoutRequestActionRequest,
    session: DbSession,
    admin_user_id: str = Depends(require_platform_admin),
):
    row = await _get_payout_or_404(session, payout_id)
    if row.status != PayoutRequestStatusEnum.pending:
        raise HTTPException(status_code=409, detail=f"Payout request is already {row.status.value}")

    await get_or_create_account(session, "user", UUID(str(row.user_id)))
    approval_event = await append_event(
        session,
        LedgerEventTypeEnum.transfer,
        row.amount_currency,
        Decimal(row.amount_value),
        metadata={
            "type": "creator_payout_approved",
            "payout_request_id": str(row.id),
            "user_id": str(row.user_id),
            "method": row.method,
            "destination": row.destination,
            "approved_by": admin_user_id,
            "admin_notes": body.admin_notes,
            "request_ledger_event_id": str(row.request_ledger_event_id) if row.request_ledger_event_id else None,
        },
    )
    row.status = PayoutRequestStatusEnum.approved
    row.approval_ledger_event_id = approval_event.id
    row.admin_notes = body.admin_notes
    row.processed_at = datetime.now(UTC)
    row.updated_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(row)
    return _serialize_payout_request(row)


@router.post("/admin/payouts/{payout_id}/reject", response_model=PayoutRequestPublic)
async def reject_payout_request(
    payout_id: str,
    body: PayoutRequestActionRequest,
    session: DbSession,
    admin_user_id: str = Depends(require_platform_admin),
):
    row = await _get_payout_or_404(session, payout_id)
    if row.status != PayoutRequestStatusEnum.pending:
        raise HTTPException(status_code=409, detail=f"Payout request is already {row.status.value}")

    user_acc = await get_or_create_account(session, "user", UUID(str(row.user_id)))
    rejection_event = await append_event(
        session,
        LedgerEventTypeEnum.deposit,
        row.amount_currency,
        Decimal(row.amount_value),
        dst_account_id=user_acc.id,
        metadata={
            "type": "creator_payout_rejected_refund",
            "payout_request_id": str(row.id),
            "user_id": str(row.user_id),
            "method": row.method,
            "destination": row.destination,
            "rejected_by": admin_user_id,
            "admin_notes": body.admin_notes,
        },
    )
    row.status = PayoutRequestStatusEnum.rejected
    row.rejection_ledger_event_id = rejection_event.id
    row.admin_notes = body.admin_notes
    row.processed_at = datetime.now(UTC)
    row.updated_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(row)
    return _serialize_payout_request(row)
