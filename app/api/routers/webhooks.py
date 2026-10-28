from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, select

from app.api.deps import DbSession, get_current_user_id
from app.db.models import WebhookEndpoint, WebhookDelivery
from app.services.webhook_url_policy import UnsafeWebhookUrl, validate_webhook_url_async


def _dispatch():
    # Lazy import allows tests to monkeypatch webhook_dispatcher before this runs.
    from app.services.webhook_dispatcher import dispatch_webhook_event
    return dispatch_webhook_event


router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class WebhookCreate(BaseModel):
    url: str
    event_types: list[str]
    description: str | None = None


class WebhookPublic(BaseModel):
    id: str
    url: str
    event_types: list[str]
    description: str | None = None
    is_active: bool = True
    created_at: str | None = None


class WebhookDeliveryPublic(BaseModel):
    id: str
    event_type: str
    status: str
    attempt: int
    response_status: int | None = None
    created_at: str | None = None
    delivered_at: str | None = None


def sign_webhook_payload(payload: str, secret: str) -> str:
    return "sha256=" + hmac.new(
        secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    if not signature.startswith("sha256="):
        return False
    return hmac.compare_digest(sign_webhook_payload(payload, secret), signature)


def generate_webhook_secret() -> str:
    return secrets.token_hex(32)


@router.get("", response_model=list[WebhookPublic])
async def list_webhooks(
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    q = (
        select(WebhookEndpoint)
        .where(WebhookEndpoint.owner_user_id == uuid.UUID(user_id))
        .order_by(desc(WebhookEndpoint.created_at))
    )
    r = await session.execute(q)
    return [
        WebhookPublic(
            id=str(w.id),
            url=w.url,
            event_types=list(w.event_types) if w.event_types else [],
            description=w.description,
            is_active=w.is_active,
            created_at=w.created_at.isoformat() if w.created_at else None,
        )
        for w in r.scalars().all()
    ]


@router.post("", response_model=WebhookPublic, status_code=201)
async def create_webhook(
    body: WebhookCreate,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not body.event_types:
        raise HTTPException(status_code=400, detail="At least one event type is required")
    try:
        target = await validate_webhook_url_async(body.url)
        safe_url = target.url
    except UnsafeWebhookUrl as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    endpoint = WebhookEndpoint(
        owner_user_id=uuid.UUID(user_id),
        url=safe_url,
        secret=generate_webhook_secret(),
        event_types=body.event_types,
        description=body.description,
        is_active=True,
    )
    session.add(endpoint)
    await session.commit()
    await session.refresh(endpoint)

    return WebhookPublic(
        id=str(endpoint.id),
        url=endpoint.url,
        event_types=list(endpoint.event_types),
        description=endpoint.description,
        is_active=endpoint.is_active,
        created_at=endpoint.created_at.isoformat() if endpoint.created_at else None,
    )


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    q = select(WebhookEndpoint).where(
        WebhookEndpoint.id == uuid.UUID(webhook_id),
        WebhookEndpoint.owner_user_id == uuid.UUID(user_id),
    )
    r = await session.execute(q)
    endpoint = r.scalar_one_or_none()
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await session.delete(endpoint)
    await session.commit()


@router.get("/{webhook_id}", response_model=WebhookPublic)
async def get_webhook(
    webhook_id: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    q = select(WebhookEndpoint).where(
        WebhookEndpoint.id == uuid.UUID(webhook_id),
        WebhookEndpoint.owner_user_id == uuid.UUID(user_id),
    )
    r = await session.execute(q)
    endpoint = r.scalar_one_or_none()
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return WebhookPublic(
        id=str(endpoint.id),
        url=endpoint.url,
        event_types=list(endpoint.event_types),
        description=endpoint.description,
        is_active=endpoint.is_active,
        created_at=endpoint.created_at.isoformat() if endpoint.created_at else None,
    )


@router.post("/{webhook_id}/rotate-secret", response_model=WebhookPublic)
async def rotate_webhook_secret(
    webhook_id: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    q = select(WebhookEndpoint).where(
        WebhookEndpoint.id == uuid.UUID(webhook_id),
        WebhookEndpoint.owner_user_id == uuid.UUID(user_id),
    )
    r = await session.execute(q)
    endpoint = r.scalar_one_or_none()
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    endpoint.secret = generate_webhook_secret()
    await session.commit()
    await session.refresh(endpoint)
    return WebhookPublic(
        id=str(endpoint.id),
        url=endpoint.url,
        event_types=list(endpoint.event_types),
        description=endpoint.description,
        is_active=endpoint.is_active,
        created_at=endpoint.created_at.isoformat() if endpoint.created_at else None,
    )


@router.get("/{webhook_id}/deliveries", response_model=list[WebhookDeliveryPublic])
async def list_webhook_deliveries(
    webhook_id: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
    limit: int = Query(50, ge=1, le=200),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    endpoint_q = select(WebhookEndpoint).where(
        WebhookEndpoint.id == uuid.UUID(webhook_id),
        WebhookEndpoint.owner_user_id == uuid.UUID(user_id),
    )
    endpoint_r = await session.execute(endpoint_q)
    endpoint = endpoint_r.scalar_one_or_none()
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Webhook not found")

    q = (
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_endpoint_id == endpoint.id)
        .order_by(desc(WebhookDelivery.created_at))
        .limit(limit)
    )
    r = await session.execute(q)
    return [
        WebhookDeliveryPublic(
            id=str(d.id),
            event_type=d.event_type,
            status=d.status,
            attempt=d.attempt,
            response_status=d.response_status,
            created_at=d.created_at.isoformat() if d.created_at else None,
            delivered_at=d.delivered_at.isoformat() if d.delivered_at else None,
        )
        for d in r.scalars().all()
    ]


@router.get("/{webhook_id}/deliveries/{delivery_id}", response_model=WebhookDeliveryPublic)
async def get_webhook_delivery(
    webhook_id: str,
    delivery_id: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify ownership
    endpoint_q = select(WebhookEndpoint).where(
        WebhookEndpoint.id == uuid.UUID(webhook_id),
        WebhookEndpoint.owner_user_id == uuid.UUID(user_id),
    )
    endpoint_r = await session.execute(endpoint_q)
    endpoint = endpoint_r.scalar_one_or_none()
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Webhook not found")

    q = select(WebhookDelivery).where(
        WebhookDelivery.id == uuid.UUID(delivery_id),
        WebhookDelivery.webhook_endpoint_id == endpoint.id,
    )
    r = await session.execute(q)
    delivery = r.scalar_one_or_none()
    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found")

    return WebhookDeliveryPublic(
        id=str(delivery.id),
        event_type=delivery.event_type,
        status=delivery.status,
        attempt=delivery.attempt,
        response_status=delivery.response_status,
        created_at=delivery.created_at.isoformat() if delivery.created_at else None,
        delivered_at=delivery.delivered_at.isoformat() if delivery.delivered_at else None,
    )


@router.post("/{webhook_id}/deliveries/{delivery_id}/replay")
async def replay_webhook_delivery(
    webhook_id: str,
    delivery_id: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    """Replay a webhook delivery (re-send the original payload to the endpoint).

    Creates a new delivery record with attempt=1 and dispatches immediately.
    """
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify ownership
    endpoint_q = select(WebhookEndpoint).where(
        WebhookEndpoint.id == uuid.UUID(webhook_id),
        WebhookEndpoint.owner_user_id == uuid.UUID(user_id),
    )
    endpoint_r = await session.execute(endpoint_q)
    endpoint = endpoint_r.scalar_one_or_none()
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Find original delivery
    delivery_q = select(WebhookDelivery).where(
        WebhookDelivery.id == uuid.UUID(delivery_id),
        WebhookDelivery.webhook_endpoint_id == endpoint.id,
    )
    delivery_r = await session.execute(delivery_q)
    original = delivery_r.scalar_one_or_none()
    if original is None:
        raise HTTPException(status_code=404, detail="Delivery not found")

    result = await _dispatch()(
        session,
        endpoint,
        original.event_type,
        dict(original.payload_json) if original.payload_json else {},
        attempt=1,  # replay always starts at attempt 1
    )
    return result


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    q = select(WebhookEndpoint).where(
        WebhookEndpoint.id == uuid.UUID(webhook_id),
        WebhookEndpoint.owner_user_id == uuid.UUID(user_id),
    )
    r = await session.execute(q)
    endpoint = r.scalar_one_or_none()
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Webhook not found")

    result = await _dispatch()(
        session, endpoint, "webhook.test", {"test": True, "webhook_id": webhook_id}
    )
    return result
