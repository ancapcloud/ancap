from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import csv
import hashlib
import hmac
import io
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from sqlalchemy import desc, func, select
from sqlalchemy.orm.attributes import flag_modified

from app.api.deps import DbSession, require_auth, require_platform_admin
from app.constants import PLATFORM_ACCOUNT_OWNER_ID
from app.db.models import Agent, ApiKey, ApiUsageEvent, LedgerEventTypeEnum, Organization
from app.schemas import (
    Money,
    PaidApiAnalyzeRequest,
    PaidApiAnalyzeResponse,
    PaidApiProductPublic,
    PaidApiProductsResponse,
    PaidApiRevenueEndpointSummaryPublic,
    PaidApiRevenueMoneyPublic,
    PaidApiRevenueOrganizationSummaryPublic,
    PaidApiRevenueSummaryPublic,
    PaidApiSpendCapRequest,
    PaidApiSpendCapResponse,
    PaidApiUsageEventsResponse,
    PaidApiUsagePublic,
)
from app.services.api_keys import resolve_key_record
from app.services.idempotency import get_idempotency_hit, store_idempotency_result
from app.services.ledger import append_event, balance_for_account, get_or_create_account, is_ledger_invariant_halted
from app.services.org_nfc_policy import require_nfc_for_payments


router = APIRouter(prefix="/paid-api", tags=["Paid API"])

PAID_API_PROVIDER_COST_RATE = Decimal("0.18")


def _x402_terms(product_slug: str, amount: str, currency: str = "ACP") -> dict[str, object]:
    return {
        "version": "x402-compatible-preview",
        "accepts": [{"scheme": "exact", "network": "base", "currency": currency, "amount": amount}],
        "resource": f"https://ancap.cloud/api/v1/paid-api/{product_slug}",
        "pay_to": "ancap-workflow-treasury",
        "proof_url_template": "https://ancap.cloud/proof-center?run={workflow_run_id}",
    }


PAID_API_PRODUCTS: list[PaidApiProductPublic] = [
    PaidApiProductPublic(
        slug="token-risk",
        title="Token Risk Snapshot",
        description="Score token risk using lightweight launch, liquidity, and trust signals.",
        endpoint="/paid-api/token-risk",
        price=Money(amount="2.00", currency="ACP"),
        accepted_currencies=["ACP"],
        tags=["risk", "token", "api"],
        x402=_x402_terms("token-risk", "2.00"),
    ),
    PaidApiProductPublic(
        slug="listing-readiness",
        title="Listing Readiness Score",
        description="Check whether a token/project profile is ready for directory or exchange submissions.",
        endpoint="/paid-api/listing-readiness",
        price=Money(amount="1.50", currency="ACP"),
        accepted_currencies=["ACP"],
        tags=["listing", "launch", "api"],
        x402=_x402_terms("listing-readiness", "1.50"),
    ),
    PaidApiProductPublic(
        slug="wallet-risk",
        title="Wallet Risk Snapshot",
        description="Score a wallet reference for operational, concentration, and behavior risk.",
        endpoint="/paid-api/wallet-risk",
        price=Money(amount="2.00", currency="ACP"),
        accepted_currencies=["ACP"],
        tags=["wallet", "risk", "api"],
        x402=_x402_terms("wallet-risk", "2.00"),
    ),
    PaidApiProductPublic(
        slug="bridge-proof",
        title="Bridge Proof Check",
        description="Produce a compact proof-readiness result for bridge transaction references.",
        endpoint="/paid-api/bridge-proof",
        price=Money(amount="1.00", currency="ACP"),
        accepted_currencies=["ACP"],
        tags=["bridge", "proof", "api"],
        x402=_x402_terms("bridge-proof", "1.00"),
    ),
    PaidApiProductPublic(
        slug="campaign-score",
        title="Campaign Score",
        description="Score campaign inputs for clarity, channel fit, proof quality, and spam risk.",
        endpoint="/paid-api/campaign-score",
        price=Money(amount="1.00", currency="ACP"),
        accepted_currencies=["ACP"],
        tags=["campaign", "growth", "api"],
        x402=_x402_terms("campaign-score", "1.00"),
    ),
]


