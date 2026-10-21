from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID
from urllib.parse import urlsplit

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import PaymentIntent, PaymentIntentStatusEnum, User
from app.schemas import (
    PaymentMethodCardPublic,
    PaymentMethodPublic,
    PaymentMethodsResponse,
    StripeIntentCreateRequest,
    StripeIntentSessionPublic,
    WorkflowCreditPackagePublic,
)
from app.services.workflow_execution import find_credit_package

_ZERO_DECIMAL_CURRENCIES = {
    "bif",
    "clp",
    "djf",
    "gnf",
    "jpy",
    "kmf",
    "krw",
    "mga",
    "pyg",
    "rwf",
    "ugx",
    "vnd",
    "vuv",
    "xaf",
    "xof",
    "xpf",
}
# Card top-ups are USD-only until a real FX quote path exists (EUR previously
# charged the ACP sticker 1:1 as euros).
SUPPORTED_STRIPE_CURRENCIES = ("USD",)
_SUPPORTED_STRIPE_CURRENCIES = SUPPORTED_STRIPE_CURRENCIES
_SUPPORTED_STRIPE_CURRENCY_SET = {code.lower() for code in SUPPORTED_STRIPE_CURRENCIES}
_STRIPE_API_BASE = "https://api.stripe.com/v1"


def _stripe_request_base(settings) -> str:
    configured = (settings.stripe_api_base or _STRIPE_API_BASE).rstrip("/")
    if configured == _STRIPE_API_BASE:
        # Return a constant for the production request sink, not the configured URL.
        return _STRIPE_API_BASE
    if settings.environment in {"development", "test"} and settings.stripe_allow_local_test_api:
        try:
            parsed = urlsplit(configured)
            valid_port = parsed.port is None or 1 <= parsed.port <= 65535
        except ValueError:
            parsed = None
            valid_port = False
        if parsed and valid_port and parsed.scheme in {"http", "https"} and parsed.hostname in {"localhost", "127.0.0.1", "::1"} and not (
            parsed.username or parsed.password or parsed.query or parsed.fragment
        ) and parsed.path == "/v1":
            return configured
    raise HTTPException(status_code=503, detail="Stripe API endpoint configuration is not allowed")


def stripe_is_configured() -> bool:
    settings = get_settings()
    return bool((settings.stripe_secret_key or "").strip() and (settings.stripe_publishable_key or "").strip())


def require_stripe_configured() -> None:
    if stripe_is_configured():
        return
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Stripe payments are not configured",
    )


def normalize_stripe_currency(currency: str) -> str:
    currency_code = (currency or "USD").strip().upper()
    if currency_code.lower() not in _SUPPORTED_STRIPE_CURRENCY_SET:
        supported = ", ".join(_SUPPORTED_STRIPE_CURRENCIES)
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported Stripe currency. Supported values: {supported}",
        )
    return currency_code


def quote_stripe_credit_package_amount(
    package: WorkflowCreditPackagePublic,
    currency: str,
) -> Decimal:
    normalize_stripe_currency(currency)
    # First Stripe slice: keep package sticker price as the fiat adapter baseline.
    return Decimal(package.price.amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def amount_to_minor_units(amount: Decimal, currency: str) -> int:
    normalized_currency = normalize_stripe_currency(currency).lower()
    if normalized_currency in _ZERO_DECIMAL_CURRENCIES:
        return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return int((amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


async def _stripe_request(
    method: str,
    path: str,
    *,
    data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    secret_key = (settings.stripe_secret_key or "").strip()
    if not secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe secret key is not configured",
        )

    base_url = _stripe_request_base(settings)
    if not re.fullmatch(
        r"/(?:customers(?:/cus_[A-Za-z0-9_-]+/payment_methods)?|"
        r"payment_intents(?:/pi_[A-Za-z0-9_-]+)?|payment_methods/pm_[A-Za-z0-9_-]+(?:/detach)?)",
        path,
    ):
        raise HTTPException(status_code=400, detail="Invalid Stripe API path")
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=False) as client:
            response = await client.request(
                method.upper(),
                f"{base_url}{path}",
                data=data,
                params=params,
                headers={
                    "Authorization": f"Bearer {secret_key}",
                    "Accept": "application/json",
                },
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe API is temporarily unavailable",
        ) from exc

    if response.status_code >= 300:
        detail = "Stripe API request failed"
        try:
            payload = response.json()
            message = ((payload.get("error") or {}).get("message") or "").strip()
            if message:
                detail = f"Stripe API request failed: {message}"
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)

    try:
        return response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe API returned invalid JSON",
        ) from exc


