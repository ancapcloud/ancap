from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import WebhookEndpoint, WebhookDelivery
from app.services.webhook_url_policy import UnsafeWebhookUrl, validate_webhook_url_async


MAX_RETRIES = 3
RETRY_DELAYS = [60, 300, 900]  # seconds: 1m, 5m, 15m
REQUEST_TIMEOUT = 10
# Do not follow redirects — prevents open-redirect SSRF pivots after URL validation.


def sign_webhook_payload(payload: str, secret: str) -> str:
    return "sha256=" + hmac.new(
        secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()


async def dispatch_webhook_event(
    session: AsyncSession,
    endpoint: WebhookEndpoint,
    event_type: str,
    payload: dict[str, Any],
    attempt: int = 1,
) -> dict[str, Any]:
    """Dispatch a single webhook event to an endpoint. Returns delivery result."""
    now = datetime.now(timezone.utc)
    payload_json = {
        "event_type": event_type,
        "payload": payload,
        "delivered_at": now.isoformat(),
        "delivery_id": str(endpoint.id),
    }
    raw = json.dumps(payload_json, default=str)
    signature = sign_webhook_payload(raw, endpoint.secret)

    delivery_record = WebhookDelivery(
        webhook_endpoint_id=endpoint.id,
        event_type=event_type,
        payload_json=payload_json,
        attempt=attempt,
        status="pending",
        created_at=now,
    )
    session.add(delivery_record)
    await session.flush()

    response_status = None
    response_body = None
    try:
        try:
            target = await validate_webhook_url_async(endpoint.url)
        except UnsafeWebhookUrl as exc:
            delivery_record.status = "failed"
            delivery_record.response_body = f"blocked_url:{exc}"[:500]
            await session.commit()
            return {
                "delivery_id": str(delivery_record.id),
                "status": delivery_record.status,
                "response_status": None,
            }

        # Connect to the DNS-pinned IP; keep original hostname for Host + SNI/TLS.
        request_url = target.pinned_request_url()
        headers = {
            "Content-Type": "application/json",
            "Host": target.hostname,
            "X-ANCAP-Signature": signature,
            "X-ANCAP-Event": event_type,
            "X-ANCAP-Webhook-ID": str(endpoint.id),
        }
        extensions = {"sni_hostname": target.hostname} if target.scheme == "https" else None

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=False) as client:
            resp = await client.post(
                request_url,
                content=raw,
                headers=headers,
                extensions=extensions,
            )
            response_status = resp.status_code
            response_body = resp.text[:2000]

        if 200 <= response_status < 300:
            delivery_record.status = "delivered"
            delivery_record.response_status = response_status
            delivery_record.response_body = response_body
            delivery_record.delivered_at = datetime.now(timezone.utc)
        else:
            delivery_record.status = "failed"
            delivery_record.response_status = response_status
            delivery_record.response_body = response_body
            if attempt < MAX_RETRIES:
                delivery_record.next_retry_at = datetime.now(timezone.utc) + timedelta(
                    seconds=RETRY_DELAYS[attempt - 1]
                )
    except httpx.TimeoutException:
        delivery_record.status = "failed"
        delivery_record.response_body = "timeout"
        delivery_record.next_retry_at = datetime.now(timezone.utc) + timedelta(
            seconds=RETRY_DELAYS[attempt - 1]
        ) if attempt < MAX_RETRIES else None
    except Exception as exc:
        delivery_record.status = "failed"
        delivery_record.response_body = str(exc)[:500]
        delivery_record.next_retry_at = datetime.now(timezone.utc) + timedelta(
            seconds=RETRY_DELAYS[attempt - 1]
        ) if attempt < MAX_RETRIES else None

    await session.commit()
    return {
        "delivery_id": str(delivery_record.id),
        "status": delivery_record.status,
        "response_status": response_status,
    }


async def dispatch_event_to_owner_subscribers(
    session: AsyncSession,
    *,
    owner_user_id: str | UUID,
    event_type: str,
    payload: dict[str, Any],
) -> dict[str, int]:
    """Dispatch only to webhook endpoints owned by the given user."""
    owner_id = str(owner_user_id)
    q = select(WebhookEndpoint).where(
        WebhookEndpoint.is_active == True,
        WebhookEndpoint.owner_user_id == owner_id,
    )
    r = await session.execute(q)
    endpoints = list(r.scalars().all())
    subscribed = [ep for ep in endpoints if ep.event_types and event_type in ep.event_types]
    results = {"dispatched": 0, "failed": 0}
    for ep in subscribed:
        try:
            result = await dispatch_webhook_event(session, ep, event_type, payload)
            if result["status"] == "delivered":
                results["dispatched"] += 1
            else:
                results["failed"] += 1
        except Exception:
            results["failed"] += 1
    return results


