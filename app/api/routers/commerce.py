from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import desc, func, select

from app.api.deps import DbSession, require_auth, require_platform_admin
from app.db.models import ClaimCode, MerchantAccount, PaymentLink, RampWaitlistEntry
from app.schemas.helio import HelioAdapterStatusPublic, HelioWebhookAck
from app.schemas.webid import (
    WebIdAdapterStatusPublic,
    WebIdSessionStartRequest,
    WebIdSessionStartResponse,
    WebIdWebhookAck,
)
from app.services.helio_commerce import (
    helio_public_status,
    parse_helio_json_body,
    summarize_helio_webhook,
    verify_helio_webhook_signature,
)
from app.services.webid_kyc import (
    WebIdNotConfigured,
    WebIdUpstreamError,
    parse_webid_json_body,
    start_webid_session,
    summarize_webid_webhook,
    verify_webid_webhook_signature,
    webid_public_status,
)
from app.services.merchant_pay import get_or_create_merchant_account

router = APIRouter(prefix="/commerce", tags=["Commerce"])

COMMERCE_PLANS = [
    {
        "tier": "free",
        "label": "Free",
        "monthly_price_acp": "0",
        "payment_links_limit": 5,
        "mcp_enabled": False,
        "api_monthly_cap_acp": "10",
    },
    {
        "tier": "pro",
        "label": "Pro",
        "monthly_price_acp": "49",
        "payment_links_limit": 50,
        "mcp_enabled": True,
        "api_monthly_cap_acp": "100",
    },
    {
        "tier": "merchant",
        "label": "Merchant",
        "monthly_price_acp": "149",
        "payment_links_limit": 500,
        "mcp_enabled": True,
        "api_monthly_cap_acp": "500",
    },
    {
        "tier": "developer",
        "label": "Developer",
        "monthly_price_acp": "199",
        "payment_links_limit": 100,
        "mcp_enabled": True,
        "api_monthly_cap_acp": "2000",
    },
]


class RampWaitlistRequest(BaseModel):
    email: EmailStr
    interest: str = Field(default="stablecoin_topup", max_length=64)
    region: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=500)


class PlanSelectRequest(BaseModel):
    tier: str = Field(pattern="^(free|pro|merchant|developer|starter)$")


@router.get("/plans")
async def list_commerce_plans():
    return {"items": COMMERCE_PLANS}


@router.post("/plans/select")
async def select_commerce_plan(body: PlanSelectRequest, session: DbSession, user_id: str = Depends(require_auth)):
    tier = body.tier if body.tier != "starter" else "free"
    if tier not in {plan["tier"] for plan in COMMERCE_PLANS}:
        raise HTTPException(status_code=400, detail="Unknown plan tier")
    account = await get_or_create_merchant_account(session, UUID(user_id))
    account.plan_tier = tier
    account.updated_at = datetime.now(UTC)
    await session.flush()
    return {"status": "ok", "plan_tier": account.plan_tier}


@router.post("/ramp-waitlist", status_code=201)
async def join_ramp_waitlist(body: RampWaitlistRequest, session: DbSession):
    existing = await session.scalar(
        select(RampWaitlistEntry).where(
            RampWaitlistEntry.email == body.email.strip().lower(),
            RampWaitlistEntry.interest == body.interest,
        )
    )
    if existing:
        return {
            "status": "already_registered",
            "id": str(existing.id),
            "created_at": existing.created_at,
        }
    row = RampWaitlistEntry(
        email=body.email.strip().lower(),
        interest=body.interest,
        region=(body.region or "").strip() or None,
        notes=(body.notes or "").strip() or None,
        status="pending",
    )
    session.add(row)
    await session.flush()
    return {"status": "registered", "id": str(row.id), "created_at": row.created_at}