def _product(product_slug: str) -> PaidApiProductPublic:
    item = next((product for product in PAID_API_PRODUCTS if product.slug == product_slug), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Paid API product not found")
    return item


def _serialize_usage(row: ApiUsageEvent) -> PaidApiUsagePublic:
    return PaidApiUsagePublic(
        id=str(row.id),
        agent_id=str(row.agent_id),
        owner_user_id=str(row.owner_user_id) if row.owner_user_id else None,
        api_key_prefix=row.api_key_prefix,
        product_slug=row.product_slug,
        endpoint=row.endpoint,
        status=row.status,
        amount=Money(amount=str(row.amount_value), currency=row.amount_currency),
        ledger_event_id=str(row.ledger_event_id) if row.ledger_event_id else None,
        request_hash=row.request_hash,
        created_at=row.created_at,
    )


def _hash_request(body: PaidApiAnalyzeRequest) -> str:
    payload = body.model_dump(mode="json")
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _agent_spend_caps(agent: Agent) -> dict[str, str]:
    metadata = agent.metadata_ if isinstance(agent.metadata_, dict) else {}
    caps = metadata.get("paid_api_spend_caps") if isinstance(metadata.get("paid_api_spend_caps"), dict) else {}
    return {str(currency).upper(): str(amount) for currency, amount in caps.items() if str(amount).strip()}


def _api_key_endpoint_spend_caps(row: ApiKey | None) -> dict[str, dict[str, str]]:
    if row is None or not isinstance(row.metadata_json, dict):
        return {}
    raw_caps = row.metadata_json.get("paid_api_spend_caps")
    if not isinstance(raw_caps, dict):
        return {}

    normalized: dict[str, dict[str, str]] = {}
    for endpoint, currency_map in raw_caps.items():
        endpoint_key = str(endpoint or "").strip()
        if not endpoint_key or not isinstance(currency_map, dict):
            continue
        normalized_currency_map: dict[str, str] = {}
        for currency, amount in currency_map.items():
            currency_key = str(currency or "").strip().upper()
            amount_value = str(amount or "").strip()
            if not currency_key or not amount_value:
                continue
            normalized_currency_map[currency_key] = amount_value
        if normalized_currency_map:
            normalized[endpoint_key] = normalized_currency_map
    return normalized


async def _api_key_30d_spend(session: DbSession, api_key_id: UUID, endpoint: str, currency: str) -> Decimal:
    since = datetime.now(UTC) - timedelta(days=30)
    total = (
        await session.execute(
            select(func.coalesce(func.sum(ApiUsageEvent.amount_value), 0)).where(
                ApiUsageEvent.amount_currency == currency,
                ApiUsageEvent.status == "captured",
                ApiUsageEvent.created_at >= since,
                ApiUsageEvent.metadata_json["api_key_id"].astext == str(api_key_id),
                ApiUsageEvent.endpoint == endpoint,
            )
        )
    ).scalar_one()
    return Decimal(str(total or "0"))


def _usage_cost_snapshot(row: ApiUsageEvent) -> tuple[Decimal, Decimal]:
    gross = Decimal(str(row.amount_value or "0"))
    metadata = row.metadata_json if isinstance(row.metadata_json, dict) else {}
    provider_cost = metadata.get("provider_cost") if isinstance(metadata.get("provider_cost"), dict) else None
    margin = metadata.get("estimated_margin") if isinstance(metadata.get("estimated_margin"), dict) else None

    try:
        if provider_cost and str(provider_cost.get("amount", "")).strip():
            provider_cost_amount = Decimal(str(provider_cost.get("amount", "0")))
        else:
            provider_cost_amount = (gross * PAID_API_PROVIDER_COST_RATE).quantize(Decimal("0.01"))
    except Exception:
        provider_cost_amount = Decimal("0")

    try:
        if margin and str(margin.get("amount", "")).strip():
            margin_amount = Decimal(str(margin.get("amount", "0")))
        else:
            margin_amount = (gross - provider_cost_amount).quantize(Decimal("0.01"))
    except Exception:
        margin_amount = Decimal("0")
    return provider_cost_amount, margin_amount


async def _agent_30d_spend(session: DbSession, agent_id: UUID, currency: str) -> Decimal:
    since = datetime.now(UTC) - timedelta(days=30)
    total = (
        await session.execute(
            select(func.coalesce(func.sum(ApiUsageEvent.amount_value), 0)).where(
                ApiUsageEvent.agent_id == agent_id,
                ApiUsageEvent.amount_currency == currency,
                ApiUsageEvent.status == "captured",
                ApiUsageEvent.created_at >= since,
            )
        )
    ).scalar_one()
    return Decimal(str(total or "0"))


async def _current_spend_map(session: DbSession, agent_id: UUID, caps: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for currency in sorted(caps.keys() or ["ACP"]):
        out[currency] = str(await _agent_30d_spend(session, agent_id, currency))
    return out


def _score_from_request(product_slug: str, body: PaidApiAnalyzeRequest) -> int:
    base = int(hashlib.sha256(f"{product_slug}:{body.subject}:{body.chain or ''}".encode("utf-8")).hexdigest()[:4], 16)
    signal_bonus = min(len(body.signals or {}) * 4, 24)
    metadata_bonus = min(len(body.metadata or {}) * 2, 10)
    return max(1, min(99, 35 + (base % 45) + signal_bonus + metadata_bonus))


def _build_result(product: PaidApiProductPublic, body: PaidApiAnalyzeRequest) -> dict:
    score = _score_from_request(product.slug, body)
    risk_level = "low" if score >= 76 else "medium" if score >= 48 else "high"
    subject = body.subject.strip()
    chain = (body.chain or "unknown").strip() or "unknown"

    if product.slug == "listing-readiness":
        missing = []
        for key in ("project_summary", "tokenomics", "links", "team_note"):
            if key not in body.signals:
                missing.append(key)
        return {
            "subject": subject,
            "chain": chain,
            "score": score,
            "readiness": "ready" if score >= 76 and not missing else "needs_review",
            "missing_fields": missing[:6],
            "recommendations": [
                "Keep short and long project descriptions aligned.",
                "Attach proof links for tokenomics, liquidity, and community channels.",
                "Use the workflow store listing pack for reusable exchange answers.",
            ],
        }

    if product.slug == "bridge-proof":
        return {
            "subject": subject,
            "chain": chain,
            "score": score,
            "proof_status": "review_ready" if score >= 60 else "needs_more_evidence",
            "required_evidence": ["source_tx", "destination_tx", "amount", "counterparty", "timestamp"],
            "proof_hash": hashlib.sha256(f"bridge-proof:{subject}:{chain}".encode("utf-8")).hexdigest(),
        }

    if product.slug == "campaign-score":
        return {
            "subject": subject,
            "score": score,
            "grade": "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "D",
            "channel_fit": sorted([str(item) for item in body.signals.get("channels", [])]) if isinstance(body.signals.get("channels"), list) else [],
            "flags": [] if score >= 70 else ["message clarity", "proof density", "anti-spam controls"],
        }

    flags = []
    if score < 50:
        flags.extend(["concentration_review", "liquidity_review"])
    if "owner" not in body.signals:
        flags.append("owner_signal_missing")
    return {
        "subject": subject,
        "chain": chain,
        "score": score,
        "risk_level": risk_level,
        "flags": flags,
        "summary": f"{product.title} for {subject} on {chain}: {risk_level} risk signal.",
    }


async def _charge_usage(
    session: DbSession,
    *,
    product: PaidApiProductPublic,
    body: PaidApiAnalyzeRequest,
    raw_api_key: str | None,
) -> ApiUsageEvent:
    if await is_ledger_invariant_halted(session):
        raise HTTPException(status_code=503, detail="Ledger invariant violated; operations temporarily blocked")
    if not raw_api_key:
        raise HTTPException(status_code=401, detail="Agent identity required (X-API-Key)")
    resolved_key = await resolve_key_record(session, raw_api_key)
    if resolved_key is None or resolved_key.agent_id is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    agent_id = resolved_key.agent_id
    agent = await session.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    owner_user_id = UUID(str(agent.owner_user_id)) if agent.owner_user_id else None
    payer_type = "user" if owner_user_id else "agent"
    payer_id = owner_user_id or UUID(str(agent.id))
    payer_acc = await get_or_create_account(session, payer_type, payer_id)
    platform_acc = await get_or_create_account(session, "system", PLATFORM_ACCOUNT_OWNER_ID)

    resolved_org_id = str(resolved_key.org_id) if resolved_key.org_id else None
    if not resolved_org_id and isinstance(agent.metadata_, dict):
        raw_org_id = agent.metadata_.get("org_id")
        if isinstance(raw_org_id, str) and raw_org_id.strip():
            resolved_org_id = raw_org_id.strip()

    if resolved_org_id and owner_user_id is not None:
        await require_nfc_for_payments(
            session,
            org_id=UUID(resolved_org_id),
            user_id=owner_user_id,
        )

    currency = product.price.currency
    amount = Decimal(product.price.amount)
    caps = _agent_spend_caps(agent)
    cap_value = caps.get(currency)
    if cap_value is not None:
        current_spend = await _agent_30d_spend(session, UUID(str(agent.id)), currency)
        monthly_cap = Decimal(str(cap_value))
        if current_spend + amount > monthly_cap:
            raise HTTPException(
                status_code=402,
                detail={
                    "message": "Paid API monthly spend cap exceeded",
                    "code": "spend_cap_exceeded",
                    "currency": currency,
                    "monthly_cap": str(monthly_cap),
                    "current_30d_spend": str(current_spend),
                    "required": str(amount),
                    "x402": product.x402,
                },
            )

    endpoint_caps = _api_key_endpoint_spend_caps(await session.get(ApiKey, resolved_key.row_id))
    endpoint_cap_value = endpoint_caps.get(product.endpoint, {}).get(currency)
    if endpoint_cap_value is not None:
        endpoint_current_spend = await _api_key_30d_spend(session, resolved_key.row_id, product.endpoint, currency)
        endpoint_monthly_cap = Decimal(str(endpoint_cap_value))
        if endpoint_current_spend + amount > endpoint_monthly_cap:
            raise HTTPException(
                status_code=402,
                detail={
                    "message": "Paid API endpoint spend cap exceeded",
                    "code": "endpoint_spend_cap_exceeded",
                    "endpoint": product.endpoint,
                    "currency": currency,
                    "monthly_cap": str(endpoint_monthly_cap),
                    "current_30d_spend": str(endpoint_current_spend),
                    "required": str(amount),
                    "x402": product.x402,
                },
            )
    balances = await balance_for_account(session, payer_acc.id, currency)
    available = balances.get(currency) or Decimal(0)
    if available < amount:
        raise HTTPException(
            status_code=402,
            detail={
                "message": "Insufficient credits for paid API usage",
                "currency": currency,
                "required": str(amount),
                "available": str(available),
                "x402": product.x402,
            },
        )

    request_hash = _hash_request(body)
    ev = await append_event(
        session,
        LedgerEventTypeEnum.fee,
        currency,
        amount,
        src_account_id=payer_acc.id,
        dst_account_id=platform_acc.id,
        metadata={
            "type": "paid_api_usage_charge",
            "agent_id": str(agent.id),
            "owner_user_id": str(owner_user_id) if owner_user_id else None,
            "product_slug": product.slug,
            "endpoint": product.endpoint,
            "request_hash": request_hash,
            "org_id": resolved_org_id,
            "api_key_id": str(resolved_key.row_id),
        },
    )
    provider_cost_amount = (amount * PAID_API_PROVIDER_COST_RATE).quantize(Decimal("0.01"))
    estimated_margin_amount = (amount - provider_cost_amount).quantize(Decimal("0.01"))
    row = ApiUsageEvent(
        agent_id=UUID(str(agent.id)),
        owner_user_id=owner_user_id,
        api_key_prefix=resolved_key.key_prefix,
        product_slug=product.slug,
        endpoint=product.endpoint,
        status="captured",
        amount_currency=currency,
        amount_value=amount,
        ledger_event_id=ev.id,
        request_hash=request_hash,
        metadata_json={
            "payer_type": payer_type,
            "payer_id": str(payer_id),
            "org_id": resolved_org_id,
            "api_key_id": str(resolved_key.row_id),
            "provider_cost": {"amount": str(provider_cost_amount), "currency": currency},
            "estimated_margin": {"amount": str(estimated_margin_amount), "currency": currency},
        },
    )
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return row


@router.get("/products", response_model=PaidApiProductsResponse)
async def list_paid_api_products():
    return PaidApiProductsResponse(items=PAID_API_PRODUCTS)


@router.get("/me/usage", response_model=PaidApiUsageEventsResponse)
async def list_my_paid_api_usage(
    session: DbSession,
    user_id: str = Depends(require_auth),
    limit: int = Query(50, ge=1, le=200),
):
    rows = (
        await session.execute(
            select(ApiUsageEvent)
            .where(ApiUsageEvent.owner_user_id == UUID(user_id))
            .order_by(desc(ApiUsageEvent.created_at))
            .limit(limit)
        )
    ).scalars().all()
    totals_by_currency: dict[str, Decimal] = {}
    for row in rows:
        currency = (row.amount_currency or "ACP").upper()
        totals_by_currency[currency] = totals_by_currency.get(currency, Decimal("0")) + Decimal(str(row.amount_value or "0"))
    return PaidApiUsageEventsResponse(
        items=[_serialize_usage(row) for row in rows],
        exported_at=datetime.now(UTC),
        totals_by_currency={currency: str(amount) for currency, amount in totals_by_currency.items()},
    )


@router.get("/me/usage/export")
async def export_my_paid_api_usage_csv(
    session: DbSession,
    user_id: str = Depends(require_auth),
    limit: int = Query(500, ge=1, le=5000),
):
    rows = (
        await session.execute(
            select(ApiUsageEvent)
            .where(ApiUsageEvent.owner_user_id == UUID(user_id))
            .order_by(desc(ApiUsageEvent.created_at))
            .limit(limit)
        )
    ).scalars().all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "id",
        "created_at",
        "agent_id",
        "owner_user_id",
        "api_key_prefix",
        "product_slug",
        "endpoint",
        "status",
        "amount_currency",
        "amount_value",
        "ledger_event_id",
        "request_hash",
    ])
    for row in rows:
        writer.writerow([
            str(row.id),
            row.created_at.isoformat() if row.created_at else "",
            str(row.agent_id),
            str(row.owner_user_id) if row.owner_user_id else "",
            row.api_key_prefix or "",
            row.product_slug,
            row.endpoint,
            row.status,
            row.amount_currency,
            str(row.amount_value),
            str(row.ledger_event_id) if row.ledger_event_id else "",
            row.request_hash,
        ])
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    headers = {"Content-Disposition": f'attachment; filename="ancap-paid-api-usage-{timestamp}.csv"'}
    return Response(content=buffer.getvalue(), media_type="text/csv; charset=utf-8", headers=headers)