async def get_user_or_404(session: AsyncSession, user_id: str) -> User:
    try:
        parsed_user_id = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc

    user = (
        await session.execute(
            select(User).where(User.id == parsed_user_id).limit(1)
        )
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def get_or_create_stripe_customer(session: AsyncSession, user: User) -> str:
    existing_customer_id = (user.stripe_customer_id or "").strip()
    if existing_customer_id:
        return existing_customer_id

    payload = await _stripe_request(
        "POST",
        "/customers",
        data={
            "email": user.email,
            "name": (user.display_name or user.email),
            "metadata[ancap_user_id]": str(user.id),
            "metadata[ancap_source]": "ancap",
        },
    )
    customer_id = str(payload.get("id") or "").strip()
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe customer creation did not return an id",
        )
    user.stripe_customer_id = customer_id
    await session.flush()
    return customer_id


async def get_stripe_payment_method_for_customer(payment_method_id: str, customer_id: str) -> dict[str, Any]:
    normalized_payment_method_id = (payment_method_id or "").strip()
    normalized_customer_id = (customer_id or "").strip()
    if not normalized_payment_method_id or not normalized_customer_id:
        raise HTTPException(status_code=404, detail="Payment method not found")

    payload = await _stripe_request("GET", f"/payment_methods/{normalized_payment_method_id}")
    payment_method_customer_id = str(payload.get("customer") or "").strip()
    if payment_method_customer_id != normalized_customer_id:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return payload


async def create_stripe_credit_topup_intent(
    session: AsyncSession,
    user: User,
    body: StripeIntentCreateRequest,
) -> tuple[PaymentIntent, WorkflowCreditPackagePublic, StripeIntentSessionPublic]:
    require_stripe_configured()

    package = find_credit_package(body.package_slug)
    if package is None:
        raise HTTPException(status_code=404, detail="Credit package not found")

    currency = normalize_stripe_currency(body.currency or "USD")
    quoted_amount = quote_stripe_credit_package_amount(package, currency)
    customer_id = await get_or_create_stripe_customer(session, user)
    payment_method_selection = "saved_method" if body.payment_method_id else "new_card"

    if body.payment_method_id:
        await get_stripe_payment_method_for_customer(body.payment_method_id, customer_id)

    request_data: dict[str, Any] = {
        "amount": str(amount_to_minor_units(quoted_amount, currency)),
        "currency": currency.lower(),
        "customer": customer_id,
        "automatic_payment_methods[enabled]": "true",
        "description": f"ANCAP {package.title}",
        "metadata[ancap_user_id]": str(user.id),
        "metadata[ancap_package_slug]": package.slug,
        "metadata[ancap_credit_amount]": package.credit_amount.amount,
        "metadata[ancap_credit_currency]": package.credit_amount.currency,
        "metadata[ancap_source]": "ancap_credit_topup",
        "metadata[ancap_payment_method_selection]": payment_method_selection,
        "metadata[ancap_save_payment_method_requested]": "true" if body.save_payment_method else "false",
    }
    if body.payment_method_id:
        request_data["payment_method"] = body.payment_method_id
    if body.save_payment_method:
        request_data["setup_future_usage"] = "off_session"

    stripe_payload = await _stripe_request("POST", "/payment_intents", data=request_data)
    stripe_payment_intent_id = str(stripe_payload.get("id") or "").strip()
    client_secret = str(stripe_payload.get("client_secret") or "").strip()
    if not stripe_payment_intent_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe payment intent response was incomplete",
        )

    status_value = str(stripe_payload.get("status") or "requires_payment_method")
    payment_method_types = [str(item) for item in (stripe_payload.get("payment_method_types") or [])]

    intent = PaymentIntent(
        owner_user_id=user.id,
        workflow_run_id=None,
        intent_type="credit_topup",
        status=PaymentIntentStatusEnum.requires_payment.value,
        payment_method="stripe",
        amount_currency=currency,
        amount_value=quoted_amount,
        payment_reference=f"stripe:{stripe_payment_intent_id}",
        stripe_payment_intent_id=stripe_payment_intent_id,
        provider_payload_json={
            "package_slug": package.slug,
            "package_title": package.title,
            "credit_amount": package.credit_amount.model_dump(),
            "price": {"amount": str(quoted_amount), "currency": currency},
            "mode": "stripe",
            "stripe_customer_id": customer_id,
            "stripe_status": status_value,
            "payment_method_types": payment_method_types,
            "payment_method_selection": payment_method_selection,
            "save_payment_method": body.save_payment_method,
            "save_payment_method_requested": body.save_payment_method,
            "payment_method_id": body.payment_method_id,
            "requested_payment_method_id": body.payment_method_id,
            "note": body.note,
        },
    )
    session.add(intent)
    await session.flush()
    await session.refresh(intent)

    settings = get_settings()
    stripe_session = StripeIntentSessionPublic(
        customer_id=customer_id,
        payment_intent_id=stripe_payment_intent_id,
        client_secret=client_secret,
        publishable_key=(settings.stripe_publishable_key or "").strip(),
        amount={"amount": str(quoted_amount), "currency": currency},
        currency=currency,
        payment_method_types=payment_method_types,
        status=status_value,
    )
    return intent, package, stripe_session


