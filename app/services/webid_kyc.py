"""WebID KYC partner adapter — fail-closed until commercial credentials exist.

Partner: https://webid-solutions.com/en/
WebID verifies identity (KYC/KYB). It does not issue payment cards or Apple Pay.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
from typing import Any
from urllib.parse import urlencode, urljoin
from uuid import uuid4

import httpx

from app.config import get_settings
from app.schemas.webid import WebIdAdapterStatusPublic, WebIdSessionStartResponse

logger = logging.getLogger(__name__)


class WebIdNotConfigured(RuntimeError):
    """Raised when WEBID_* is incomplete or disabled."""


class WebIdUpstreamError(RuntimeError):
    """Raised when the WebID create-process call fails."""


def webid_is_configured() -> bool:
    settings = get_settings()
    if not bool(settings.webid_enabled):
        return False
    return bool(
        (settings.webid_api_base or "").strip()
        and (settings.webid_client_id or "").strip()
        and (settings.webid_client_secret or "").strip()
    )


def webid_sessions_ready() -> bool:
    """Configured credentials plus a usable create path or light-redirect base."""
    if not webid_is_configured():
        return False
    settings = get_settings()
    return bool(
        (settings.webid_create_path or "").strip()
        or (settings.webid_light_redirect_base or "").strip()
    )


def webid_public_status() -> WebIdAdapterStatusPublic:
    settings = get_settings()
    enabled = bool(settings.webid_enabled)
    configured = webid_is_configured()
    sessions_ready = webid_sessions_ready()
    product = (settings.webid_product or "VideoID").strip() or "VideoID"
    notes: list[str] = [
        "WebID is a KYC/KYB identity partner slot — it does not issue payment cards or enable Apple Pay.",
        "Physical cards and Apple Pay require a separate licensed BaaS/EMI issuer after counsel review.",
        "Partner site: https://webid-solutions.com/en/",
    ]
    if not enabled:
        notes.append("WEBID_ENABLED is false — IDV flows stay off.")
    elif not configured:
        notes.append("WEBID_API_BASE / WEBID_CLIENT_ID / WEBID_CLIENT_SECRET incomplete — fail-closed.")
    elif not sessions_ready:
        notes.append("Credentials present but WEBID_CREATE_PATH / WEBID_LIGHT_REDIRECT_BASE empty.")
    if not (settings.webid_webhook_secret or "").strip():
        notes.append("WEBID_WEBHOOK_SECRET missing — webhook signature checks stay fail-closed.")
    return WebIdAdapterStatusPublic(
        configured=configured,
        enabled=enabled,
        role="kyc_partner_slot",
        issues_cards=False,
        apple_pay_ready=False,
        sessions_ready=sessions_ready,
        webhook_secret_present=bool((settings.webid_webhook_secret or "").strip()),
        product_hint=product,
        notes=notes,
    )


def _auth_header() -> str:
    settings = get_settings()
    raw = f"{(settings.webid_client_id or '').strip()}:{(settings.webid_client_secret or '').strip()}"
    token = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def _safe_log_token(value: Any, *, max_len: int = 64) -> str:
    raw = "" if value is None else str(value)
    cleaned = "".join(ch for ch in raw if ch.isprintable() and ch not in "\r\n\t")
    return cleaned[:max_len]


def _pick_str(payload: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if value is None and "." not in key:
            continue
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    # nested actionId / redirectUrl under common wrappers
    for wrapper in ("data", "result", "identification", "process"):
        nested = payload.get(wrapper)
        if isinstance(nested, dict):
            found = _pick_str(nested, *keys)
            if found:
                return found
    return None


def _build_light_redirect(*, action_id: str, return_url: str, product: str) -> str | None:
    settings = get_settings()
    base = (settings.webid_light_redirect_base or "").strip()
    if not base:
        return None
    query = urlencode(
        {
            "actionId": action_id,
            "returnUrl": return_url,
            "product": product,
        }
    )
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}{query}"


async def start_webid_session(
    *,
    user_id: str,
    return_url: str | None = None,
    product: str | None = None,
    locale: str | None = None,
) -> WebIdSessionStartResponse:
    """Create a WebID identification process (light integration / API). Fail-closed."""
    if not webid_sessions_ready():
        raise WebIdNotConfigured(
            "WebID KYC is not configured. Set WEBID_ENABLED and commercial credentials first."
        )

    settings = get_settings()
    product_name = (product or settings.webid_product or "VideoID").strip() or "VideoID"
    back = (return_url or settings.webid_return_url or "https://ancap.cloud/cards").strip()
    notes = [
        "Identity verification only — WebID does not issue cards or enable Apple Pay.",
        "After success you return to ANCAP; card issuance stays on a separate licensed track.",
    ]

    create_path = (settings.webid_create_path or "").strip()
    api_base = (settings.webid_api_base or "").strip().rstrip("/")
    action_id: str | None = None
    redirect_url: str | None = None

    if create_path and api_base:
        url = urljoin(api_base + "/", create_path.lstrip("/"))
        body = {
            "customerReference": user_id,
            "returnUrl": back,
            "product": product_name,
            "locale": (locale or "en").strip() or "en",
            "callbackUrl": "https://api.ancap.cloud/v1/commerce/webid/webhook",
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    url,
                    json=body,
                    headers={
                        "Authorization": _auth_header(),
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                )
        except httpx.HTTPError as exc:
            logger.warning("webid_create_session transport_error=%s", _safe_log_token(type(exc).__name__))
            raise WebIdUpstreamError("WebID create-process transport failed") from exc

        if response.status_code >= 400:
            logger.warning(
                "webid_create_session http_status=%s",
                response.status_code,
            )
            raise WebIdUpstreamError(f"WebID create-process rejected ({response.status_code})")

        try:
            payload = response.json()
        except ValueError as exc:
            raise WebIdUpstreamError("WebID create-process returned non-JSON") from exc
        if not isinstance(payload, dict):
            raise WebIdUpstreamError("WebID create-process returned unexpected payload")

        action_id = _pick_str(payload, "actionId", "action_id", "id", "processId", "process_id")
        redirect_url = _pick_str(
            payload,
            "redirectUrl",
            "redirect_url",
            "url",
            "identificationUrl",
            "identification_url",
        )
        logger.info(
            "webid_create_session ok action_id=%s has_redirect=%s",
            _safe_log_token(action_id),
            bool(redirect_url),
        )

    if not action_id:
        # Local sandbox placeholder when light-redirect base is set but create-path unused.
        action_id = f"local-{uuid4().hex[:12]}"
        notes.append("Local action id generated — replace with live WebID create-process response in production.")

    if not redirect_url:
        redirect_url = _build_light_redirect(action_id=action_id, return_url=back, product=product_name)

    if not redirect_url:
        raise WebIdUpstreamError(
            "WebID session created without redirect URL. Set WEBID_LIGHT_REDIRECT_BASE or ensure the API returns one."
        )

    return WebIdSessionStartResponse(
        status="ready",
        action_id=action_id,
        redirect_url=redirect_url,
        product=product_name,
        issues_cards=False,
        notes=notes,
    )


def verify_webid_webhook_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """HMAC-SHA256 hex digest of the raw body with WEBID_WEBHOOK_SECRET."""
    settings = get_settings()
    shared = (settings.webid_webhook_secret or "").strip()
    if not shared:
        return False
    provided = (signature_header or "").strip()
    if not provided:
        return False
    # Accept plain hex or sha256=<hex>
    if provided.lower().startswith("sha256="):
        provided = provided.split("=", 1)[1].strip()
    expected = hmac.new(shared.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    try:
        return hmac.compare_digest(expected, provided)
    except Exception:
        return False


def parse_webid_json_body(raw_body: bytes) -> dict[str, Any]:
    if not raw_body:
        return {}
    try:
        data = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def summarize_webid_webhook(payload: dict[str, Any]) -> dict[str, Any]:
    event = _pick_str(payload, "event", "type", "eventType", "event_type")
    action_id = _pick_str(payload, "actionId", "action_id", "id", "processId")
    status = _pick_str(
        payload,
        "status",
        "identificationStatus",
        "identification_status",
        "result",
    )
    meta = {
        "event": event,
        "action_id": action_id,
        "identification_status": status,
    }
    # Hash webhook fields before logging so user-controlled strings cannot inject log lines.
    event_token = _safe_log_token(meta.get("event"))
    action_token = _safe_log_token(meta.get("action_id"))
    status_token = _safe_log_token(meta.get("identification_status"))
    logger.info(
        "webid_webhook event_sha=%s action_sha=%s status_sha=%s",
        hashlib.sha256(event_token.encode("utf-8")).hexdigest()[:16],
        hashlib.sha256(action_token.encode("utf-8")).hexdigest()[:16],
        hashlib.sha256(status_token.encode("utf-8")).hexdigest()[:16],
    )
    return meta
