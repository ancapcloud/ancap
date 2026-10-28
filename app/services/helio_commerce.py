"""MoonPay Commerce (Helio) adapter — keys stay in env; never log secrets."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any

from app.config import get_settings
from app.schemas.helio import HelioAdapterStatusPublic

logger = logging.getLogger(__name__)

DEFAULT_AMOUNT = "10"
DEFAULT_NETWORK = "main"
DEFAULT_PRIMARY_PAYMENT_METHOD = "fiat"


def helio_is_configured() -> bool:
    settings = get_settings()
    return bool(
        (settings.helio_public_key or "").strip()
        and (settings.helio_secret_key or "").strip()
        and (settings.helio_paylink_id or "").strip()
    )


def helio_public_status() -> HelioAdapterStatusPublic:
    settings = get_settings()
    paylink_id = (settings.helio_paylink_id or "").strip() or None
    network = (settings.helio_network or DEFAULT_NETWORK).strip() or DEFAULT_NETWORK
    primary = (settings.helio_primary_payment_method or DEFAULT_PRIMARY_PAYMENT_METHOD).strip() or DEFAULT_PRIMARY_PAYMENT_METHOD
    amount = (settings.helio_default_amount or DEFAULT_AMOUNT).strip() or DEFAULT_AMOUNT
    notes: list[str] = []
    if not (settings.helio_public_key or "").strip() or not (settings.helio_secret_key or "").strip():
        notes.append("HELIO_PUBLIC_KEY / HELIO_SECRET_KEY missing on host")
    if not paylink_id:
        notes.append("HELIO_PAYLINK_ID missing — create a Pay Link on moonpay.hel.io")
    if not (settings.helio_webhook_shared_token or "").strip():
        notes.append("HELIO_WEBHOOK_SHARED_TOKEN missing — webhook signature checks stay fail-closed")
    notes.append("Checkout settles via MoonPay Commerce; ACP ledger credit remains desk/operator after webhook.")
    return HelioAdapterStatusPublic(
        configured=helio_is_configured(),
        paylink_configured=bool(paylink_id),
        webhook_secret_present=bool((settings.helio_webhook_shared_token or "").strip()),
        network=network,
        paylink_id=paylink_id if helio_is_configured() else None,
        primary_payment_method=primary,
        default_amount=amount,
        currency_hint=(settings.helio_currency_hint or "USDC").strip() or "USDC",
        notes=notes,
    )


def verify_helio_webhook_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """HMAC-SHA256 hex digest of the raw JSON body with the webhook sharedToken."""
    settings = get_settings()
    shared = (settings.helio_webhook_shared_token or "").strip()
    if not shared:
        return False
    provided = (signature_header or "").strip()
    if not provided:
        return False
    expected = hmac.new(shared.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    try:
        return hmac.compare_digest(expected, provided)
    except Exception:
        return False


def _safe_log_token(value: Any, *, max_len: int = 64) -> str:
    """Strip control chars so webhook fields cannot inject multiline log entries."""
    raw = "" if value is None else str(value)
    cleaned = "".join(ch for ch in raw if ch.isprintable() and ch not in "\r\n\t")
    return cleaned[:max_len]


def summarize_helio_webhook(payload: dict[str, Any]) -> dict[str, Any]:
    event = payload.get("event")
    tx = payload.get("transactionObject") or payload.get("transaction") or {}
    meta = {
        "event": str(event) if event is not None else None,
        "transaction_id": str(tx.get("id") or "") or None,
        "paylink_id": str(
            (tx.get("paylinkId") or tx.get("paylink") or payload.get("paylinkId") or "")
        )
        or None,
        "status": str(tx.get("status") or "") or None,
    }
    logger.info(
        "helio_webhook event=%r transaction_id=%r paylink_id=%r status=%r",
        _safe_log_token(meta.get("event")),
        _safe_log_token(meta.get("transaction_id")),
        _safe_log_token(meta.get("paylink_id")),
        _safe_log_token(meta.get("status")),
    )
    return meta


def parse_helio_json_body(raw_body: bytes) -> dict[str, Any]:
    if not raw_body:
        return {}
    try:
        data = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}
