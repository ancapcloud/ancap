from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class MerchantAccountPublic(BaseModel):
    id: str
    display_name: str
    plan_tier: str
    fee_bps: int
    created_at: datetime


class PaymentLinkCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    amount: str
    currency: str = "ACP"
    expires_in_hours: int | None = Field(default=168, ge=1, le=8760)


class PaymentLinkPublic(BaseModel):
    id: str
    code: str
    title: str
    description: str | None
    amount: str
    currency: str
    status: str
    pay_url: str
    qr_url: str
    expires_at: datetime | None
    created_at: datetime
    payment_intent_id: str | None = None
    proof_url: str | None = None


class PaymentLinkCheckoutRequest(BaseModel):
    payment_method: str = "credits"
    payment_reference: str | None = None


class PaymentLinkCheckoutResponse(BaseModel):
    payment_link: PaymentLinkPublic
    payment_intent_id: str
    status: str
    ledger_event_id: str | None = None


class InvoiceLineItem(BaseModel):
    description: str
    quantity: Decimal = Field(default=Decimal("1"), gt=0, le=1000000000, allow_inf_nan=False)
    unit_amount: str
    currency: str = "ACP"


class InvoiceCreateRequest(BaseModel):
    customer_email: str | None = None
    line_items: list[InvoiceLineItem] = Field(min_length=1, max_length=200)
    due_in_days: int | None = Field(default=14, ge=1, le=365)
    notes: str | None = None
    create_payment_link: bool = True


class InvoicePublic(BaseModel):
    id: str
    invoice_number: str
    customer_email: str | None
    line_items: list[InvoiceLineItem]
    amount: str
    currency: str
    status: str
    due_at: datetime | None
    payment_link: PaymentLinkPublic | None = None
    created_at: datetime


class MerchantDashboardPublic(BaseModel):
    account: MerchantAccountPublic
    total_links: int
    paid_links: int
    pending_links: int
    total_volume_acp: str
    recent_links: list[PaymentLinkPublic]
