from __future__ import annotations

import secrets
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.constants import PLATFORM_ACCOUNT_OWNER_ID
from app.db.models import (
    LedgerEventTypeEnum,
    MerchantAccount,
    PaymentIntent,
    PaymentIntentStatusEnum,
    PaymentLink,
)
from app.services.ledger import append_event, balance_for_account, get_or_create_account, is_ledger_invariant_halted


def generate_payment_code() -> str:
    return secrets.token_urlsafe(9).replace("-", "")[:12].lower()


def pay_url_for_code(code: str) -> str:
    settings = get_settings()
    base = (settings.public_app_url or "https://ancap.cloud").rstrip("/")
    return f"{base}/pay/{code}"


async def get_or_create_merchant_account(session: AsyncSession, user_id: UUID) -> MerchantAccount:
    row = await session.scalar(select(MerchantAccount).where(MerchantAccount.owner_user_id == user_id))
    if row is not None:
        return row
    row = MerchantAccount(owner_user_id=user_id, display_name="Merchant")
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return row


async def capture_payment_link_credits(
    session: AsyncSession,
    *,
    link: PaymentLink,
    payer_user_id: UUID,
    payment_reference: str | None,
) -> tuple[PaymentIntent, str]:
    if await is_ledger_invariant_halted(session):
        raise HTTPException(status_code=503, detail="Ledger invariant violated; operations temporarily blocked")

    if link.status == "paid":
        raise HTTPException(status_code=409, detail="Payment link already paid")
    if link.expires_at and link.expires_at < datetime.now(UTC):
        link.status = "expired"
        await session.flush()
        raise HTTPException(status_code=410, detail="Payment link expired")

    amount = Decimal(str(link.amount_value))
    currency = link.amount_currency.upper()
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid payment link amount")

    merchant = await session.get(MerchantAccount, link.merchant_account_id)
    if merchant is None:
        raise HTTPException(status_code=404, detail="Merchant account not found")

    fee_bps = max(0, int(merchant.fee_bps or 0))
    platform_fee = (amount * Decimal(fee_bps) / Decimal(10000)).quantize(Decimal("0.00000001"))
    merchant_net = amount - platform_fee

    payer_acc = await get_or_create_account(session, "user", payer_user_id)
    balances = await balance_for_account(session, payer_acc.id, currency)
    available = balances.get(currency) or Decimal(0)
    if available < amount:
        raise HTTPException(
            status_code=402,
            detail={
                "message": "Insufficient credits",
                "currency": currency,
                "required": str(amount),
                "available": str(available),
            },
        )

    intent = PaymentIntent(
        owner_user_id=payer_user_id,
        workflow_run_id=None,
        intent_type="merchant_payment",
        status=PaymentIntentStatusEnum.requires_payment.value,
        payment_method="credits",
        amount_currency=currency,
        amount_value=amount,
        payment_reference=payment_reference,
        provider_payload_json={
            "payment_link_id": str(link.id),
            "payment_link_code": link.code,
            "merchant_user_id": str(link.owner_user_id),
        },
    )
    session.add(intent)
    await session.flush()

    merchant_acc = await get_or_create_account(session, "user", UUID(str(link.owner_user_id)))
    ev = await append_event(
        session,
        LedgerEventTypeEnum.transfer,
        currency,
        merchant_net,
        src_account_id=payer_acc.id,
        dst_account_id=merchant_acc.id,
        metadata={
            "type": "merchant_payment_capture",
            "payment_intent_id": str(intent.id),
            "payment_link_id": str(link.id),
            "payment_link_code": link.code,
        },
    )
    ledger_event_id = str(ev.id)

    if platform_fee > 0:
        # Unified platform revenue account (owner_type=system): all platform
        # fees land here so staking rewards and treasury sweeps see one bucket.
        fees_acc = await get_or_create_account(session, "system", PLATFORM_ACCOUNT_OWNER_ID)
        await append_event(
            session,
            LedgerEventTypeEnum.fee,
            currency,
            platform_fee,
            src_account_id=payer_acc.id,
            dst_account_id=fees_acc.id,
            metadata={
                "type": "merchant_platform_fee",
                "payment_intent_id": str(intent.id),
                "payment_link_id": str(link.id),
                "fee_bps": fee_bps,
            },
        )

    intent.status = PaymentIntentStatusEnum.captured.value
    intent.capture_ledger_event_id = ev.id
    intent.payment_reference = payment_reference or f"pay:{link.code}"
    intent.updated_at = datetime.now(UTC)

    link.status = "paid"
    link.payer_user_id = payer_user_id
    link.payment_intent_id = intent.id
    link.updated_at = datetime.now(UTC)

    await session.flush()
    return intent, ledger_event_id


async def merchant_volume_total(session: AsyncSession, owner_user_id: UUID) -> Decimal:
    result = await session.scalar(
        select(func.coalesce(func.sum(PaymentLink.amount_value), 0)).where(
            PaymentLink.owner_user_id == owner_user_id,
            PaymentLink.status == "paid",
        )
    )
    return Decimal(str(result or 0))
