"""Global rate limiting for the public API surface.

Per-route limits already exist for a handful of expensive endpoints. This
middleware adds one coarse bucket per API key (or client IP) so unauthenticated
floods and a single abusive credential cannot exhaust the process. It is off by
default and enabled explicitly in production (``RATE_LIMIT_ENABLED=true``).
"""

from __future__ import annotations

import hashlib

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import get_settings
from app.services.rate_limit import build_rate_limit_key, check_rate_limit

_SKIP_PATHS = {"/", "/docs", "/redoc", "/openapi.json"}
_SKIP_PREFIXES = (
    "/docs/",
    "/redoc/",
    "/v1/system/health",
    "/v1/system/ready",
    "/v1/metrics",
)


def should_rate_limit_path(path: str) -> bool:
    return path not in _SKIP_PATHS and not path.startswith(_SKIP_PREFIXES)


def request_identity(scope: Scope) -> tuple[str, str | None]:
    """Return (client_ip, api_key_subject) for a request scope."""
    headers = Headers(scope=scope)
    api_key = (headers.get("x-api-key") or "").strip()
    authorization = (headers.get("authorization") or "").strip()
    if not api_key and authorization.lower().startswith("bearer ancap_"):
        api_key = authorization[7:].strip()

    forwarded = headers.get("x-forwarded-for") or headers.get("cf-connecting-ip") or ""
    ip = forwarded.split(",")[0].strip()
    if not ip:
        client = scope.get("client") or ("unknown", 0)
        ip = str(client[0] or "unknown")

    subject = None
    if api_key:
        # Store only a short fingerprint: the limiter must never persist raw keys.
        subject = "key:" + hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]
    return ip, subject


class GlobalRateLimitMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        settings = get_settings()
        path = scope.get("path", "")
        if not settings.rate_limit_enabled or not should_rate_limit_path(path):
            await self.app(scope, receive, send)
            return

        ip, subject = request_identity(scope)
        key = build_rate_limit_key(scope="global", ip=ip, subject=subject)
        allowed = await check_rate_limit(
            key,
            limit=settings.rate_limit_per_minute,
            window_seconds=60,
        )
        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": {
                        "code": "RATE_LIMITED",
                        "message": "Too many requests. Try again later.",
                        "retry_after_seconds": 60,
                    }
                },
                headers={"Retry-After": "60"},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
