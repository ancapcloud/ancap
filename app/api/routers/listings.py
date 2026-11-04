from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Header, Query, HTTPException

from app.schemas import (
    ListingCreateRequest,
    ListingPublic,
    Pagination,
    ListingStatus,
    MarketplaceSort,
    MarketplaceListingPublic,
    MarketplaceListingsResponse,
    Money,
)
from app.schemas.listings import (
    ListingPromotionCreateRequest,
    ListingPromotionPricingPublic,
    ListingPromotionPublic,
    ListingPromotionsResponse,
)
from app.services import listing_promotions
from app.services.idempotency import get_idempotency_hit, store_idempotency_result
from app.api.deps import Caller, DbSession, require_agent_control
from app.config import get_settings
from app.db.models import (
    Listing,
    ListingPromotion,
    ListingStatusEnum,
    Strategy,
    StrategyVersion,
    Order,
    OrderStatusEnum,
    Review,
    Vertical,
    PublicActivityFeedEvent,
)
from app.services.ledger import append_event, balance_for_account, get_or_create_account, lock_account_for_spend
from app.db.models import LedgerEventTypeEnum
from app.constants import PLATFORM_ACCOUNT_OWNER_ID
from app.services.stakes import require_activated_if_stake_required
from app.services.participation_gates import evaluate_agent_gate
from app.services.decision_logs import log_reject_decision
from sqlalchemy import select, func, or_, cast, String, Numeric, desc

router = APIRouter(prefix="/listings", tags=["Listings"])


def _listing_price_from_fee_model(fee_model: dict) -> tuple[Decimal, str]:
    one_time = (fee_model or {}).get("one_time_price") or {}
    if one_time:
        return Decimal(str(one_time.get("amount") or "0")), str(one_time.get("currency") or "ACP")
    monthly = (fee_model or {}).get("subscription_price_monthly") or {}
    if monthly:
        return Decimal(str(monthly.get("amount") or "0")), str(monthly.get("currency") or "ACP")
    legacy_subscription = (fee_model or {}).get("subscription_price") or {}
    if legacy_subscription:
        return Decimal(str(legacy_subscription.get("amount") or "0")), str(legacy_subscription.get("currency") or "ACP")
    quarterly = (fee_model or {}).get("subscription_price_quarterly") or {}
    if quarterly:
        return Decimal(str(quarterly.get("amount") or "0")), str(quarterly.get("currency") or "ACP")
    annual = (fee_model or {}).get("subscription_price_annual") or {}
    if annual:
        return Decimal(str(annual.get("amount") or "0")), str(annual.get("currency") or "ACP")
    return Decimal(0), "ACP"


def _serialize_listing(listing: Listing) -> ListingPublic:
    return ListingPublic(
        id=str(listing.id),
        strategy_id=str(listing.strategy_id),
        strategy_version_id=str(listing.strategy_version_id) if listing.strategy_version_id else None,
        fee_model=listing.fee_model,
        status=ListingStatus(listing.status.value),
        terms_url=listing.terms_url,
        notes=listing.notes,
        created_at=listing.created_at,
    )


def _bool_flag_from_notes(notes: str | None, flag: str) -> bool:
    if not notes:
        return False
    lower = notes.lower()
    return f"#{flag}" in lower or f"[{flag}]" in lower


def _float_or_zero(value) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


