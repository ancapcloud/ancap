from __future__ import annotations

import csv
import io
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import desc, func, select

from app.api.deps import DbSession, require_auth
from app.db.models import MerchantAccount, MerchantInvoice, PaymentLink
from app.schemas.merchant import (
    InvoiceCreateRequest,
    InvoiceLineItem,
    InvoicePublic,
    MerchantAccountPublic,
    MerchantDashboardPublic,
    PaymentLinkCheckoutRequest,
    PaymentLinkCheckoutResponse,
    PaymentLinkCreateRequest,
    PaymentLinkPublic,
)
from app.services.merchant_pay import (
    capture_payment_link_credits,
    generate_payment_code,
    get_or_create_merchant_account,
    merchant_volume_total,
    pay_url_for_code,
)
from app.api.routers.commerce import enforce_payment_link_plan_limit
from app.services.webhook_dispatcher import dispatch_event_to_owner_subscribers

router = APIRouter(tags=["ANCAP Pay"])
pay_router = APIRouter(prefix="/pay", tags=["ANCAP Pay"])
merchant_router = APIRouter(prefix="/merchant", tags=["Merchant"])


def _serialize_account(row: MerchantAccount) -> MerchantAccountPublic:
    return MerchantAccountPublic(
        id=str(row.id),
        display_name=row.display_name,
        plan_tier=row.plan_tier,
        fee_bps=row.fee_bps,
        created_at=row.created_at,
    )


def _serialize_link(row: PaymentLink) -> PaymentLinkPublic:
    proof_url = None
    if row.payment_intent_id:
        proof_url = f"https://ancap.cloud/proof-center?payment_intent={row.payment_intent_id}"
    return PaymentLinkPublic(
        id=str(row.id),
        code=row.code,
        title=row.title,
        description=row.description,
        amount=str(row.amount_value),
        currency=row.amount_currency,
        status=row.status,
        pay_url=pay_url_for_code(row.code),
        qr_url=f"{pay_url_for_code(row.code)}?qr=1",
        expires_at=row.expires_at,
        created_at=row.created_at,
        payment_intent_id=str(row.payment_intent_id) if row.payment_intent_id else None,
        proof_url=proof_url,
    )


def _parse_amount(raw: str) -> Decimal:
    try:
        value = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid amount") from exc
    if value <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    return value


