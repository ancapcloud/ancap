"""ROP-04 renewal events: record due renewals and measure the due cohort.

Records are operator evidence. Nothing here moves money; ``paid`` only records
that an external payment reference was confirmed by an operator.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RenewalEvent

# Allowed status transitions. paid and cancelled are terminal.
_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"paid", "failed", "cancelled"}),
    "failed": frozenset({"paid", "cancelled"}),
    "paid": frozenset(),
    "cancelled": frozenset(),
}


class RenewalConflict(Exception):
    """Same project/client/subscription/due_at already recorded."""


class InvalidTransition(Exception):
    def __init__(self, current: str, target: str):
        super().__init__(f"Cannot change renewal status from {current} to {target}")
        self.current = current
        self.target = target


async def create_event(
    session: AsyncSession,
    *,
    project_id: str,
    client_id: str,
    subscription_id: str | None,
    renewal_type: str,
    due_at: datetime,
    amount_due: Decimal,
    currency: str,
    note: str | None,
    recorded_by_user_id: str | None,
) -> RenewalEvent:
    now = datetime.now(timezone.utc)
    row = RenewalEvent(
        id=str(uuid4()),
        project_id=project_id,
        client_id=client_id,
        subscription_id=subscription_id,
        renewal_type=renewal_type,
        due_at=due_at,
        amount_due=amount_due,
        currency=currency,
        status="pending",
        note=note,
        recorded_by_user_id=recorded_by_user_id,
        created_at=now,
        updated_at=now,
    )
    try:
        async with session.begin_nested():
            session.add(row)
            await session.flush()
    except IntegrityError as exc:
        raise RenewalConflict() from exc
    return row


async def get_event(session: AsyncSession, event_id: str, *, for_update: bool = False) -> RenewalEvent | None:
    stmt = select(RenewalEvent).where(RenewalEvent.id == event_id)
    if for_update:
        stmt = stmt.with_for_update()
    return (await session.execute(stmt)).scalar_one_or_none()


async def list_events(
    session: AsyncSession,
    *,
    project_id: str | None = None,
    client_id: str | None = None,
    status: str | None = None,
    due_from: datetime | None = None,
    due_to: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[RenewalEvent], int]:
    filters = []
    if project_id:
        filters.append(RenewalEvent.project_id == project_id)
    if client_id:
        filters.append(RenewalEvent.client_id == client_id)
    if status:
        filters.append(RenewalEvent.status == status)
    if due_from:
        filters.append(RenewalEvent.due_at >= due_from)
    if due_to:
        filters.append(RenewalEvent.due_at < due_to)
    total = (await session.execute(select(func.count()).select_from(RenewalEvent).where(*filters))).scalar_one()
    rows = (
        await session.execute(
            select(RenewalEvent)
            .where(*filters)
            .order_by(RenewalEvent.due_at.asc(), RenewalEvent.id.asc())
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()
    return list(rows), int(total)


async def update_status(
    session: AsyncSession,
    event_id: str,
    *,
    status: str,
    renewed_at: datetime | None,
    payment_reference: str | None,
    note: str | None,
) -> RenewalEvent | None:
    """Apply a lifecycle transition. Repeating the same final state is idempotent."""
    row = await get_event(session, event_id, for_update=True)
    if row is None:
        return None
    if row.status == status:
        return row
    if status not in _TRANSITIONS.get(row.status, frozenset()):
        raise InvalidTransition(row.status, status)
    row.status = status
    if status == "paid":
        row.renewed_at = renewed_at or datetime.now(timezone.utc)
    if payment_reference is not None:
        row.payment_reference = payment_reference
    if note is not None:
        row.note = note
    row.updated_at = datetime.now(timezone.utc)
    await session.flush()
    return row


def format_amount(value: Decimal | None) -> str:
    if value is None:
        return "0"
    normalized = Decimal(value).normalize()
    # normalize() may produce exponent form (1E+2); render as plain digits.
    return format(normalized, "f")


async def cohort_summary(
    session: AsyncSession,
    *,
    due_from: datetime,
    due_to: datetime,
    project_id: str | None = None,
) -> dict:
    filters = [RenewalEvent.due_at >= due_from, RenewalEvent.due_at < due_to]
    if project_id:
        filters.append(RenewalEvent.project_id == project_id)
    rows = (
        await session.execute(
            select(
                RenewalEvent.status,
                RenewalEvent.currency,
                func.count(),
                func.coalesce(func.sum(RenewalEvent.amount_due), 0),
            )
            .where(*filters)
            .group_by(RenewalEvent.status, RenewalEvent.currency)
        )
    ).all()

    counts = {"pending": 0, "paid": 0, "failed": 0, "cancelled": 0}
    due_by_currency: dict[str, Decimal] = defaultdict(Decimal)
    paid_by_currency: dict[str, Decimal] = defaultdict(Decimal)
    for status, currency, count, amount in rows:
        counts[status] = counts.get(status, 0) + int(count)
        due_by_currency[currency] += Decimal(amount)
        if status == "paid":
            paid_by_currency[currency] += Decimal(amount)

    resolved = counts["paid"] + counts["failed"] + counts["cancelled"]
    rate = None
    if resolved:
        rate = str((Decimal(counts["paid"]) / Decimal(resolved)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN))

    return {
        "project_id": project_id,
        "due_from": due_from,
        "due_to": due_to,
        "total": sum(counts.values()),
        **counts,
        "renewal_rate": rate,
        "totals": [
            {
                "currency": currency,
                "due": format_amount(due_by_currency[currency]),
                "paid": format_amount(paid_by_currency.get(currency, Decimal(0))),
            }
            for currency in sorted(due_by_currency)
        ],
    }