@router.post("", response_model=ListingPublic, status_code=201)
async def create_listing(body: ListingCreateRequest, session: DbSession, caller: Caller):
    strategy_id = UUID(body.strategy_id)
    strat = await session.get(Strategy, strategy_id)
    if not strat:
        raise HTTPException(status_code=404, detail="Strategy not found")
    version_id = UUID(body.strategy_version_id)
    ver = await session.get(StrategyVersion, version_id)
    if not ver:
        raise HTTPException(status_code=404, detail="Strategy version not found")
    if str(ver.strategy_id) != str(strategy_id):
        raise HTTPException(status_code=400, detail="Strategy version does not belong to strategy")
    # The listing fee is debited from the owner agent's balance, so only that
    # agent (or the user who owns it) may list the strategy.
    await require_agent_control(session, caller, strat.owner_agent_id)
    await require_activated_if_stake_required(session, strat.owner_agent_id)
    gate = await evaluate_agent_gate(session, strat.owner_agent_id)
    if not gate.ok:
        await log_reject_decision(
            session,
            reason_code=gate.reason_code or "agent_gate_rejected",
            message=gate.detail,
            scope="listings.create",
            actor_type="agent",
            actor_id=strat.owner_agent_id,
            subject_type="agent",
            subject_id=strat.owner_agent_id,
            metadata=gate.metrics,
        )
        raise HTTPException(
            status_code=403,
            detail={
                "reason_code": gate.reason_code,
                "message": gate.detail,
                "metrics": gate.metrics,
            },
        )
    # L3: platform listing fee (% of listing price; fallback to static fee if configured)
    settings = get_settings()
    listing_price, listing_currency = _listing_price_from_fee_model(body.fee_model.model_dump())
    listing_fee_percent = Decimal(str(getattr(settings, "listing_fee_percent", "0") or "0"))
    fee_value = Decimal(0)
    fee_currency = listing_currency
    if listing_fee_percent > 0 and listing_price > 0:
        fee_value = (listing_price * listing_fee_percent / Decimal(100)).quantize(Decimal("0.00000001"))
    elif settings.listing_fee_amount and Decimal(settings.listing_fee_amount) > 0:
        fee_value = Decimal(settings.listing_fee_amount)
        fee_currency = settings.listing_fee_currency

    if fee_value > 0:
        acc_agent = await get_or_create_account(session, "agent", strat.owner_agent_id)
        await lock_account_for_spend(session, acc_agent.id)
        acc_platform = await get_or_create_account(session, "system", PLATFORM_ACCOUNT_OWNER_ID)
        bal = await balance_for_account(session, acc_agent.id, fee_currency)
        if (bal.get(fee_currency) or Decimal(0)) < fee_value:
            raise HTTPException(status_code=402, detail="Insufficient balance for listing fee")
        await append_event(
            session,
            LedgerEventTypeEnum.fee,
            fee_currency,
            fee_value,
            src_account_id=acc_agent.id,
            dst_account_id=acc_platform.id,
            metadata={
                "type": "listing_fee",
                "strategy_id": str(strategy_id),
                "basis": "listing_price_percent" if listing_fee_percent > 0 and listing_price > 0 else "static",
                "listing_price": str(listing_price),
                "listing_fee_percent": str(listing_fee_percent),
            },
        )
    listing = Listing(
        strategy_id=strategy_id,
        strategy_version_id=version_id,
        fee_model=body.fee_model.model_dump(),
        status=ListingStatusEnum(body.status.value),
        terms_url=body.terms_url,
        notes=body.notes,
    )
    session.add(listing)
    await session.flush()
    await session.refresh(listing)
    return _serialize_listing(listing)


@router.get("", response_model=Pagination[ListingPublic])
async def list_listings(
    session: DbSession,
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    status: ListingStatus | None = Query(None),
    strategy_id: UUID | None = Query(None),
):
    q = select(Listing).order_by(Listing.created_at.desc()).limit(limit + 1)
    if cursor:
        try:
            q = q.where(Listing.id < UUID(cursor))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid pagination cursor") from None
    if status:
        q = q.where(Listing.status == status.value)
    if strategy_id:
        q = q.where(Listing.strategy_id == strategy_id)
    r = await session.execute(q)
    rows = r.scalars().all()
    next_cursor = str(rows[-1].id) if len(rows) > limit else None
    items = rows[:limit]
    return Pagination(
        items=[_serialize_listing(l) for l in items],
        next_cursor=next_cursor,
    )


