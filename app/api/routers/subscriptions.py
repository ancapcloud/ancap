from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from app.api.deps import DbSession, require_auth
from app.db.models import (
    AccessGrant,
    AccessScopeEnum,
    Listing,
    ListingStatusEnum,
    Order,
    OrderStatusEnum,
    Strategy,
    Subscription,
    SubscriptionBillingPeriodEnum,
    SubscriptionStatusEnum,
)
from app.schemas import (
    Money,
    SubscriptionBillingPeriod,
    SubscriptionCreateRequest,
    SubscriptionListResponse,
    SubscriptionPublic,
    SubscriptionStatus,
)
from app.services.ledger import balance_for_account, get_or_create_account, append_event
from app.db.models import LedgerEventTypeEnum

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


_BILLING_PERIOD_DELTAS: dict[SubscriptionBillingPeriodEnum, timedelta] = {
    SubscriptionBillingPeriodEnum.monthly: timedelta(days=30),
    SubscriptionBillingPeriodEnum.quarterly: timedelta(days=90),
    SubscriptionBillingPeriodEnum.annual: timedelta(days=365),
}

_BILLING_PERIOD_LABELS: dict[SubscriptionBillingPeriodEnum, str] = {
    SubscriptionBillingPeriodEnum.monthly: "monthly",
    SubscriptionBillingPeriodEnum.quarterly: "quarterly",
    SubscriptionBillingPeriodEnum.annual: "annual",
}


def _quantize_amount(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000000000000000001"), rounding=ROUND_HALF_UP)


def _parse_subscription_price(listing: Listing, billing_period: SubscriptionBillingPeriodEnum) -> tuple[Decimal, str]:
    fee_model = listing.fee_model or {}
    if str(fee_model.get("type") or "") != "subscription":
        raise HTTPException(status_code=400, detail="Listing does not offer subscriptions")

    period_key = f"subscription_price_{_BILLING_PERIOD_LABELS[billing_period]}"
    price_block = fee_model.get(period_key) or {}
    if not price_block and billing_period == SubscriptionBillingPeriodEnum.monthly:
        price_block = fee_model.get("subscription_price") or fee_model.get("subscription_price_monthly") or {}
    elif not price_block:
        raise HTTPException(
            status_code=400,
            detail=f"Listing does not offer {billing_period.value} subscriptions",
        )

    try:
        amount = Decimal(str(price_block.get("amount") or "0"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Listing subscription price is invalid") from exc
    currency = str(price_block.get("currency") or "ACP").upper()
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Listing subscription price must be greater than zero")
    if currency != "ACP":
        raise HTTPException(status_code=400, detail="Subscriptions currently support ACP only")
    return _quantize_amount(amount), currency


async def _serialize_subscription(row: Subscription) -> SubscriptionPublic:
    return SubscriptionPublic(
        id=str(row.id),
        listing_id=str(row.listing_id),
        user_id=str(row.user_id),
        status=SubscriptionStatus(row.status.value),
        billing_period=SubscriptionBillingPeriod(row.billing_period.value),
        price=Money(amount=str(row.price_acp), currency="ACP"),
        next_billing_at=row.next_billing_at,
        auto_renew=bool(row.auto_renew),
        retry_count=int(row.retry_count or 0),
        last_order_id=str(row.last_order_id) if row.last_order_id else None,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.post("", response_model=SubscriptionPublic, status_code=201)
async def create_subscription(
    body: SubscriptionCreateRequest,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    try:
        listing_id = UUID(body.listing_id)
        parsed_user_id = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid listing or user id") from exc

    billing_period = SubscriptionBillingPeriodEnum(body.billing_period.value)
    listing = await session.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status != ListingStatusEnum.active:
        raise HTTPException(status_code=400, detail="Listing is not active")

    amount, currency = _parse_subscription_price(listing, billing_period)

    existing = (
        await session.execute(
            select(Subscription)
            .where(
                Subscription.user_id == parsed_user_id,
                Subscription.listing_id == listing_id,
                Subscription.billing_period == billing_period,
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if existing and existing.status in {
        SubscriptionStatusEnum.active,
        SubscriptionStatusEnum.paused,
        SubscriptionStatusEnum.past_due,
    }:
        raise HTTPException(status_code=409, detail="Subscription already exists for this listing and billing period")

    buyer_account = await get_or_create_account(session, "user", parsed_user_id)
    balance = await balance_for_account(session, buyer_account.id, currency)
    available = balance.get(currency) or Decimal(0)
    if available < amount:
        raise HTTPException(status_code=402, detail="Insufficient balance for subscription")

    seller_account = None
    strategy = await session.get(Strategy, listing.strategy_id) if listing.strategy_id else None
    if strategy is not None and strategy.owner_agent_id:
        seller_account = await get_or_create_account(session, "agent", strategy.owner_agent_id)

    if seller_account is not None:
        await append_event(
            session,
            LedgerEventTypeEnum.transfer,
            currency,
            amount,
            src_account_id=buyer_account.id,
            dst_account_id=seller_account.id,
            metadata={"subscription_billing": True, "listing_id": str(listing.id), "billing_period": billing_period.value},
        )

    order = Order(
        listing_id=listing.id,
        buyer_type="user",
        buyer_id=parsed_user_id,
        status=OrderStatusEnum.paid,
        amount_currency=currency,
        amount_value=amount,
        payment_method="subscription",
        note=f"subscription:{billing_period.value}",
    )
    session.add(order)
    await session.flush()

    next_billing_at = datetime.now(UTC) + _BILLING_PERIOD_DELTAS[billing_period]
    row = existing or Subscription(
        user_id=parsed_user_id,
        listing_id=listing.id,
        billing_period=billing_period,
        price_acp=amount,
        auto_renew=body.auto_renew,
        retry_count=0,
    )
    row.status = SubscriptionStatusEnum.active
    row.price_acp = amount
    row.auto_renew = body.auto_renew
    row.retry_count = 0
    row.next_billing_at = next_billing_at
    row.last_order_id = order.id
    session.add(row)

    grant = AccessGrant(
        strategy_id=listing.strategy_id,
        grantee_type="user",
        grantee_id=parsed_user_id,
        scope=AccessScopeEnum.execute,
        expires_at=next_billing_at,
    )
    session.add(grant)
    await session.flush()
    await session.refresh(row)
    return await _serialize_subscription(row)


@router.get("", response_model=SubscriptionListResponse)
async def list_subscriptions(
    session: DbSession,
    user_id: str = Depends(require_auth),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    status: SubscriptionStatus | None = Query(None),
):
    try:
        parsed_user_id = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user id") from exc

    q = (
        select(Subscription)
        .where(Subscription.user_id == parsed_user_id)
        .order_by(Subscription.created_at.desc())
        .limit(limit + 1)
    )
    if cursor:
        try:
            q = q.where(Subscription.id < UUID(cursor))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid pagination cursor") from None
    if status:
        q = q.where(Subscription.status == SubscriptionStatusEnum(status.value))

    rows = (await session.execute(q)).scalars().all()
    next_cursor = str(rows[-1].id) if len(rows) > limit else None
    items = rows[:limit]
    return SubscriptionListResponse(
        items=[await _serialize_subscription(item) for item in items],
        next_cursor=next_cursor,
    )
