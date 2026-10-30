"""Mobile exchange office API — ACP-hub multi-asset foundation for iPhone wallet."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_auth, require_platform_admin
from app.config import get_settings
from app.db.models import AcpExchangeTicket, AcpOtcIntakeOrder
from app.schemas.exchange_office import (
    ExchangeCatalogPublic,
    ExchangeQuotePublic,
    ExchangeQuoteRequest,
    ExchangeTicketAdminCompleteRequest,
    ExchangeTicketAuthSettleRequest,
    ExchangeTicketCreateRequest,
    ExchangeTicketPublic,
)
from app.services import exchange_office as xo_svc
from app.services import exchange_ticket_settle as settle_svc
from app.services import otc_intake as otc_svc

router = APIRouter(tags=["Mobile Exchange Office"])


def _enabled() -> None:
    settings = get_settings()
    if not bool(getattr(settings, "exchange_office_enabled", True)):
        raise HTTPException(status_code=503, detail="Exchange office temporarily disabled")


def _parse_dec(raw) -> Decimal:
    try:
        return Decimal(str(raw))
    except (InvalidOperation, TypeError):
        return Decimal("0")


def _iso(dt: datetime | None) -> str:
    if dt is None:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    return dt.isoformat().replace("+00:00", "Z")


def _ticket_public(row: AcpExchangeTicket) -> ExchangeTicketPublic:
    return ExchangeTicketPublic(
        id=str(row.id),
        user_id=str(row.user_id) if row.user_id else None,
        status=row.status,  # type: ignore[arg-type]
        from_asset=row.from_asset,
        to_asset=row.to_asset,
        from_amount=str(row.from_amount).rstrip("0").rstrip(".") if row.from_amount is not None else "0",
        to_amount_estimated=str(row.to_amount_estimated).rstrip("0").rstrip(".")
        if row.to_amount_estimated is not None
        else "0",
        acp_hub_amount=str(row.acp_hub_amount).rstrip("0").rstrip(".") if row.acp_hub_amount is not None else "0",
        rail=row.rail,  # type: ignore[arg-type]
        rail_ref_type=row.rail_ref_type,
        rail_ref_id=str(row.rail_ref_id) if row.rail_ref_id else None,
        quote_id=row.quote_id,
        quote_snapshot=dict(row.quote_snapshot or {}),
        payout_acp_address=row.payout_acp_address,
        counterparty_address=row.counterparty_address,
        intake_reference=row.intake_reference,
        handoff_instructions=row.handoff_instructions,
        next_step=row.next_step or "",
        note=row.note,
        expires_at=_iso(row.expires_at) if row.expires_at else None,
        created_at=_iso(row.created_at),
        updated_at=_iso(row.updated_at),
    )


@router.get("/mobile/exchange/catalog", response_model=ExchangeCatalogPublic)
def exchange_catalog():
    _enabled()
    return xo_svc.catalog()


@router.post("/mobile/exchange/quote", response_model=ExchangeQuotePublic)
def exchange_quote(body: ExchangeQuoteRequest):
    _enabled()
    return xo_svc.quote(body)


@router.get("/mobile/exchange/quotes/{quote_id}", response_model=ExchangeQuotePublic)
def exchange_get_quote(quote_id: str):
    _enabled()
    cached = xo_svc.get_cached_quote(quote_id)
    if not cached:
        raise HTTPException(status_code=404, detail="Quote not found or expired")
    return ExchangeQuotePublic(**cached["payload"])


async def _open_otc_rail(
    *,
    session: AsyncSession,
    user_id: str,
    quote: dict,
    payout: str,
    note: str | None,
    goods_title: str | None,
    goods_description: str | None,
) -> tuple[str, str, str]:
    """Create underlying OTC order; returns (ref_type, ref_id, intake_reference)."""
    from_asset = quote["from_asset"]
    assets = {a.id: a for a in xo_svc.build_assets()}
    asset = assets.get(from_asset)
    if not asset:
        raise HTTPException(status_code=400, detail="Unknown from_asset for OTC rail")

    now = datetime.now(timezone.utc)
    if asset.rail == "otc_metal":
        metal = str(asset.metadata.get("metal") or "")
        purity = 999
        detail = otc_svc.build_metal_detail(
            metal=metal,  # type: ignore[arg-type]
            weight_grams=str(quote["from_amount"]),
            purity_ppt=purity,
        )
        q = otc_svc.quote_metal(metal=metal, weight_grams=str(quote["from_amount"]), purity_ppt=purity)  # type: ignore[arg-type]
        rail = "metal"
    elif asset.rail == "otc_commodity":
        commodity = str(asset.metadata.get("commodity") or "")
        detail = otc_svc.build_commodity_detail(
            commodity=commodity,  # type: ignore[arg-type]
            quantity=str(quote["from_amount"]),
        )
        q = otc_svc.quote_commodity(commodity=commodity, quantity=str(quote["from_amount"]))  # type: ignore[arg-type]
        rail = "commodity"
    elif asset.rail == "otc_real_estate":
        deal = str(asset.metadata.get("deal_type") or "sale")
        parcel = (goods_title or "").strip() or f"{asset.label} parcel"
        detail = otc_svc.build_real_estate_detail(
            deal_type=deal,  # type: ignore[arg-type]
            address_or_parcel=parcel,
            estimated_value_acp=str(quote["acp_hub_amount"]),
            document_hash=None,
        )
        q = otc_svc.quote_real_estate(deal_type=deal, estimated_value_acp=str(quote["acp_hub_amount"]))  # type: ignore[arg-type]
        rail = "real_estate"
    elif asset.rail == "otc_space":
        cls = str(asset.metadata.get("object_class") or "satellite")
        oid = (goods_title or "").strip() or None
        detail = otc_svc.build_space_detail(
            object_class=cls,  # type: ignore[arg-type]
            estimated_value_acp=str(quote["acp_hub_amount"]),
            space_object_id=oid,
        )
        q = otc_svc.quote_space(object_class=cls, estimated_value_acp=str(quote["acp_hub_amount"]), norad_or_cospar_id=oid)  # type: ignore[arg-type]
        rail = "space"
    elif asset.rail == "otc_ip":
        kind = str(asset.metadata.get("ip_kind") or "patent")
        title = (goods_title or "").strip() or f"{asset.label} package"
        detail = otc_svc.build_ip_detail(
            kind=kind,  # type: ignore[arg-type]
            title=title,
            estimated_value_acp=str(quote["acp_hub_amount"]),
            registration_uri=None,
            document_hash=None,
        )
        q = otc_svc.quote_ip(kind=kind, estimated_value_acp=str(quote["acp_hub_amount"]))  # type: ignore[arg-type]
        rail = "ip"
    else:
        category = str(asset.metadata.get("category") or "other")
        title = (goods_title or "").strip() or f"{asset.label} intake"
        detail = otc_svc.build_goods_detail(
            category=category,  # type: ignore[arg-type]
            title=title,
            description=goods_description,
            estimated_value_acp=str(quote["acp_hub_amount"]),
        )
        q = otc_svc.quote_goods(category=category, estimated_value_acp=str(quote["acp_hub_amount"]))  # type: ignore[arg-type]
        rail = "goods"

    order = AcpOtcIntakeOrder(
        id=uuid4(),
        user_id=user_id,
        rail=rail,
        status="awaiting_handoff",
        asset_label=otc_svc.asset_label_for(rail=rail, detail=detail),
        asset_detail=detail,
        estimated_acp_amount=_parse_dec(q.estimated_acp_amount),
        payout_acp_address=payout,
        intake_reference=f"OTC-{uuid4().hex[:8].upper()}",
        note=note,
        created_at=now,
        updated_at=now,
    )
    session.add(order)
    await session.flush()
    return "otc_intake", str(order.id), str(order.intake_reference)


@router.post("/mobile/exchange/tickets", response_model=ExchangeTicketPublic, status_code=201)
async def create_exchange_ticket(
    body: ExchangeTicketCreateRequest,
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    _enabled()
    idempotency_key = (x_idempotency_key or "").strip() or None
    if idempotency_key:
        existing = (
            await session.execute(
                select(AcpExchangeTicket).where(
                    AcpExchangeTicket.user_id == user_id,
                    AcpExchangeTicket.idempotency_key == idempotency_key,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return _ticket_public(existing)

    cached = xo_svc.get_cached_quote(body.quote_id)
    if not cached:
        raise HTTPException(status_code=400, detail="Quote not found or expired — request a fresh quote")
    quote = cached["payload"]
    if get_settings().external_token_racp_only and (
        quote["to_asset"] in {"wacp_bsc", "sacp_bsc", "usdt_bsc"}
        or quote["from_asset"] == "usdt_bsc"
    ):
        raise HTTPException(status_code=409, detail="New BSC exchange tickets are closed; request a fresh quote using supported assets.")

    needs_payout = quote["to_asset"] == "acp" or quote["rail"] in (
        "swap_desk",
        "otc_metal",
        "otc_goods",
        "otc_commodity",
        "otc_real_estate",
        "otc_space",
        "otc_ip",
        "hub_cross",
    )
    payout = body.payout_acp_address
    if needs_payout and not payout:
        raise HTTPException(status_code=400, detail="payout_acp_address required for this quote")

    now = datetime.now(timezone.utc)
    rail = quote["rail"]
    rail_ref_type = None
    rail_ref_id = None
    intake_reference = xo_svc.make_intake_reference()
    handoff = None
    status = "opened"
    next_step = quote.get("next_step") or ""

    if rail in ("otc_metal", "otc_goods", "otc_commodity", "otc_real_estate", "otc_space", "otc_ip") and payout:
        rail_ref_type, rail_ref_id, intake_reference = await _open_otc_rail(
            session=session,
            user_id=user_id,
            quote=quote,
            payout=payout,
            note=body.note.strip() if body.note else None,
            goods_title=body.goods_title,
            goods_description=body.goods_description,
        )
        status = "awaiting_user"
        handoff = otc_svc.handoff_instructions()
        next_step = (
            f"Hand off physical asset with reference {intake_reference}, then confirm on the OTC desk."
        )
    elif rail == "swap_desk":
        status = "awaiting_user"
        next_step = (
            "Use /wallet/acp/swap (web desk) or create a USDT TRC-20 swap order with this ticket id in the note. "
            f"Ticket reference {intake_reference}."
        )
    elif rail == "bridge":
        status = "awaiting_user"
        next_step = (
            "Open a bridge intent (ACP↔wACP) from the Bridge tab. "
            f"Keep ticket reference {intake_reference}."
        )
    elif rail == "hub_cross":
        status = "awaiting_user"
        next_step = quote.get("next_step") or (
            f"Execute legs in order. Ticket {intake_reference}."
        )
    elif rail == "fiat_onramp":
        status = "opened"
        next_step = "Fiat on-ramp is planned — ticket recorded for waitlist / partner rail."
    elif rail == "dex_deep_link":
        status = "awaiting_user"
        next_step = "Open PancakeSwap / smart-pay route for wACP↔USDT, then bridge as needed."

    expires_at = None
    if quote.get("expires_at"):
        try:
            expires_at = datetime.fromisoformat(str(quote["expires_at"]).replace("Z", "+00:00"))
        except ValueError:
            expires_at = None

    ticket = AcpExchangeTicket(
        id=uuid4(),
        user_id=user_id,
        status=status,
        from_asset=quote["from_asset"],
        to_asset=quote["to_asset"],
        from_amount=_parse_dec(quote["from_amount"]),
        to_amount_estimated=_parse_dec(quote["to_amount"]),
        acp_hub_amount=_parse_dec(quote["acp_hub_amount"]),
        rail=rail,
        rail_ref_type=rail_ref_type,
        rail_ref_id=rail_ref_id,
        quote_id=quote["quote_id"],
        quote_snapshot=quote,
        payout_acp_address=payout,
        counterparty_address=body.counterparty_address,
        intake_reference=intake_reference,
        handoff_instructions=handoff,
        next_step=next_step,
        note=body.note.strip() if body.note else None,
        idempotency_key=idempotency_key,
        expires_at=expires_at,
        created_at=now,
        updated_at=now,
    )
    session.add(ticket)
    await session.flush()
    return _ticket_public(ticket)


@router.get("/mobile/exchange/tickets", response_model=list[ExchangeTicketPublic])
async def list_exchange_tickets(
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    _enabled()
    rows = (
        await session.execute(
            select(AcpExchangeTicket)
            .where(AcpExchangeTicket.user_id == user_id)
            .order_by(AcpExchangeTicket.created_at.desc())
            .limit(50)
        )
    ).scalars().all()
    return [_ticket_public(r) for r in rows]


@router.get("/mobile/exchange/tickets/{ticket_id}", response_model=ExchangeTicketPublic)
async def get_exchange_ticket(
    ticket_id: str,
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    _enabled()
    row = await session.get(AcpExchangeTicket, ticket_id)
    if row is None or str(row.user_id) != str(user_id):
        raise HTTPException(status_code=404, detail="Ticket not found")
    return _ticket_public(row)


@router.post("/mobile/exchange/tickets/{ticket_id}/cancel", response_model=ExchangeTicketPublic)
async def cancel_exchange_ticket(
    ticket_id: str,
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    _enabled()
    row = await session.get(AcpExchangeTicket, ticket_id)
    if row is None or str(row.user_id) != str(user_id):
        raise HTTPException(status_code=404, detail="Ticket not found")
    if row.status in ("completed", "cancelled", "rejected"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel ticket in status {row.status}")
    row.status = "cancelled"
    row.updated_at = datetime.now(timezone.utc)
    await session.flush()
    return _ticket_public(row)


@router.post("/mobile/exchange/tickets/{ticket_id}/auth-settle", response_model=ExchangeTicketPublic)
async def auth_settle_exchange_ticket(
    ticket_id: str,
    body: ExchangeTicketAuthSettleRequest = ExchangeTicketAuthSettleRequest(),
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    """Open/link the settlement rail (swap desk order, bridge handoff, OTC review)."""
    _enabled()
    row = await session.get(AcpExchangeTicket, ticket_id)
    if row is None or str(row.user_id) != str(user_id):
        raise HTTPException(status_code=404, detail="Ticket not found")
    updated = await settle_svc.auth_settle_ticket(
        session,
        row,
        user_id=user_id,
        tron_txid=body.tron_txid,
    )
    return _ticket_public(updated)


@router.post("/mobile/exchange/tickets/{ticket_id}/sync", response_model=ExchangeTicketPublic)
async def sync_exchange_ticket(
    ticket_id: str,
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    """Refresh ticket status from the linked swap/OTC rail."""
    _enabled()
    row = await session.get(AcpExchangeTicket, ticket_id)
    if row is None or str(row.user_id) != str(user_id):
        raise HTTPException(status_code=404, detail="Ticket not found")
    updated = await settle_svc.sync_ticket_from_rail(session, row, user_id=user_id)
    return _ticket_public(updated)


@router.post("/mobile/exchange/tickets/{ticket_id}/complete", response_model=ExchangeTicketPublic)
async def admin_complete_exchange_ticket(
    ticket_id: str,
    body: ExchangeTicketAdminCompleteRequest = ExchangeTicketAdminCompleteRequest(),
    _admin: str = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
):
    """Platform admin marks a supervised ticket settled (desk/OTC/manual rails)."""
    _enabled()
    row = await session.get(AcpExchangeTicket, ticket_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    updated = await settle_svc.admin_complete_ticket(session, row, note=body.note)
    return _ticket_public(updated)