@router.get("/ramp-waitlist")
async def list_ramp_waitlist(session: DbSession, _admin: str = Depends(require_platform_admin)):
    rows = (
        await session.scalars(select(RampWaitlistEntry).order_by(desc(RampWaitlistEntry.created_at)).limit(500))
    ).all()
    return {
        "items": [
            {
                "id": str(row.id),
                "email": row.email,
                "interest": row.interest,
                "region": row.region,
                "notes": row.notes,
                "status": row.status,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    }


@router.get("/helio/status", response_model=HelioAdapterStatusPublic)
async def helio_adapter_status():
    """Public checkout config for /buy-acp — never returns secret keys."""
    return helio_public_status()


@router.get("/webid/status", response_model=WebIdAdapterStatusPublic)
async def webid_adapter_status():
    """Public WebID KYC partner-slot status — never returns secrets; never claims card issuing."""
    return webid_public_status()


@router.post("/webid/session", response_model=WebIdSessionStartResponse)
async def webid_start_session(
    body: WebIdSessionStartRequest,
    user_id: str = Depends(require_auth),
):
    """Start WebID KYC/KYB identification (fail-closed without commercial credentials)."""
    try:
        return await start_webid_session(
            user_id=user_id,
            return_url=str(body.return_url) if body.return_url else None,
            product=body.product,
            locale=body.locale,
        )
    except WebIdNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except WebIdUpstreamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/webid/webhook", response_model=WebIdWebhookAck)
async def webid_status_webhook(
    request: Request,
    x_signature: str | None = Header(default=None, alias="X-Signature"),
    x_webid_signature: str | None = Header(default=None, alias="X-WebID-Signature"),
):
    """Ack WebID identification status webhooks (HMAC-SHA256). Identity only — no card mint."""
    raw = await request.body()
    signature = x_webid_signature or x_signature
    if not verify_webid_webhook_signature(raw, signature):
        raise HTTPException(status_code=401, detail="Invalid WebID webhook signature")
    payload = parse_webid_json_body(raw)
    meta = summarize_webid_webhook(payload)
    return WebIdWebhookAck(
        status="ok",
        event=meta.get("event"),
        action_id=meta.get("action_id"),
        identification_status=meta.get("identification_status"),
    )


@router.post("/helio/webhook", response_model=HelioWebhookAck)
async def helio_paylink_webhook(
    request: Request,
    x_signature: str | None = Header(default=None, alias="X-Signature"),
):
    """Verify MoonPay Commerce pay-link webhooks (HMAC-SHA256 sharedToken)."""
    raw = await request.body()
    if not verify_helio_webhook_signature(raw, x_signature):
        raise HTTPException(status_code=401, detail="Invalid Helio webhook signature")
    payload = parse_helio_json_body(raw)
    meta = summarize_helio_webhook(payload)
    return HelioWebhookAck(
        status="ok",
        event=meta.get("event"),
        transaction_id=meta.get("transaction_id"),
    )


@router.get("/metrics")
async def commerce_metrics(session: DbSession, _admin: str = Depends(require_platform_admin)):
    payment_links = int(await session.scalar(select(func.count()).select_from(PaymentLink)) or 0)
    active_merchants = int(
        await session.scalar(
            select(func.count(func.distinct(PaymentLink.owner_user_id))).where(PaymentLink.status == "active")
        )
        or 0
    )
    claim_redemptions = int(
        await session.scalar(select(func.coalesce(func.sum(ClaimCode.redemption_count), 0))) or 0
    )
    claim_codes_active = int(
        await session.scalar(select(func.count()).select_from(ClaimCode).where(ClaimCode.status == "active")) or 0
    )
    ramp_waitlist = int(await session.scalar(select(func.count()).select_from(RampWaitlistEntry)) or 0)
    return {
        "payment_links_total": payment_links,
        "active_merchants_estimate": active_merchants,
        "claim_codes_active": claim_codes_active,
        "claim_redemptions_total": claim_redemptions,
        "ramp_waitlist_signups": ramp_waitlist,
        "exported_at": datetime.now(UTC).isoformat(),
    }


def plan_limit_for_tier(tier: str, key: str) -> int | Decimal:
    for plan in COMMERCE_PLANS:
        if plan["tier"] == tier:
            return plan.get(key, 0)
    return COMMERCE_PLANS[0].get(key, 0)


async def enforce_payment_link_plan_limit(session: DbSession, account: MerchantAccount) -> None:
    limit = int(plan_limit_for_tier(account.plan_tier or "free", "payment_links_limit"))
    active_count = int(
        await session.scalar(
            select(func.count())
            .select_from(PaymentLink)
            .where(PaymentLink.owner_user_id == account.owner_user_id, PaymentLink.status == "active")
        )
        or 0
    )
    if active_count >= limit:
        raise HTTPException(
            status_code=402,
            detail=f"Payment link limit reached for plan '{account.plan_tier}' ({limit}). Upgrade at /commerce/plans.",
        )
