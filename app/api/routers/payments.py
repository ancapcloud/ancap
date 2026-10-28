from __future__ import annotations
from app.services.recoverable_errors import report_optional_failure

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api.deps import DbSession, require_auth, require_platform_admin
from app.api.routers.workflow_store import _capture_credit_top_up_intent, _package_for_top_up_intent, _serialize_payment_intent
from app.config import get_settings
from app.constants import PLATFORM_ACCOUNT_OWNER_ID
from app.db.models import PaymentIntent, PaymentIntentStatusEnum, RefundRequest, RefundRequestStatusEnum, StripeEvent
from app.schemas import (
    PaymentMethodsResponse,
    RefundRequestActionRequest,
    RefundRequestCreateRequest,
    RefundRequestPublic,
    RefundRequestsResponse,
    StripeIntentCreateRequest,
    StripeIntentCreateResponse,
    StripeAdapterStatusPublic,
    StripeWebhookAck,
    WorkflowCreditTopUpIntentConfirmRequest,
    WorkflowCreditTopUpIntentResponse,
)
from app.schemas.common import Money
from app.services import stripe_payments
from app.services.idempotency import get_idempotency_hit, store_idempotency_result
from app.services.ledger import append_event, balance_for_account, get_or_create_account
from app.services.webhook_dispatcher import emit_payment_refunded
from app.db.models import LedgerEventTypeEnum

router = APIRouter(tags=["Payments"])


def _serialize_refund_request(row: RefundRequest) -> RefundRequestPublic:
    return RefundRequestPublic(
        id=str(row.id),
        payment_intent_id=str(row.payment_intent_id),
        user_id=str(row.user_id),
        amount=Money(amount=str(row.amount_value), currency=row.amount_currency),
        reason=row.reason,
        status=row.status,
        admin_notes=row.admin_notes,
        refund_ledger_event_id=str(row.refund_ledger_event_id) if row.refund_ledger_event_id else None,
        created_at=row.created_at,
        updated_at=row.updated_at,
        processed_at=row.processed_at,
    )


async def _get_owned_captured_payment_intent(session: DbSession, user_id: str, intent_id: str) -> PaymentIntent:
    intent = await _get_owned_payment_intent(session, user_id, intent_id)
    if intent.intent_type == "workflow_run":
        if not intent.workflow_run_id:
            raise HTTPException(status_code=409, detail="Refund requests currently support captured workflow payments only")
    elif intent.intent_type == "credit_topup":
        pass
    else:
        raise HTTPException(
            status_code=409,
            detail="Refund requests currently support captured workflow or credit-top-up payments only",
        )
    if intent.status != PaymentIntentStatusEnum.captured.value:
        raise HTTPException(status_code=409, detail="Refund requests require a captured payment intent")
    if not intent.capture_ledger_event_id:
        raise HTTPException(status_code=409, detail="Captured payment intent is missing settlement evidence")
    return intent


def _refund_money_for_intent(intent: PaymentIntent) -> tuple[str, Decimal]:
    """Return (currency, amount) to settle on refund approval.

    Workflow refunds restore the charged currency to the user.
    Credit top-ups credited ACP packages — claw the package credit, not fiat sticker.
    """
    if intent.intent_type == "credit_topup":
        package = _package_for_top_up_intent(intent)
        return package.credit_amount.currency, Decimal(package.credit_amount.amount)
    return intent.amount_currency, Decimal(intent.amount_value)