@router.get("/marketplace/listings", response_model=MarketplaceListingsResponse)
async def list_marketplace_listings(
    session: DbSession,
    search: str | None = Query(None, min_length=1, max_length=200),
    category: str | None = Query(None, min_length=1, max_length=80),
    price_min: Decimal | None = Query(None, ge=0),
    price_max: Decimal | None = Query(None, ge=0),
    sort: MarketplaceSort = Query(MarketplaceSort.popular),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    price_type = Numeric(36, 18)
    listing_price_amount = cast(
        func.coalesce(
            Listing.fee_model["one_time_price"]["amount"].astext,
            Listing.fee_model["subscription_price_monthly"]["amount"].astext,
            Listing.fee_model["subscription_price"]["amount"].astext,
            Listing.fee_model["subscription_price_quarterly"]["amount"].astext,
            Listing.fee_model["subscription_price_annual"]["amount"].astext,
            "0",
        ),
        price_type,
    )
    listing_price_currency = func.upper(
        func.coalesce(
            Listing.fee_model["one_time_price"]["currency"].astext,
            Listing.fee_model["subscription_price_monthly"]["currency"].astext,
            Listing.fee_model["subscription_price"]["currency"].astext,
            Listing.fee_model["subscription_price_quarterly"]["currency"].astext,
            Listing.fee_model["subscription_price_annual"]["currency"].astext,
            "ACP",
        )
    )
    search_text = (search or "").strip()
    use_fts = bool(search_text)
    ts_query = func.plainto_tsquery("english", search_text) if use_fts else None
    strategy_search_vector = func.to_tsvector(
        "english",
        func.concat_ws(" ", Strategy.name, Strategy.summary, Strategy.description, Vertical.name),
    )
    search_rank = func.ts_rank(strategy_search_vector, ts_query).label("search_rank") if use_fts else func.cast(0, price_type).label("search_rank")
    order_count_sq = (
        select(func.count(Order.id))
        .where(Order.listing_id == Listing.id, Order.status == OrderStatusEnum.paid)
        .correlate(Listing)
        .scalar_subquery()
    )
    review_avg_sq = (
        select(func.coalesce(func.avg(Review.weight), 0.0))
        .where(Review.target_type == "listing", Review.target_id == Listing.id)
        .correlate(Listing)
        .scalar_subquery()
    )
    review_count_sq = (
        select(func.count(Review.id))
        .where(Review.target_type == "listing", Review.target_id == Listing.id)
        .correlate(Listing)
        .scalar_subquery()
    )
    listing_views_sq = (
        select(func.count(PublicActivityFeedEvent.id))
        .where(
            PublicActivityFeedEvent.ref_type == "listing",
            PublicActivityFeedEvent.ref_id == Listing.id,
            PublicActivityFeedEvent.event_type.in_(["listing_viewed", "listing_opened"]),
        )
        .correlate(Listing)
        .scalar_subquery()
    )

    sponsored_now_sq = listing_promotions.sponsored_now_subquery()
    sponsored_until_sq = listing_promotions.sponsored_until_subquery()
    sponsored_rank = func.coalesce(sponsored_now_sq, 0) > 0

    base_query = (
        select(
            Listing,
            Strategy,
            Vertical,
            sponsored_rank.label("is_sponsored"),
            sponsored_until_sq.label("sponsored_until"),
            listing_price_amount.label("listing_price_amount"),
            listing_price_currency.label("listing_price_currency"),
            order_count_sq.label("listing_purchases"),
            review_avg_sq.label("rating"),
            review_count_sq.label("rating_count"),
            listing_views_sq.label("listing_views"),
            search_rank,
        )
        .join(Strategy, Listing.strategy_id == Strategy.id)
        .join(Vertical, Strategy.vertical_id == Vertical.id)
        .where(Listing.status == ListingStatusEnum.active)
    )

    if use_fts:
        fallback_q = f"%{search_text}%"
        base_query = base_query.where(
            or_(
                strategy_search_vector.op("@@")(ts_query),
                Strategy.name.ilike(fallback_q),
                Strategy.description.ilike(fallback_q),
                Strategy.summary.ilike(fallback_q),
                Vertical.name.ilike(fallback_q),
                Listing.notes.ilike(fallback_q),
                cast(Listing.id, String).ilike(fallback_q),
                cast(Strategy.id, String).ilike(fallback_q),
            )
        )
    if category:
        base_query = base_query.where(func.lower(Vertical.name) == category.strip().lower())
    if price_min is not None:
        base_query = base_query.where(listing_price_amount >= price_min)
    if price_max is not None:
        base_query = base_query.where(listing_price_amount <= price_max)

    sort_exprs = {
        MarketplaceSort.popular: [desc(order_count_sq), desc(listing_views_sq), Listing.created_at.desc()],
        MarketplaceSort.recent: [Listing.created_at.desc()],
        MarketplaceSort.price_asc: [listing_price_amount.asc(), Listing.created_at.desc()],
        MarketplaceSort.price_desc: [listing_price_amount.desc(), Listing.created_at.desc()],
        MarketplaceSort.rating: [desc(review_avg_sq), desc(review_count_sq), Listing.created_at.desc()],
    }
    # Paid placements lead the default "popular" view only; explicit sorts
    # (price, rating, recency) and searches keep their organic order so
    # buyers who ask for cheapest or best-rated get exactly that.
    lead = [desc(sponsored_rank)] if sort == MarketplaceSort.popular and not use_fts else []
    if use_fts:
        query = base_query.order_by(desc(search_rank), *sort_exprs[sort]).limit(limit).offset(offset)
    else:
        query = base_query.order_by(*lead, *sort_exprs[sort]).limit(limit).offset(offset)
    rows = (await session.execute(query)).all()

    total_query = select(func.count()).select_from(base_query.order_by(None).subquery())
    total = int((await session.execute(total_query)).scalar() or 0)
    categories_query = (
        select(Vertical.name)
        .join(Strategy, Strategy.vertical_id == Vertical.id)
        .join(Listing, Listing.strategy_id == Strategy.id)
        .where(Listing.status == ListingStatusEnum.active)
        .distinct()
        .order_by(Vertical.name.asc())
    )
    available_categories = [name for name in (await session.execute(categories_query)).scalars().all() if name]

    items: list[MarketplaceListingPublic] = []
    for (
        listing,
        strategy,
        vertical,
        is_sponsored,
        sponsored_until,
        price_amount,
        price_currency,
        listing_purchases,
        rating,
        rating_count,
        listing_views,
        _search_rank,
    ) in rows:
        purchase_count = int(listing_purchases or 0)
        view_count = int(listing_views or 0)
        avg_rating = _float_or_zero(rating)
        featured_by_tag = _bool_flag_from_notes(listing.notes, "featured")
        trending_by_tag = _bool_flag_from_notes(listing.notes, "trending")
        is_featured = featured_by_tag or purchase_count >= 3 or (view_count >= 5 and avg_rating >= 0.85)
        is_trending = trending_by_tag or (purchase_count >= 1 and view_count >= 2) or avg_rating >= 0.9
        items.append(
            MarketplaceListingPublic(
                id=str(listing.id),
                strategy_id=str(listing.strategy_id),
                strategy_version_id=str(listing.strategy_version_id) if listing.strategy_version_id else None,
                strategy_name=strategy.name,
                strategy_description=strategy.description,
                category=vertical.name if vertical else None,
                fee_model=listing.fee_model,
                price=Money(amount=str(price_amount), currency=str(price_currency or "ACP")),
                status=ListingStatus(listing.status.value),
                terms_url=listing.terms_url,
                notes=listing.notes,
                listing_views=view_count,
                listing_purchases=purchase_count,
                rating=avg_rating,
                rating_count=int(rating_count or 0),
                is_featured=is_featured,
                is_trending=is_trending,
                is_sponsored=bool(is_sponsored),
                sponsored_until=sponsored_until if is_sponsored else None,
                created_at=listing.created_at,
            )
        )

    return MarketplaceListingsResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        available_categories=available_categories,
    )


