"""Paid "Sponsored" placement for marketplace listings.

Revenue line from ROADMAP-MONETIZATION.md ("premium placement"): a listing
owner pays a daily ACP fee to be ranked first in its category for a fixed
window. Placement is scarce (a few slots per category) and always disclosed
to buyers as sponsored, so ranking stays honest for everyone else.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.constants import PLATFORM_ACCOUNT_OWNER_ID
from app.db.models import (
    LedgerEventTypeEnum,
    Listing,
    ListingPromotion,
    ListingStatusEnum,
    Strategy,
)
from app.services.ledger import (
    append_event,
    balance_for_account,
    get_or_create_account,
    is_ledger_invariant_halted,
    lock_account_for_spend,
)


@dataclass(frozen=True)
class PromotionPricing:
    enabled: bool
    daily_fee: Decimal
    currency: str
    max_days: int
    slots_per_category: int


def pricing() -> PromotionPricing:
    settings = get_settings()
    return PromotionPricing(
        enabled=bool(settings.listing_promotion_enabled),
        daily_fee=Decimal(str(settings.listing_promotion_daily_fee or "0")),
        currency=(settings.listing_promotion_currency or "ACP").upper(),
        max_days=max(1, int(settings.listing_promotion_max_days)),
        slots_per_category=max(1, int(settings.listing_promotion_slots_per_category)),
    )


def _now() -> datetime:
    return datetime.now(UTC)


async def active_until(session: AsyncSession, listing_id: str) -> datetime | None:
    value = await session.scalar(
        select(func.max(ListingPromotion.ends_at)).where(
            ListingPromotion.listing_id == listing_id,
            ListingPromotion.ends_at > _now(),
        )
    )
    return value


async def _lock(session: AsyncSession, key: str) -> None:
    await session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": key})


async def lock_listing_purchase(session: AsyncSession, listing_id: str) -> None:
    """Serialize purchases for one listing (taken before the idempotency lookup).

    Lock order everywhere: listing -> category -> account spend lock.
    """
    await _lock(session, f"listing_promotion:listing:{listing_id}")


async def purchase(
    session: AsyncSession,
    *,
    listing: Listing,
    strategy: Strategy,
    days: int,
    purchased_by_user_id: str | None,
) -> ListingPromotion:
    cfg = pricing()
    if not cfg.enabled:
        raise HTTPException(status_code=503, detail="Sponsored placement is not available")
    if days < 1 or days > cfg.max_days:
        raise HTTPException(status_code=422, detail=f"days must be between 1 and {cfg.max_days}")
    if listing.status != ListingStatusEnum.active:
        raise HTTPException(status_code=409, detail="Only active listings can be promoted")
    if await is_ledger_invariant_halted(session):
        raise HTTPException(status_code=503, detail="Ledger is halted; payments are paused")

    vertical_id = str(strategy.vertical_id) if strategy.vertical_id else None
    await lock_listing_purchase(session, str(listing.id))
    await _lock(session, f"listing_promotion:vertical:{vertical_id}")

    now = _now()
    current_end = await active_until(session, str(listing.id))
    if current_end is None:
        # New placement: enforce scarcity per category.
        busy = await session.scalar(
            select(func.count(func.distinct(ListingPromotion.listing_id))).where(
                ListingPromotion.vertical_id == vertical_id,
                ListingPromotion.ends_at > now,
            )
        )
        if int(busy or 0) >= cfg.slots_per_category:
            raise HTTPException(status_code=409, detail="All sponsored slots in this category are taken")
    starts_at = current_end or now
    ends_at = starts_at + timedelta(days=days)
    if ends_at - now > timedelta(days=cfg.max_days):
        raise HTTPException(
            status_code=422,
            detail=f"Sponsored placement can be booked at most {cfg.max_days} days ahead",
        )

    amount = (cfg.daily_fee * days).quantize(Decimal("0.00000001"))
    ledger_event_id = None
    if amount > 0:
        acc_agent = await get_or_create_account(session, "agent", strategy.owner_agent_id)
        # Shared with withdrawals and listing fees, so concurrent debits of the
        # same account cannot both pass the balance check.
        await lock_account_for_spend(session, acc_agent.id)
        acc_platform = await get_or_create_account(session, "system", PLATFORM_ACCOUNT_OWNER_ID)
        bal = await balance_for_account(session, acc_agent.id, cfg.currency)
        if (bal.get(cfg.currency) or Decimal(0)) < amount:
            raise HTTPException(status_code=402, detail="Insufficient balance for sponsored placement")
        ev = await append_event(
            session,
            LedgerEventTypeEnum.fee,
            cfg.currency,
            amount,
            src_account_id=acc_agent.id,
            dst_account_id=acc_platform.id,
            metadata={
                "type": "listing_promotion",
                "listing_id": str(listing.id),
                "days": days,
                "daily_fee": str(cfg.daily_fee),
                "starts_at": starts_at.isoformat(),
                "ends_at": ends_at.isoformat(),
            },
        )
        ledger_event_id = str(ev.id)

    row = ListingPromotion(
        listing_id=str(listing.id),
        vertical_id=vertical_id,
        owner_agent_id=str(strategy.owner_agent_id) if strategy.owner_agent_id else None,
        purchased_by_user_id=purchased_by_user_id,
        days=days,
        starts_at=starts_at,
        ends_at=ends_at,
        amount_value=amount,
        amount_currency=cfg.currency,
        ledger_event_id=ledger_event_id,
        created_at=now,
    )
    session.add(row)
    await session.flush()
    return row


def sponsored_now_subquery():
    """Correlated scalar: 1 when a paid placement covers this listing right now."""
    return (
        select(func.count(ListingPromotion.id))
        .where(
            ListingPromotion.listing_id == Listing.id,
            ListingPromotion.starts_at <= func.now(),
            ListingPromotion.ends_at > func.now(),
        )
        .correlate(Listing)
        .scalar_subquery()
    )


def sponsored_until_subquery():
    """Correlated scalar: end of the booked (possibly extended) sponsored window."""
    return (
        select(func.max(ListingPromotion.ends_at))
        .where(ListingPromotion.listing_id == Listing.id, ListingPromotion.ends_at > func.now())
        .correlate(Listing)
        .scalar_subquery()
    )