async def fetch_stripe_payment_intent(stripe_payment_intent_id: str) -> dict[str, Any]:
    require_stripe_configured()
    normalized_id = (stripe_payment_intent_id or "").strip()
    if not normalized_id:
        raise HTTPException(status_code=400, detail="Stripe payment intent id is required")
    return await _stripe_request("GET", f"/payment_intents/{normalized_id}")


async def list_stripe_payment_methods_for_user(
    session: AsyncSession,
    user: User,
) -> PaymentMethodsResponse:
    require_stripe_configured()
    customer_id = (user.stripe_customer_id or "").strip()
    if not customer_id:
        return PaymentMethodsResponse(items=[])

    payload = await _stripe_request(
        "GET",
        f"/customers/{customer_id}/payment_methods",
        params={"type": "card"},
    )
    items: list[PaymentMethodPublic] = []
    for item in payload.get("data") or []:
        card = item.get("card") or {}
        items.append(
            PaymentMethodPublic(
                id=str(item.get("id") or ""),
                type=str(item.get("type") or "card"),
                customer_id=str(item.get("customer") or customer_id or "") or None,
                reusable=bool(item.get("customer")),
                card=PaymentMethodCardPublic(
                    brand=(card.get("brand") or None),
                    last4=(card.get("last4") or None),
                    exp_month=card.get("exp_month"),
                    exp_year=card.get("exp_year"),
                    funding=(card.get("funding") or None),
                    country=(card.get("country") or None),
                ),
            )
        )
    return PaymentMethodsResponse(items=items)


async def detach_stripe_payment_method_for_user(
    session: AsyncSession,
    user: User,
    payment_method_id: str,
) -> None:
    require_stripe_configured()
    customer_id = (user.stripe_customer_id or "").strip()
    if not customer_id:
        raise HTTPException(status_code=404, detail="Payment method not found")

    await get_stripe_payment_method_for_customer(payment_method_id, customer_id)
    await _stripe_request("POST", f"/payment_methods/{payment_method_id}/detach")


def build_stripe_webhook_signature(payload: bytes, secret: str, timestamp: int | None = None) -> str:
    signed_timestamp = int(time.time()) if timestamp is None else int(timestamp)
    signed_payload = f"{signed_timestamp}.{payload.decode('utf-8')}"
    signature = hmac.new(secret.encode("utf-8"), signed_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"t={signed_timestamp},v1={signature}"


def parse_stripe_webhook_event(
    payload: bytes,
    stripe_signature: str | None,
    secret: str,
    *,
    tolerance_seconds: int = 300,
) -> dict[str, Any]:
    header_value = (stripe_signature or "").strip()
    if not header_value:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    timestamp: int | None = None
    signatures: list[str] = []
    for part in header_value.split(","):
        key, _, value = part.partition("=")
        if key == "t":
            try:
                timestamp = int(value)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid Stripe webhook timestamp") from exc
        elif key == "v1" and value:
            signatures.append(value)

    if timestamp is None or not signatures:
        raise HTTPException(status_code=400, detail="Invalid Stripe-Signature header")

    if tolerance_seconds > 0 and abs(int(time.time()) - timestamp) > tolerance_seconds:
        raise HTTPException(status_code=400, detail="Stripe webhook timestamp is outside the allowed tolerance")

    signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
    expected = hmac.new(secret.encode("utf-8"), signed_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, candidate) for candidate in signatures):
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook signature")

    try:
        return json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Stripe webhook payload is not valid JSON") from exc