def _promotion_public(row: ListingPromotion) -> ListingPromotionPublic:
    return ListingPromotionPublic(
        id=str(row.id),
        listing_id=str(row.listing_id),
        days=int(row.days),
        starts_at=row.starts_at,
        ends_at=row.ends_at,
        amount=Money(amount=format(Decimal(row.amount_value).normalize(), "f"), currency=row.amount_currency),
        ledger_event_id=str(row.ledger_event_id) if row.ledger_event_id else None,
        created_at=row.created_at,
    )


@router.get("/promotions/pricing", response_model=ListingPromotionPricingPublic)
async def listing_promotion_pricing():
    """Public price list for sponsored marketplace placement."""
    cfg = listing_promotions.pricing()
    return ListingPromotionPricingPublic(
        enabled=cfg.enabled,
        daily_fee=Money(amount=format(cfg.daily_fee.normalize(), "f"), currency=cfg.currency),
        max_days=cfg.max_days,
        slots_per_category=cfg.slots_per_category,
    )


@router.post("/{listing_id}/promotions", response_model=ListingPromotionPublic, status_code=201)
async def promote_listing(
    listing_id: UUID,
    body: ListingPromotionCreateRequest,
    session: DbSession,
    caller: Caller,
    # Matches IdempotencyKey.key (String(128)); longer keys would fail on insert.
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=128),
):
    """Buy (or extend) sponsored placement; the fee is paid from the owner agent's balance."""
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    strategy = await session.get(Strategy, listing.strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    await require_agent_control(session, caller, strategy.owner_agent_id)

    scope = f"listing_promotion:{listing_id}"
    payload = body.model_dump(mode="json")
    # Lock before the idempotency lookup so an overlapping retry with the same
    # key waits for the first purchase and then replays its stored response.
    await listing_promotions.lock_listing_purchase(session, str(listing_id))
    if idempotency_key:
        hit = await get_idempotency_hit(session, scope=scope, key=idempotency_key, request_payload=payload)
        if hit is not None:
            return ListingPromotionPublic.model_validate(hit.response_json)

    row = await listing_promotions.purchase(
        session,
        listing=listing,
        strategy=strategy,
        days=body.days,
        purchased_by_user_id=caller.user_id,
    )
    result = _promotion_public(row)
    if idempotency_key:
        await store_idempotency_result(
            session,
            scope=scope,
            key=idempotency_key,
            request_payload=payload,
            status_code=201,
            response_json=result.model_dump(mode="json"),
        )
    return result


@router.get("/{listing_id}/promotions", response_model=ListingPromotionsResponse)
async def list_listing_promotions(listing_id: UUID, session: DbSession, caller: Caller):
    """Sponsored placement history for a listing (owner only)."""
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    strategy = await session.get(Strategy, listing.strategy_id)
    await require_agent_control(session, caller, strategy.owner_agent_id if strategy else None)
    rows = (
        await session.scalars(
            select(ListingPromotion)
            .where(ListingPromotion.listing_id == str(listing_id))
            .order_by(ListingPromotion.starts_at.desc())
            .limit(100)
        )
    ).all()
    return ListingPromotionsResponse(
        items=[_promotion_public(x) for x in rows],
        active_until=await listing_promotions.active_until(session, str(listing_id)),
    )


@router.get("/{listing_id}", response_model=ListingPublic)
async def get_listing(listing_id: UUID, session: DbSession):
    q = select(Listing).where(Listing.id == listing_id)
    r = await session.execute(q)
    listing = r.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    session.add(
        PublicActivityFeedEvent(
            event_type="listing_opened",
            ref_type="listing",
            ref_id=listing.id,
            visibility="public",
            score=Decimal("0.05"),
            payload_json={
                "listing_id": str(listing.id),
                "strategy_id": str(listing.strategy_id),
            },
        )
    )
    return _serialize_listing(listing)