@pay_router.post("/payment-links", response_model=PaymentLinkPublic, status_code=201)
async def create_payment_link(
    body: PaymentLinkCreateRequest,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    user_uuid = UUID(user_id)
    merchant = await get_or_create_merchant_account(session, user_uuid)
    await enforce_payment_link_plan_limit(session, merchant)
    amount = _parse_amount(body.amount)
    currency = body.currency.strip().upper()
    if currency not in {"ACP", "SACP", "USDT", "USD"}:
        raise HTTPException(
            status_code=400,
            detail="currency must be one of ACP, SACP, USDT, USD",
        )
    expires_at = None
    if body.expires_in_hours:
        expires_at = datetime.now(UTC) + timedelta(hours=body.expires_in_hours)

    code = generate_payment_code()
    while await session.scalar(select(PaymentLink.id).where(PaymentLink.code == code)):
        code = generate_payment_code()

    row = PaymentLink(
        merchant_account_id=merchant.id,
        owner_user_id=user_uuid,
        code=code,
        title=body.title.strip(),
        description=body.description,
        amount_currency=currency,
        amount_value=amount,
        status="pending",
        expires_at=expires_at,
    )
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return _serialize_link(row)


@pay_router.get("/payment-links/{link_id}", response_model=PaymentLinkPublic)
async def get_payment_link_by_id(
    link_id: str,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    try:
        parsed = UUID(link_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Payment link not found") from exc
    row = await session.get(PaymentLink, parsed)
    if row is None or str(row.owner_user_id) != user_id:
        raise HTTPException(status_code=404, detail="Payment link not found")
    return _serialize_link(row)


@pay_router.get("/{code}", response_model=PaymentLinkPublic)
async def get_public_payment_link(code: str, session: DbSession):
    row = await session.scalar(select(PaymentLink).where(PaymentLink.code == code))
    if row is None:
        raise HTTPException(status_code=404, detail="Payment link not found")
    if row.expires_at and row.expires_at < datetime.now(UTC) and row.status == "pending":
        row.status = "expired"
        await session.flush()
    return _serialize_link(row)


@pay_router.post("/{code}/checkout", response_model=PaymentLinkCheckoutResponse)
async def checkout_payment_link(
    code: str,
    body: PaymentLinkCheckoutRequest,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    row = await session.scalar(select(PaymentLink).where(PaymentLink.code == code))
    if row is None:
        raise HTTPException(status_code=404, detail="Payment link not found")
    if str(row.owner_user_id) == user_id:
        raise HTTPException(status_code=400, detail="Cannot pay your own payment link")

    method = (body.payment_method or "credits").strip().lower()
    if method not in {"credits", "ledger_credits"}:
        raise HTTPException(status_code=400, detail="Only credits checkout is supported in MVP")

    intent, ledger_event_id = await capture_payment_link_credits(
        session,
        link=row,
        payer_user_id=UUID(user_id),
        payment_reference=body.payment_reference,
    )
    await dispatch_event_to_owner_subscribers(
        session,
        owner_user_id=row.owner_user_id,
        event_type="merchant.payment.captured",
        payload={
            "payment_link_id": str(row.id),
            "payment_link_code": row.code,
            "payment_intent_id": str(intent.id),
            "amount": str(row.amount_value),
            "currency": row.amount_currency,
            "payer_user_id": user_id,
            "merchant_user_id": str(row.owner_user_id),
        },
    )
    await session.refresh(row)
    return PaymentLinkCheckoutResponse(
        payment_link=_serialize_link(row),
        payment_intent_id=str(intent.id),
        status=intent.status,
        ledger_event_id=ledger_event_id,
    )


@pay_router.post("/invoices", response_model=InvoicePublic, status_code=201)
async def create_invoice(
    body: InvoiceCreateRequest,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    user_uuid = UUID(user_id)
    merchant = await get_or_create_merchant_account(session, user_uuid)
    if not body.line_items:
        raise HTTPException(status_code=400, detail="At least one line item is required")

    total = Decimal(0)
    currency = body.line_items[0].currency.strip().upper()
    if currency not in {"ACP", "SACP", "USDT", "USD"}:
        raise HTTPException(
            status_code=400,
            detail="currency must be one of ACP, SACP, USDT, USD",
        )
    serialized_items: list[dict] = []
    for item in body.line_items:
        unit = _parse_amount(item.unit_amount)
        qty = Decimal(str(item.quantity))
        total += unit * qty
        serialized_items.append(item.model_dump(mode="json"))

    count = await session.scalar(
        select(func.count()).select_from(MerchantInvoice).where(MerchantInvoice.owner_user_id == user_uuid)
    )
    invoice_number = f"INV-{datetime.now(UTC).strftime('%Y%m%d')}-{int(count or 0) + 1:04d}"
    due_at = None
    if body.due_in_days:
        due_at = datetime.now(UTC) + timedelta(days=body.due_in_days)

    payment_link_row = None
    if body.create_payment_link:
        code = generate_payment_code()
        payment_link_row = PaymentLink(
            merchant_account_id=merchant.id,
            owner_user_id=user_uuid,
            code=code,
            title=f"Invoice {invoice_number}",
            description=body.notes,
            amount_currency=currency,
            amount_value=total,
            status="pending",
            expires_at=due_at,
        )
        session.add(payment_link_row)
        await session.flush()

    invoice = MerchantInvoice(
        merchant_account_id=merchant.id,
        owner_user_id=user_uuid,
        invoice_number=invoice_number,
        customer_email=body.customer_email,
        line_items_json=serialized_items,
        amount_currency=currency,
        amount_value=total,
        status="sent" if payment_link_row else "draft",
        due_at=due_at,
        payment_link_id=payment_link_row.id if payment_link_row else None,
        notes=body.notes,
    )
    session.add(invoice)
    await session.flush()
    await session.refresh(invoice)
    if payment_link_row:
        await session.refresh(payment_link_row)

    return InvoicePublic(
        id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        customer_email=invoice.customer_email,
        line_items=[InvoiceLineItem(**item) for item in serialized_items],
        amount=str(invoice.amount_value),
        currency=invoice.amount_currency,
        status=invoice.status,
        due_at=invoice.due_at,
        payment_link=_serialize_link(payment_link_row) if payment_link_row else None,
        created_at=invoice.created_at,
    )


@pay_router.get("/invoices/{invoice_id}", response_model=InvoicePublic)
async def get_invoice(
    invoice_id: str,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    try:
        parsed = UUID(invoice_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Invoice not found") from exc
    invoice = await session.get(MerchantInvoice, parsed)
    if invoice is None or str(invoice.owner_user_id) != user_id:
        raise HTTPException(status_code=404, detail="Invoice not found")
    link = None
    if invoice.payment_link_id:
        link_row = await session.get(PaymentLink, invoice.payment_link_id)
        if link_row:
            link = _serialize_link(link_row)
    return InvoicePublic(
        id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        customer_email=invoice.customer_email,
        line_items=[InvoiceLineItem(**item) for item in (invoice.line_items_json or [])],
        amount=str(invoice.amount_value),
        currency=invoice.amount_currency,
        status=invoice.status,
        due_at=invoice.due_at,
        payment_link=link,
        created_at=invoice.created_at,
    )


@merchant_router.get("/dashboard", response_model=MerchantDashboardPublic)
async def merchant_dashboard(session: DbSession, user_id: str = Depends(require_auth)):
    user_uuid = UUID(user_id)
    merchant = await get_or_create_merchant_account(session, user_uuid)
    total_links = int(
        await session.scalar(
            select(func.count()).select_from(PaymentLink).where(PaymentLink.owner_user_id == user_uuid)
        )
        or 0
    )
    paid_links = int(
        await session.scalar(
            select(func.count())
            .select_from(PaymentLink)
            .where(PaymentLink.owner_user_id == user_uuid, PaymentLink.status == "paid")
        )
        or 0
    )
    pending_links = int(
        await session.scalar(
            select(func.count())
            .select_from(PaymentLink)
            .where(PaymentLink.owner_user_id == user_uuid, PaymentLink.status == "pending")
        )
        or 0
    )
    volume = await merchant_volume_total(session, user_uuid)
    recent = await session.scalars(
        select(PaymentLink)
        .where(PaymentLink.owner_user_id == user_uuid)
        .order_by(desc(PaymentLink.created_at))
        .limit(10)
    )
    return MerchantDashboardPublic(
        account=_serialize_account(merchant),
        total_links=total_links,
        paid_links=paid_links,
        pending_links=pending_links,
        total_volume_acp=str(volume),
        recent_links=[_serialize_link(row) for row in recent],
    )


@merchant_router.get("/export.csv")
async def merchant_export_csv(session: DbSession, user_id: str = Depends(require_auth)):
    user_uuid = UUID(user_id)
    rows = await session.scalars(
        select(PaymentLink).where(PaymentLink.owner_user_id == user_uuid).order_by(desc(PaymentLink.created_at))
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["code", "title", "amount", "currency", "status", "created_at", "paid_by"])
    for row in rows:
        writer.writerow(
            [
                row.code,
                row.title,
                str(row.amount_value),
                row.amount_currency,
                row.status,
                row.created_at.isoformat() if row.created_at else "",
                str(row.payer_user_id or ""),
            ]
        )
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="ancap-merchant-payments.csv"'},
    )


@pay_router.get("/invoices/{invoice_id}/export.txt")
async def export_invoice_text(
    invoice_id: str,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    try:
        parsed = UUID(invoice_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Invoice not found") from exc
    invoice = await session.get(MerchantInvoice, parsed)
    if invoice is None or str(invoice.owner_user_id) != user_id:
        raise HTTPException(status_code=404, detail="Invoice not found")
    lines = [
        f"ANCAP Invoice {invoice.invoice_number}",
        f"Status: {invoice.status}",
        f"Customer: {invoice.customer_email or '—'}",
        f"Amount: {invoice.amount_value} {invoice.amount_currency}",
        f"Due: {invoice.due_at.isoformat() if invoice.due_at else '—'}",
        "",
        "Line items:",
    ]
    for item in invoice.line_items_json or []:
        if isinstance(item, dict):
            lines.append(
                f"- {item.get('description', 'Item')} x{item.get('quantity', 1)} @ {item.get('unit_amount')} {item.get('currency', invoice.amount_currency)}"
            )
    if invoice.notes:
        lines.extend(["", f"Notes: {invoice.notes}"])
    body = "\n".join(lines)
    return Response(
        content=body,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{invoice.invoice_number}.txt"'},
    )


@pay_router.get("/{code}/qr")
async def payment_link_qr_meta(code: str, session: DbSession):
    """QR checkout metadata for static/dynamic merchant payment links."""
    row = await session.scalar(select(PaymentLink).where(PaymentLink.code == code))
    if row is None:
        raise HTTPException(status_code=404, detail="Payment link not found")
    pay_url = pay_url_for_code(row.code)
    acp_uri = f"acp:{row.owner_user_id}?amount={row.amount_value}&currency={row.amount_currency}&code={row.code}"
    return {
        "code": row.code,
        "title": row.title,
        "amount": str(row.amount_value),
        "currency": row.amount_currency,
        "status": row.status,
        "pay_url": pay_url,
        "acp_payment_uri": acp_uri,
        "qr_payload": pay_url,
    }


@merchant_router.get("/payments")
async def list_merchant_payments(session: DbSession, user_id: str = Depends(require_auth)):
    user_uuid = UUID(user_id)
    rows = await session.scalars(
        select(PaymentLink).where(PaymentLink.owner_user_id == user_uuid).order_by(desc(PaymentLink.created_at))
    )
    return {"items": [_serialize_link(row) for row in rows]}