@router.get("/revenue-summary", response_model=PaidApiRevenueSummaryPublic)
async def paid_api_revenue_summary(
    session: DbSession,
    admin_user_id: str = Depends(require_platform_admin),
    days: int = Query(30, ge=1, le=365),
):
    _ = admin_user_id
    generated_at = datetime.now(UTC)
    since = generated_at - timedelta(days=days)

    rows = (
        await session.execute(
            select(ApiUsageEvent)
            .where(ApiUsageEvent.created_at >= since)
            .order_by(desc(ApiUsageEvent.created_at))
        )
    ).scalars().all()

    org_name_map: dict[str, str] = {}
    org_ids = {
        str(meta.get("org_id"))
        for row in rows
        for meta in [row.metadata_json if isinstance(row.metadata_json, dict) else {}]
        if meta.get("org_id")
    }
    parsed_org_ids: list[UUID] = []
    for org_id in org_ids:
        try:
            parsed_org_ids.append(UUID(org_id))
        except (TypeError, ValueError):
            continue
    if parsed_org_ids:
        organizations = (
            await session.execute(select(Organization).where(Organization.id.in_(parsed_org_ids)))
        ).scalars().all()
        org_name_map = {str(org.id): org.name for org in organizations}

    status_counts: dict[str, int] = {}
    gross_totals: dict[str, Decimal] = {}
    provider_cost_totals: dict[str, Decimal] = {}
    margin_totals: dict[str, Decimal] = {}
    endpoint_map: dict[tuple[str, str, str, str | None], dict[str, object]] = {}
    org_map: dict[str, dict[str, object]] = {}

    for row in rows:
        status = str(row.status)
        currency = (row.amount_currency or "ACP").upper()
        gross = Decimal(str(row.amount_value or "0"))
        provider_cost_amount, margin_amount = _usage_cost_snapshot(row)
        metadata = row.metadata_json if isinstance(row.metadata_json, dict) else {}
        org_id = str(metadata.get("org_id")) if metadata.get("org_id") else None

        status_counts[status] = status_counts.get(status, 0) + 1
        gross_totals[currency] = gross_totals.get(currency, Decimal("0")) + gross
        provider_cost_totals[currency] = provider_cost_totals.get(currency, Decimal("0")) + provider_cost_amount
        margin_totals[currency] = margin_totals.get(currency, Decimal("0")) + margin_amount

        endpoint_key = (row.endpoint, row.product_slug, currency, org_id)
        if endpoint_key not in endpoint_map:
            endpoint_map[endpoint_key] = {
                "endpoint": row.endpoint,
                "product_slug": row.product_slug,
                "currency": currency,
                "org_id": org_id,
                "usage_count": 0,
                "captured_count": 0,
                "gross_amount": Decimal("0"),
                "estimated_provider_cost_amount": Decimal("0"),
                "estimated_margin_amount": Decimal("0"),
            }
        endpoint_item = endpoint_map[endpoint_key]
        endpoint_item["usage_count"] = int(endpoint_item["usage_count"]) + 1
        if status == "captured":
            endpoint_item["captured_count"] = int(endpoint_item["captured_count"]) + 1
        endpoint_item["gross_amount"] = Decimal(endpoint_item["gross_amount"]) + gross
        endpoint_item["estimated_provider_cost_amount"] = Decimal(endpoint_item["estimated_provider_cost_amount"]) + provider_cost_amount
        endpoint_item["estimated_margin_amount"] = Decimal(endpoint_item["estimated_margin_amount"]) + margin_amount

        if org_id:
            if org_id not in org_map:
                org_map[org_id] = {
                    "org_id": org_id,
                    "org_name": org_name_map.get(org_id),
                    "usage_count": 0,
                    "captured_count": 0,
                    "gross_totals": {},
                    "estimated_provider_cost_totals": {},
                    "estimated_margin_totals": {},
                }
            org_item = org_map[org_id]
            org_item["usage_count"] = int(org_item["usage_count"]) + 1
            if status == "captured":
                org_item["captured_count"] = int(org_item["captured_count"]) + 1
            gross_bucket = org_item["gross_totals"]
            provider_bucket = org_item["estimated_provider_cost_totals"]
            margin_bucket = org_item["estimated_margin_totals"]
            gross_bucket[currency] = gross_bucket.get(currency, Decimal("0")) + gross
            provider_bucket[currency] = provider_bucket.get(currency, Decimal("0")) + provider_cost_amount
            margin_bucket[currency] = margin_bucket.get(currency, Decimal("0")) + margin_amount

    endpoints = [
        PaidApiRevenueEndpointSummaryPublic(
            endpoint=str(item["endpoint"]),
            product_slug=str(item["product_slug"]),
            currency=str(item["currency"]),
            org_id=str(item["org_id"]) if item["org_id"] else None,
            usage_count=int(item["usage_count"]),
            captured_count=int(item["captured_count"]),
            gross_amount=str(item["gross_amount"]),
            estimated_provider_cost_amount=str(item["estimated_provider_cost_amount"]),
            estimated_margin_amount=str(item["estimated_margin_amount"]),
        )
        for item in sorted(
            endpoint_map.values(),
            key=lambda x: (Decimal(x["gross_amount"]), int(x["usage_count"])),
            reverse=True,
        )
    ]

    organizations = [
        PaidApiRevenueOrganizationSummaryPublic(
            org_id=str(item["org_id"]),
            org_name=str(item["org_name"]) if item["org_name"] else None,
            usage_count=int(item["usage_count"]),
            captured_count=int(item["captured_count"]),
            gross_totals=[PaidApiRevenueMoneyPublic(currency=currency, amount=str(amount)) for currency, amount in item["gross_totals"].items()],
            estimated_provider_cost_totals=[PaidApiRevenueMoneyPublic(currency=currency, amount=str(amount)) for currency, amount in item["estimated_provider_cost_totals"].items()],
            estimated_margin_totals=[PaidApiRevenueMoneyPublic(currency=currency, amount=str(amount)) for currency, amount in item["estimated_margin_totals"].items()],
        )
        for item in sorted(
            org_map.values(),
            key=lambda x: (sum(Decimal(v) for v in x["gross_totals"].values()), int(x["usage_count"])),
            reverse=True,
        )
    ]

    return PaidApiRevenueSummaryPublic(
        generated_at=generated_at,
        since=since,
        window_days=days,
        usage_count=len(rows),
        status_counts=status_counts,
        gross_totals=[PaidApiRevenueMoneyPublic(currency=currency, amount=str(amount)) for currency, amount in gross_totals.items()],
        estimated_provider_cost_totals=[PaidApiRevenueMoneyPublic(currency=currency, amount=str(amount)) for currency, amount in provider_cost_totals.items()],
        estimated_margin_totals=[PaidApiRevenueMoneyPublic(currency=currency, amount=str(amount)) for currency, amount in margin_totals.items()],
        endpoints=endpoints,
        organizations=organizations,
    )


