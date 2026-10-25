"""Private WeVisOne worker client. OCR output is untrusted payment input."""
from __future__ import annotations

import json
from urllib.parse import urlsplit

import httpx

from app.config import get_settings


async def extract_wevisone_payment_text(*, image_bytes: bytes, media_type: str) -> str:
    settings = get_settings()
    if media_type not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
        raise ValueError("WeVisOne supports photos only; export the payment page as JPEG or PNG")
    if not image_bytes or len(image_bytes) > settings.mobile_smart_pay_max_image_bytes:
        raise ValueError("Invalid Smart Pay image size")
    url = settings.smart_pay_wevisone_url.rstrip("/")
    target = urlsplit(url)
    if (target.scheme not in {"https", "http"} or not target.hostname
            or target.username or target.password or target.query or target.fragment
            or (target.scheme == "http" and target.hostname not in {"127.0.0.1", "localhost", "::1"})):
        raise RuntimeError("Configure a private HTTPS WeVisOne URL (HTTP is loopback-only)")
    if not settings.smart_pay_wevisone_api_key:
        raise RuntimeError("WeVisOne OCR is not configured (SMART_PAY_WEVISONE_API_KEY)")
    # No redirects or implicit fallback to a different document processor.
    async with httpx.AsyncClient(timeout=60, follow_redirects=False) as client:
        async with client.stream(
            "POST", f"{url}/v1/payment-ocr", content=image_bytes,
            headers={"Authorization": f"Bearer {settings.smart_pay_wevisone_api_key}",
                     "Content-Type": media_type},
        ) as response:
            if response.status_code != 200:
                raise RuntimeError("WeVisOne OCR request failed")
            body = bytearray()
            async for chunk in response.aiter_bytes():
                body.extend(chunk)
                if len(body) > 65536:
                    raise RuntimeError("WeVisOne OCR response exceeds limit")
    try:
        payload = json.loads(body)
    except (ValueError, UnicodeDecodeError) as exc:
        raise RuntimeError("Invalid WeVisOne OCR response") from exc
    text = payload.get("text") if isinstance(payload, dict) else None
    if not isinstance(text, str) or len(text) > 32000:
        raise RuntimeError("Invalid WeVisOne OCR text")
    text = text.strip()
    return "" if text.upper() in {"EMPTY", "NONE"} else text
