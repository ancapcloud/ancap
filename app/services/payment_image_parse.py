from __future__ import annotations

import base64
import logging
from typing import Final

import httpx

from app.config import get_settings
from app.services.payment_text_parse import PaymentTextParseResult, parse_payment_text

logger = logging.getLogger(__name__)

_ALLOWED_MEDIA_TYPES: Final[frozenset[str]] = frozenset(
    {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
        "image/gif",
    }
)

from app.services.payment_vision_prompt import VISION_PROMPT as _VISION_PROMPT


def normalize_image_media_type(content_type: str | None) -> str | None:
    raw = (content_type or "").split(";", 1)[0].strip().lower()
    if raw == "image/jpg":
        raw = "image/jpeg"
    if raw in _ALLOWED_MEDIA_TYPES:
        return raw
    return None


async def extract_payment_text_from_image(*, image_bytes: bytes, media_type: str) -> str:
    settings = get_settings()
    if settings.smart_pay_vision_provider == "wevisone":
        from app.services.payment_wevisone import extract_wevisone_payment_text

        return await extract_wevisone_payment_text(image_bytes=image_bytes, media_type=media_type)
    if settings.smart_pay_vision_provider != "anthropic":
        raise RuntimeError("Unsupported Smart Pay vision provider")
    if not settings.anthropic_api_key:
        raise RuntimeError("Vision OCR is not configured (ANTHROPIC_API_KEY)")

    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    base_url = settings.anthropic_base_url.rstrip("/")
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{base_url}/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.llm_model,
                "max_tokens": min(1200, settings.llm_max_tokens),
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document" if media_type == "application/pdf" else "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": b64,
                                },
                            },
                            {"type": "text", "text": _VISION_PROMPT},
                        ],
                    }
                ],
            },
        )
        response.raise_for_status()
        payload = response.json()

    parts: list[str] = []
    for item in payload.get("content") or []:
        if isinstance(item, dict) and item.get("type") == "text":
            parts.append(str(item.get("text") or ""))
    text = "\n".join(part for part in parts if part).strip()
    if not text or text.upper() == "EMPTY":
        return ""
    return text


async def parse_payment_image(
    *,
    image_bytes: bytes,
    content_type: str | None,
) -> PaymentTextParseResult:
    settings = get_settings()
    max_bytes = int(settings.mobile_smart_pay_max_image_bytes)
    if len(image_bytes) <= 0:
        raise ValueError("Empty image upload")
    if len(image_bytes) > max_bytes:
        raise ValueError(f"Image exceeds max size of {max_bytes} bytes")

    media_type = normalize_image_media_type(content_type)
    if media_type is None:
        raise ValueError("Unsupported image type; use JPEG, PNG, WebP, or GIF")

    try:
        extracted = await extract_payment_text_from_image(image_bytes=image_bytes, media_type=media_type)
    except httpx.HTTPError as exc:
        logger.warning("payment image vision OCR HTTP failure: %s", type(exc).__name__)
        raise RuntimeError("Vision OCR request failed") from exc

    if not extracted:
        raise ValueError("No payment details readable from this photo")

    parsed = parse_payment_text(extracted, source="ocr")
    notes = list(parsed.parse_notes)
    notes.insert(0, "Extracted from uploaded photo via AI OCR")
    address = parsed.address
    confidence = min(parsed.confidence, 0.82)
    if settings.smart_pay_vision_provider == "wevisone" and parsed.detected_network == "acp" and address:
        from app.services.acp_privacy import valid_acp_address_checksum
        if not valid_acp_address_checksum(address):
            address = None
            confidence = min(confidence, 0.45)
            notes.append("OCR ACP address checksum failed; paste the verified recipient address manually")
    return PaymentTextParseResult(
        detected_network=parsed.detected_network,
        address=address,
        amount=parsed.amount,
        currency=parsed.currency,
        label=parsed.label,
        confidence=confidence,
        parse_notes=notes,
    )