@router.post("/agents/{agent_id}/spend-cap", response_model=PaidApiSpendCapResponse)
async def set_paid_api_spend_cap(
    agent_id: str,
    body: PaidApiSpendCapRequest,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    try:
        parsed_agent_id = UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agent_id")
    agent = await session.get(Agent, parsed_agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    if str(agent.owner_user_id or "") != user_id:
        raise HTTPException(status_code=403, detail="Forbidden agent")

    metadata = dict(agent.metadata_ or {})
    caps = dict(metadata.get("paid_api_spend_caps") or {})
    currency = body.currency.upper()
    if body.monthly_cap is None or str(body.monthly_cap).strip() == "":
        caps.pop(currency, None)
    else:
        monthly_cap = Decimal(str(body.monthly_cap)).quantize(Decimal("0.01"))
        if monthly_cap < 0:
            raise HTTPException(status_code=400, detail="monthly_cap must be positive")
        caps[currency] = str(monthly_cap)
    metadata["paid_api_spend_caps"] = caps
    agent.metadata_ = metadata
    flag_modified(agent, "metadata_")
    await session.flush()
    normalized_caps = {str(k).upper(): str(v) for k, v in caps.items()}
    return PaidApiSpendCapResponse(
        agent_id=str(agent.id),
        caps=normalized_caps,
        current_30d_spend=await _current_spend_map(session, parsed_agent_id, normalized_caps),
    )


async def _run_paid_api_product(
    product_slug: str,
    body: PaidApiAnalyzeRequest,
    session: DbSession,
    x_api_key: str | None,
    idempotency_key: str | None,
) -> PaidApiAnalyzeResponse:
    request_payload = body.model_dump(mode="json")
    if idempotency_key:
        hit = await get_idempotency_hit(
            session,
            scope=f"paid_api.{product_slug}",
            key=idempotency_key,
            request_payload=request_payload,
        )
        if hit is not None:
            return PaidApiAnalyzeResponse.model_validate(hit.response_json)

    product = _product(product_slug)
    result = _build_result(product, body)
    usage = await _charge_usage(session, product=product, body=body, raw_api_key=x_api_key)
    usage.response_json = result
    usage.metadata_json = {
        **(usage.metadata_json or {}),
        "result_score": result.get("score"),
        "completed_at": datetime.now(UTC).isoformat(),
    }
    await session.flush()
    await session.refresh(usage)
    usage_public = _serialize_usage(usage)
    response_payload = {
        "product": product.model_dump(mode="json"),
        "usage": usage_public.model_dump(mode="json"),
        "result": result,
        "receipt": {
            "receipt_version": "paid-api-usage/v1",
            "product_slug": product.slug,
            "endpoint": product.endpoint,
            "amount": usage_public.amount.model_dump(),
            "request_hash": usage.request_hash,
            "ledger_event_id": str(usage.ledger_event_id) if usage.ledger_event_id else None,
            "x402": product.x402,
        },
    }
    if idempotency_key:
        await store_idempotency_result(
            session,
            scope=f"paid_api.{product_slug}",
            key=idempotency_key,
            request_payload=request_payload,
            status_code=200,
            response_json=response_payload,
        )
    return PaidApiAnalyzeResponse.model_validate(response_payload)


@router.post("/token-risk", response_model=PaidApiAnalyzeResponse)
async def token_risk_snapshot(
    body: PaidApiAnalyzeRequest,
    session: DbSession,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    return await _run_paid_api_product("token-risk", body, session, x_api_key, idempotency_key)


@router.post("/listing-readiness", response_model=PaidApiAnalyzeResponse)
async def listing_readiness_score(
    body: PaidApiAnalyzeRequest,
    session: DbSession,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    return await _run_paid_api_product("listing-readiness", body, session, x_api_key, idempotency_key)


@router.post("/wallet-risk", response_model=PaidApiAnalyzeResponse)
async def wallet_risk_snapshot(
    body: PaidApiAnalyzeRequest,
    session: DbSession,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    return await _run_paid_api_product("wallet-risk", body, session, x_api_key, idempotency_key)


@router.post("/bridge-proof", response_model=PaidApiAnalyzeResponse)
async def bridge_proof_check(
    body: PaidApiAnalyzeRequest,
    session: DbSession,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    return await _run_paid_api_product("bridge-proof", body, session, x_api_key, idempotency_key)


@router.post("/campaign-score", response_model=PaidApiAnalyzeResponse)
async def campaign_score(
    body: PaidApiAnalyzeRequest,
    session: DbSession,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    return await _run_paid_api_product("campaign-score", body, session, x_api_key, idempotency_key)


# --- Hardened paid API gateway (challenge / settle / consume) ---

import secrets as _secrets
from pydantic import BaseModel, Field


class PaidApiChallengeResponse(BaseModel):
    challenge_id: str
    nonce: str
    product_slug: str
    amount: str
    currency: str
    expires_at: str
    signature_input: str
    signature_algorithm: str = "hmac-sha256"


class PaidApiSettleRequest(BaseModel):
    challenge_id: str
    nonce: str
    product_slug: str
    signature: str = Field(pattern=r"^[0-9a-f]{64}$")


class PaidApiConsumeRequest(BaseModel):
    settle_id: str
    request: PaidApiAnalyzeRequest


_paid_api_challenges: dict[str, dict] = {}
_paid_api_settlements: dict[str, dict] = {}


def _challenge_signature(secret: str, challenge_id: str, nonce: str, product_slug: str, amount: str) -> str:
    payload = f"{challenge_id}:{nonce}:{product_slug}:{amount}"
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


@router.get("/challenge", response_model=PaidApiChallengeResponse)
async def paid_api_challenge(
    session: DbSession,
    product_slug: str = Query(..., min_length=2),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    product = _product(product_slug)
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key required")
    key_record = await resolve_key_record(session, raw_key=x_api_key)
    if key_record is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    challenge_id = _secrets.token_urlsafe(16)
    nonce = _secrets.token_hex(16)
    expires_at = datetime.now(UTC) + timedelta(seconds=180)
    amount = str(product.price.amount)
    currency = product.price.currency
    signature_input = f"{challenge_id}:{nonce}:{product.slug}:{amount}"
    _paid_api_challenges[challenge_id] = {
        "nonce": nonce,
        "product_slug": product.slug,
        "amount": amount,
        "currency": currency,
        "api_key_id": str(key_record.row_id),
        "expires_at": expires_at,
    }
    return PaidApiChallengeResponse(
        challenge_id=challenge_id,
        nonce=nonce,
        product_slug=product.slug,
        amount=amount,
        currency=currency,
        expires_at=expires_at.isoformat(),
        signature_input=signature_input,
    )


@router.post("/settle")
async def paid_api_settle(
    body: PaidApiSettleRequest,
    session: DbSession,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key required")
    key_record = await resolve_key_record(session, raw_key=x_api_key)
    if key_record is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    challenge = _paid_api_challenges.pop(body.challenge_id, None)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found or already used")
    if challenge["nonce"] != body.nonce or challenge["product_slug"] != body.product_slug:
        raise HTTPException(status_code=400, detail="Challenge mismatch")
    if challenge["expires_at"] < datetime.now(UTC):
        raise HTTPException(status_code=410, detail="Challenge expired")
    if str(key_record.row_id) != challenge["api_key_id"]:
        raise HTTPException(status_code=403, detail="API key mismatch")

    expected = _challenge_signature(x_api_key, body.challenge_id, body.nonce, body.product_slug, challenge["amount"])
    if not hmac.compare_digest(body.signature, expected):
        raise HTTPException(status_code=403, detail="Invalid signature")

    settle_id = _secrets.token_urlsafe(18)
    _paid_api_settlements[settle_id] = {
        "product_slug": body.product_slug,
        "api_key": x_api_key,
        "idempotency_key": idempotency_key,
        "expires_at": datetime.now(UTC) + timedelta(seconds=300),
    }
    return {"settle_id": settle_id, "status": "authorized", "product_slug": body.product_slug}


@router.post("/consume", response_model=PaidApiAnalyzeResponse)
async def paid_api_consume(
    body: PaidApiConsumeRequest,
    session: DbSession,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    settlement = _paid_api_settlements.pop(body.settle_id, None)
    if settlement is None:
        raise HTTPException(status_code=404, detail="Settlement not found or already consumed")
    if settlement["expires_at"] < datetime.now(UTC):
        raise HTTPException(status_code=410, detail="Settlement expired")
    if x_api_key != settlement["api_key"]:
        raise HTTPException(status_code=403, detail="API key mismatch")
    return await _run_paid_api_product(
        settlement["product_slug"],
        body.request,
        session,
        x_api_key,
        settlement.get("idempotency_key"),
    )