async def dispatch_event_to_subscribers(
    session: AsyncSession,
    event_type: str,
    payload: dict[str, Any],
    *,
    owner_user_id: str | UUID | None = None,
) -> dict[str, int]:
    """Find active endpoints subscribed to event_type and dispatch to each.

    When owner_user_id is set, only that user's endpoints receive the event.
    """
    q = select(WebhookEndpoint).where(
        WebhookEndpoint.is_active == True,
    )
    if owner_user_id is not None:
        q = q.where(WebhookEndpoint.owner_user_id == str(owner_user_id))
    r = await session.execute(q)
    endpoints = list(r.scalars().all())

    subscribed = [
        ep for ep in endpoints
        if ep.event_types and event_type in ep.event_types
    ]

    results = {"dispatched": 0, "failed": 0}
    for ep in subscribed:
        try:
            result = await dispatch_webhook_event(session, ep, event_type, payload)
            if result["status"] == "delivered":
                results["dispatched"] += 1
            else:
                results["failed"] += 1
        except Exception:
            results["failed"] += 1

    return results


async def retry_pending_webhook_deliveries(session: AsyncSession, *, max_items: int = 100) -> dict[str, int]:
    """Retry failed webhook deliveries that are due for retry."""
    now = datetime.now(timezone.utc)
    q = (
        select(WebhookDelivery)
        .where(
            WebhookDelivery.status == "failed",
            WebhookDelivery.next_retry_at <= now,
        )
        .order_by(WebhookDelivery.created_at)
        .limit(max_items)
    )
    r = await session.execute(q)
    deliveries: list[WebhookDelivery] = list(r.scalars().all())

    retried = 0
    for delivery in deliveries:
        endpoint_q = select(WebhookEndpoint).where(WebhookEndpoint.id == delivery.webhook_endpoint_id)
        endpoint_r = await session.execute(endpoint_q)
        endpoint = endpoint_r.scalar_one_or_none()
        if endpoint is None or not endpoint.is_active:
            delivery.status = "failed"
            delivery.response_body = "endpoint_not_found"
            continue

        result = await dispatch_webhook_event(
            session,
            endpoint,
            delivery.event_type,
            dict(delivery.payload_json) if delivery.payload_json else {},
            attempt=delivery.attempt + 1,
        )
        if result["status"] == "delivered":
            retried += 1

    await session.commit()
    return {"retried": retried, "total": len(deliveries)}


# Convenience helpers for triggering events from business logic.
# Always owner-scoped — never fan out user events to every subscriber.
async def emit_run_completed(session: AsyncSession, run_id: str, title: str, user_id: str) -> dict[str, int]:
    return await dispatch_event_to_owner_subscribers(
        session,
        owner_user_id=user_id,
        event_type="run.completed",
        payload={"run_id": run_id, "title": title, "user_id": user_id},
    )


async def emit_payment_captured(
    session: AsyncSession,
    payment_id: str,
    amount: str,
    currency: str,
    run_id: str,
    *,
    owner_user_id: str,
) -> dict[str, int]:
    return await dispatch_event_to_owner_subscribers(
        session,
        owner_user_id=owner_user_id,
        event_type="payment.captured",
        payload={
            "payment_id": payment_id,
            "amount": amount,
            "currency": currency,
            "run_id": run_id,
            "user_id": owner_user_id,
        },
    )


async def emit_payment_refunded(
    session: AsyncSession,
    payment_id: str,
    amount: str,
    currency: str,
    reason: str,
    *,
    owner_user_id: str,
) -> dict[str, int]:
    return await dispatch_event_to_owner_subscribers(
        session,
        owner_user_id=owner_user_id,
        event_type="payment.refunded",
        payload={
            "payment_id": payment_id,
            "amount": amount,
            "currency": currency,
            "reason": reason,
            "user_id": owner_user_id,
        },
    )


async def emit_receipt_ready(
    session: AsyncSession,
    run_id: str,
    receipt_url: str,
    *,
    owner_user_id: str,
) -> dict[str, int]:
    return await dispatch_event_to_owner_subscribers(
        session,
        owner_user_id=owner_user_id,
        event_type="receipt.ready",
        payload={"run_id": run_id, "receipt_url": receipt_url, "user_id": owner_user_id},
    )


async def emit_api_usage(
    session: AsyncSession,
    usage_id: str,
    agent_id: str,
    product: str,
    amount: str,
    *,
    owner_user_id: str,
) -> dict[str, int]:
    return await dispatch_event_to_owner_subscribers(
        session,
        owner_user_id=owner_user_id,
        event_type="api.usage.created",
        payload={
            "usage_id": usage_id,
            "agent_id": agent_id,
            "product": product,
            "amount": amount,
            "user_id": owner_user_id,
        },
    )


async def emit_user_registered(session: AsyncSession, user_id: str, email: str | None = None) -> dict[str, int]:
    return await dispatch_event_to_owner_subscribers(
        session,
        owner_user_id=user_id,
        event_type="user.registered",
        payload={"user_id": user_id, "email": email},
    )