@router.post("/payments/refund-request", response_model=RefundRequestPublic, status_code=201)
async def create_refund_request(
    body: RefundRequestCreateRequest,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    intent = await _get_owned_captured_payment_intent(session, user_id, body.payment_intent_id)

    duplicate = (
        await session.execute(
            select(RefundRequest)
            .where(
                RefundRequest.payment_intent_id == intent.id,
                RefundRequest.user_id == UUID(user_id),
                RefundRequest.status == RefundRequestStatusEnum.pending.value,
            )
            .order_by(RefundRequest.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="Refund request is already pending for this payment intent")

    refund_currency, refund_amount = _refund_money_for_intent(intent)
    row = RefundRequest(
        payment_intent_id=intent.id,
        user_id=UUID(user_id),
        amount_currency=refund_currency,
        amount_value=refund_amount,
        reason=body.reason.strip(),
        status=RefundRequestStatusEnum.pending.value,
    )
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return _serialize_refund_request(row)


@router.get("/payments/my-refund-requests", response_model=RefundRequestsResponse)
async def list_my_refund_requests(
    session: DbSession,
    user_id: str = Depends(require_auth),
    status_filter: str | None = Query(default=None, alias="status"),
    payment_intent_id: str | None = Query(default=None),
):
    query = select(RefundRequest).where(RefundRequest.user_id == UUID(user_id)).order_by(RefundRequest.created_at.desc())
    if status_filter:
        normalized = status_filter.strip().lower()
        allowed = {item.value for item in RefundRequestStatusEnum}
        if normalized not in allowed:
            raise HTTPException(status_code=400, detail="Unsupported refund request status filter")
        query = query.where(RefundRequest.status == normalized)
    if payment_intent_id:
        intent = await _get_owned_payment_intent(session, user_id, payment_intent_id)
        query = query.where(RefundRequest.payment_intent_id == intent.id)
    rows = (await session.execute(query)).scalars().all()
    return RefundRequestsResponse(items=[_serialize_refund_request(row) for row in rows])


@router.get("/payments/refund-requests", response_model=RefundRequestsResponse)
async def list_refund_requests(
    session: DbSession,
    _admin_user_id: str = Depends(require_platform_admin),
    status_filter: str | None = Query(default=None, alias="status"),
):
    query = select(RefundRequest).order_by(RefundRequest.created_at.desc())
    if status_filter:
        normalized = status_filter.strip().lower()
        allowed = {item.value for item in RefundRequestStatusEnum}
        if normalized not in allowed:
            raise HTTPException(status_code=400, detail="Unsupported refund request status filter")
        query = query.where(RefundRequest.status == normalized)
    rows = (await session.execute(query)).scalars().all()
    return RefundRequestsResponse(items=[_serialize_refund_request(row) for row in rows])


@router.post("/admin/refund-requests/{refund_request_id}/approve", response_model=RefundRequestPublic)
async def approve_refund_request(
    refund_request_id: str,
    body: RefundRequestActionRequest,
    session: DbSession,
    admin_user_id: str = Depends(require_platform_admin),
):
    try:
        refund_uuid = UUID(refund_request_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Refund request not found") from exc

    row = await session.get(RefundRequest, refund_uuid)
    if row is None:
        raise HTTPException(status_code=404, detail="Refund request not found")
    if row.status != RefundRequestStatusEnum.pending.value:
        raise HTTPException(status_code=409, detail=f"Refund request is already {row.status}")

    intent = await session.get(PaymentIntent, row.payment_intent_id)
    if intent is None:
        raise HTTPException(status_code=404, detail="Payment intent not found")
    if intent.status != PaymentIntentStatusEnum.captured.value:
        raise HTTPException(status_code=409, detail="Payment intent is not refundable")
    if intent.refund_ledger_event_id:
        raise HTTPException(status_code=409, detail="Payment intent is already refunded")

    if intent.payment_method == "stripe":
        raise HTTPException(
            status_code=409,
            detail="Stripe refund approval is unavailable: provider-confirmed reconciliation is not implemented",
        )

    user_acc = await get_or_create_account(session, "user", UUID(str(row.user_id)))
    platform_acc = await get_or_create_account(session, "system", PLATFORM_ACCOUNT_OWNER_ID)
    if intent.intent_type == "credit_topup":
        # Claw back the ACP package that was credited on capture — never mint fiat.
        balances = await balance_for_account(session, user_acc.id, row.amount_currency)
        available = balances.get(row.amount_currency) or Decimal(0)
        if available < Decimal(row.amount_value):
            raise HTTPException(
                status_code=402,
                detail="Insufficient ACP balance to claw back credit top-up refund",
            )
        refund_event = await append_event(
            session,
            LedgerEventTypeEnum.refund,
            row.amount_currency,
            Decimal(row.amount_value),
            src_account_id=user_acc.id,
            dst_account_id=platform_acc.id,
            metadata={
                "type": "credit_topup_refund_clawback",
                "refund_request_id": str(row.id),
                "payment_intent_id": str(row.payment_intent_id),
                "user_id": str(row.user_id),
                "approved_by": admin_user_id,
                "admin_notes": body.admin_notes,
            },
        )
    else:
        refund_event = await append_event(
            session,
            LedgerEventTypeEnum.refund,
            row.amount_currency,
            Decimal(row.amount_value),
            src_account_id=platform_acc.id,
            dst_account_id=user_acc.id,
            metadata={
                "type": "payment_refund_request_approved",
                "refund_request_id": str(row.id),
                "payment_intent_id": str(row.payment_intent_id),
                "user_id": str(row.user_id),
                "approved_by": admin_user_id,
                "admin_notes": body.admin_notes,
            },
        )
    intent.status = PaymentIntentStatusEnum.refunded.value
    intent.refund_ledger_event_id = refund_event.id
    intent.updated_at = datetime.now(UTC)
    intent.provider_payload_json = {
        **(intent.provider_payload_json or {}),
        "refund_request_id": str(row.id),
        "refund_request_reason": row.reason,
        "refund_approved_by": admin_user_id,
        "refund_admin_notes": body.admin_notes,
        "refund_approved_at": datetime.now(UTC).isoformat(),
    }
    if intent.workflow_run_id:
        from app.api.routers.workflow_store import _set_receipt_payment_intent_proof
        from app.db.models import WorkflowRunRecord

        workflow_run = await session.get(WorkflowRunRecord, intent.workflow_run_id)
        if workflow_run is not None:
            _set_receipt_payment_intent_proof(
                workflow_run,
                intent,
                proof_status="refunded",
                ledger_event_id=str(refund_event.id),
                note=f"Refund request approved: {row.reason}",
            )

    row.status = RefundRequestStatusEnum.approved.value
    row.admin_notes = body.admin_notes
    row.refund_ledger_event_id = refund_event.id
    row.processed_at = datetime.now(UTC)
    row.updated_at = datetime.now(UTC)
    try:
        await emit_payment_refunded(
            session,
            str(intent.id),
            str(intent.amount_value),
            intent.amount_currency,
            "refund_request_approved",
            owner_user_id=str(row.user_id),
        )
    except Exception:
        report_optional_failure('app.api.routers.payments:approve_refund_request:emit_payment_refunded', quiet=False)
    await session.flush()
    await session.refresh(row)
    return _serialize_refund_request(row)


@router.post("/admin/refund-requests/{refund_request_id}/reject", response_model=RefundRequestPublic)
async def reject_refund_request(
    refund_request_id: str,
    body: RefundRequestActionRequest,
    session: DbSession,
    _admin_user_id: str = Depends(require_platform_admin),
):
    try:
        refund_uuid = UUID(refund_request_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Refund request not found") from exc

    row = await session.get(RefundRequest, refund_uuid)
    if row is None:
        raise HTTPException(status_code=404, detail="Refund request not found")
    if row.status != RefundRequestStatusEnum.pending.value:
        raise HTTPException(status_code=409, detail=f"Refund request is already {row.status}")

    row.status = RefundRequestStatusEnum.rejected.value
    row.admin_notes = body.admin_notes
    row.processed_at = datetime.now(UTC)
    row.updated_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(row)
    return _serialize_refund_request(row)


@router.post("/payments/stripe/intent", response_model=StripeIntentCreateResponse, status_code=201)
async def create_stripe_payment_intent(
    body: StripeIntentCreateRequest,
    session: DbSession,
    user_id: str = Depends(require_auth),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    idempotency_scope = "payments.create_stripe_intent"
    request_payload = {"user_id": user_id, **body.model_dump()}
    if idempotency_key:
        hit = await get_idempotency_hit(
            session,
            scope=idempotency_scope,
            key=idempotency_key,
            request_payload=request_payload,
        )
        if hit:
            return JSONResponse(status_code=200, content=hit.response_json)

    user = await stripe_payments.get_user_or_404(session, user_id)
    intent, package, stripe_session = await stripe_payments.create_stripe_credit_topup_intent(session, user, body)
    response = StripeIntentCreateResponse(
        item=_serialize_payment_intent(intent),
        package=package,
        stripe=stripe_session,
    )

    if idempotency_key:
        await store_idempotency_result(
            session,
            scope=idempotency_scope,
            key=idempotency_key,
            request_payload=request_payload,
            status_code=201,
            response_json=response.model_dump(),
        )

    return response


@router.get("/payments/methods", response_model=PaymentMethodsResponse)
async def list_payment_methods(
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    user = await stripe_payments.get_user_or_404(session, user_id)
    return await stripe_payments.list_stripe_payment_methods_for_user(session, user)


@router.delete("/payments/methods/{payment_method_id}", status_code=204)
async def delete_payment_method(
    payment_method_id: str,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    user = await stripe_payments.get_user_or_404(session, user_id)
    await stripe_payments.detach_stripe_payment_method_for_user(session, user, payment_method_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _get_owned_payment_intent(session: DbSession, user_id: str, intent_id: str) -> PaymentIntent:
    try:
        parsed_user_id = UUID(user_id)
        parsed_intent_id = UUID(intent_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Payment intent not found") from exc

    intent = (
        await session.execute(
            select(PaymentIntent)
            .where(
                PaymentIntent.id == parsed_intent_id,
                PaymentIntent.owner_user_id == parsed_user_id,
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if intent is None:
        raise HTTPException(status_code=404, detail="Payment intent not found")
    return intent


@router.get("/payments/stripe/intents/{intent_id}", response_model=WorkflowCreditTopUpIntentResponse)
async def get_stripe_payment_intent(
    intent_id: str,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    intent = await _get_owned_payment_intent(session, user_id, intent_id)
    if intent.intent_type != "credit_topup" or intent.payment_method != "stripe":
        raise HTTPException(status_code=404, detail="Payment intent not found")

    provider_payload = dict(intent.provider_payload_json or {})
    stripe_payment_intent_id = str(intent.stripe_payment_intent_id or "").strip()
    if (
        stripe_payment_intent_id
        and intent.status == PaymentIntentStatusEnum.requires_payment.value
        and stripe_payments.stripe_is_configured()
    ):
        stripe_snapshot = await stripe_payments.fetch_stripe_payment_intent(stripe_payment_intent_id)
        stripe_status = str(stripe_snapshot.get("status") or "").strip()
        latest_payment_method = stripe_snapshot.get("payment_method")
        payment_method_types = [str(item) for item in (stripe_snapshot.get("payment_method_types") or [])]
        provider_payload.update(
            {
                "stripe_status": stripe_status or provider_payload.get("stripe_status") or "requires_payment_method",
                "payment_method_types": payment_method_types or provider_payload.get("payment_method_types") or [],
            }
        )
        if latest_payment_method:
            provider_payload["payment_method_id"] = str(latest_payment_method)
        provider_payload["stripe_last_polled_at"] = datetime.now(UTC).isoformat()
        intent.provider_payload_json = provider_payload
        intent.updated_at = datetime.now(UTC)
        await session.flush()

        if stripe_status == "succeeded":
            await _handle_payment_intent_succeeded(
                session,
                intent,
                stripe_payment_intent_id,
                stripe_status,
                "stripe:poll",
            )
            await session.flush()
        elif stripe_status == "canceled":
            await _handle_payment_intent_terminal_update(
                intent,
                new_status=PaymentIntentStatusEnum.cancelled.value,
                stripe_status=stripe_status,
                event_id="stripe:poll",
                event_type="payment_intent.canceled",
            )
            await session.flush()
        elif stripe_status == "requires_payment_method":
            intent.payment_reference = f"stripe:{stripe_payment_intent_id}"
            await session.flush()

    package = _package_for_top_up_intent(intent)
    return WorkflowCreditTopUpIntentResponse(
        item=_serialize_payment_intent(intent),
        package=package,
        credited=intent.status == PaymentIntentStatusEnum.captured.value,
    )


async def _get_stripe_event_by_provider_id(session: DbSession, stripe_event_id: str) -> StripeEvent | None:
    return (
        await session.execute(
            select(StripeEvent).where(StripeEvent.stripe_event_id == stripe_event_id).limit(1)
        )
    ).scalar_one_or_none()


async def _get_payment_intent_by_stripe_id(session: DbSession, stripe_payment_intent_id: str) -> PaymentIntent | None:
    return (
        await session.execute(
            select(PaymentIntent)
            .where(PaymentIntent.stripe_payment_intent_id == stripe_payment_intent_id)
            .limit(1)
        )
    ).scalar_one_or_none()


def _merge_provider_payload(intent: PaymentIntent, **values: object) -> None:
    payload = dict(intent.provider_payload_json or {})
    payload.update({key: value for key, value in values.items() if value is not None})
    intent.provider_payload_json = payload
    intent.updated_at = datetime.now(UTC)


def _stripe_capture_confirmation_note(event_id: str) -> str:
    return "Stripe poll payment confirmation" if event_id == "stripe:poll" else "Stripe webhook payment confirmation"


async def _handle_payment_intent_succeeded(
    session: DbSession,
    intent: PaymentIntent,
    stripe_payment_intent_id: str,
    stripe_status: str,
    event_id: str,
) -> bool:
    _merge_provider_payload(
        intent,
        stripe_status=stripe_status,
        stripe_last_event_id=event_id,
        stripe_last_event_type="payment_intent.succeeded",
        stripe_last_event_at=datetime.now(UTC).isoformat(),
    )
    intent.payment_reference = f"stripe:{stripe_payment_intent_id}"

    if intent.intent_type != "credit_topup":
        return False
    if intent.status == PaymentIntentStatusEnum.captured.value and intent.capture_ledger_event_id:
        return True

    package = _package_for_top_up_intent(intent)
    await _capture_credit_top_up_intent(
        session,
        intent,
        package,
        WorkflowCreditTopUpIntentConfirmRequest(
            payment_reference=f"stripe:{stripe_payment_intent_id}",
            note=_stripe_capture_confirmation_note(event_id),
        ),
        approved_by_user_id=None,
    )
    return True


async def _handle_payment_intent_terminal_update(
    intent: PaymentIntent,
    *,
    new_status: str,
    stripe_status: str,
    event_id: str,
    event_type: str,
) -> bool:
    _merge_provider_payload(
        intent,
        stripe_status=stripe_status,
        stripe_last_event_id=event_id,
        stripe_last_event_type=event_type,
        stripe_last_event_at=datetime.now(UTC).isoformat(),
    )
    if intent.status == PaymentIntentStatusEnum.requires_payment.value:
        intent.status = new_status
        return True
    return False


@router.post("/webhooks/stripe", response_model=StripeWebhookAck)
async def stripe_webhook(
    request: Request,
    session: DbSession,
):
    settings = get_settings()
    webhook_secret = (settings.stripe_webhook_secret or "").strip()
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhook secret is not configured",
        )

    payload = await request.body()
    event = stripe_payments.parse_stripe_webhook_event(
        payload,
        request.headers.get("Stripe-Signature"),
        webhook_secret,
    )

    event_id = str(event.get("id") or "").strip()
    event_type = str(event.get("type") or "").strip()
    if not event_id or not event_type:
        raise HTTPException(status_code=400, detail="Stripe webhook payload is missing id or type")

    existing = await _get_stripe_event_by_provider_id(session, event_id)
    if existing is not None:
        return StripeWebhookAck(
            received=True,
            duplicate=True,
            processed=bool(existing.processed),
            event_id=existing.stripe_event_id,
            event_type=existing.event_type,
        )

    event_row = StripeEvent(
        stripe_event_id=event_id,
        event_type=event_type,
        processed=False,
        payload_json=event,
    )
    session.add(event_row)
    await session.flush()

    handled = False
    data_object = ((event.get("data") or {}).get("object") or {}) if isinstance(event.get("data"), dict) else {}
    stripe_payment_intent_id = str(data_object.get("id") or "").strip()
    stripe_status = str(data_object.get("status") or "").strip() or event_type

    if stripe_payment_intent_id:
        intent = await _get_payment_intent_by_stripe_id(session, stripe_payment_intent_id)
        if intent is not None:
            if event_type == "payment_intent.succeeded":
                handled = await _handle_payment_intent_succeeded(
                    session,
                    intent,
                    stripe_payment_intent_id,
                    stripe_status,
                    event_id,
                )
            elif event_type == "payment_intent.payment_failed":
                handled = await _handle_payment_intent_terminal_update(
                    intent,
                    new_status=PaymentIntentStatusEnum.failed.value,
                    stripe_status=stripe_status,
                    event_id=event_id,
                    event_type=event_type,
                )
            elif event_type == "payment_intent.canceled":
                handled = await _handle_payment_intent_terminal_update(
                    intent,
                    new_status=PaymentIntentStatusEnum.cancelled.value,
                    stripe_status=stripe_status,
                    event_id=event_id,
                    event_type=event_type,
                )

    event_row.processed = True
    event_row.processed_at = datetime.now(UTC)
    await session.flush()

    return StripeWebhookAck(
        received=True,
        duplicate=False,
        processed=handled,
        event_id=event_id,
        event_type=event_type,
    )


@router.get("/payments/stripe/status", response_model=StripeAdapterStatusPublic)
async def stripe_adapter_status():
    """Public adapter status. Booleans only — no secrets."""
    settings = get_settings()
    return StripeAdapterStatusPublic(
        configured=stripe_payments.stripe_is_configured(),
        webhook_secret_present=bool((settings.stripe_webhook_secret or "").strip()),
        currencies=list(stripe_payments.SUPPORTED_STRIPE_CURRENCIES),
    )


@router.get("/payments/stripe/verification-readiness")
async def stripe_verification_readiness(session: DbSession, user_id: str = Depends(require_platform_admin)):
    """Operator surface for Stripe E2E closure checklist (MASTER_ROADMAP §4.1)."""
    settings = get_settings()
    configured = stripe_payments.stripe_is_configured()
    last_event = await session.scalar(
        select(StripeEvent).order_by(StripeEvent.created_at.desc()).limit(1)
    )
    recent_captured = await session.scalar(
        select(PaymentIntent)
        .where(
            PaymentIntent.payment_method == "stripe",
            PaymentIntent.status == PaymentIntentStatusEnum.captured.value,
        )
        .order_by(PaymentIntent.updated_at.desc())
        .limit(1)
    )
    webhook_confirmed = False
    if recent_captured and isinstance(recent_captured.provider_payload_json, dict):
        payload = recent_captured.provider_payload_json
        webhook_confirmed = bool(payload.get("stripe_last_event_id")) and str(
            payload.get("settlement_signal") or ""
        ).lower() == "webhook"
    return {
        "stripe_configured": configured,
        "publishable_key_present": bool((settings.stripe_publishable_key or "").strip()),
        "webhook_secret_present": bool((settings.stripe_webhook_secret or "").strip()),
        "last_stripe_event_id": last_event.stripe_event_id if last_event else None,
        "last_stripe_event_type": last_event.event_type if last_event else None,
        "last_stripe_event_at": last_event.created_at.isoformat() if last_event and last_event.created_at else None,
        "recent_captured_intent_id": str(recent_captured.id) if recent_captured else None,
        "recent_capture_webhook_confirmed": webhook_confirmed,
        "runbook": "/docs/STRIPE_VERIFICATION_RUNBOOK.md",
        "evidence_template": "/docs/STRIPE_VERIFICATION_EVIDENCE_TEMPLATE.md",
        "closure_ready": configured and webhook_confirmed,
    }
