"""Instantly.ai API v2 client — email accounts (Custom IMAP/SMTP).

Docs: https://developer.instantly.ai/
Base: https://api.instantly.ai/api/v2
Auth: Authorization: Bearer <API_KEY>
Custom IMAP/SMTP provider_code = 1
"""
from __future__ import annotations
from app.services.recoverable_errors import report_optional_failure

from typing import Any

import httpx
from fastapi import HTTPException

from app.config import get_settings

# Instantly provider codes (Create Account)
PROVIDER_CUSTOM_IMAP_SMTP = 1
PROVIDER_GOOGLE = 2
PROVIDER_MICROSOFT = 3


def configured() -> bool:
    settings = get_settings()
    return bool(settings.instantly_enabled and (settings.instantly_api_key or "").strip())


def _headers() -> dict[str, str]:
    settings = get_settings()
    key = (settings.instantly_api_key or "").strip()
    if not key:
        raise HTTPException(status_code=503, detail="Instantly API key not configured")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _base() -> str:
    settings = get_settings()
    return (settings.instantly_api_base or "https://api.instantly.ai/api/v2").rstrip("/")


async def _request(method: str, path: str, *, json: dict[str, Any] | None = None) -> Any:
    settings = get_settings()
    if not settings.instantly_enabled:
        raise HTTPException(status_code=503, detail="Instantly integration disabled")
    url = f"{_base()}{path}"
    timeout = max(int(settings.instantly_timeout_seconds), 5)
    async with httpx.AsyncClient(timeout=timeout) as client:
        res = await client.request(method, url, headers=_headers(), json=json)
    if res.status_code == 401:
        raise HTTPException(status_code=502, detail="Instantly unauthorized — check INSTANTLY_API_KEY")
    if res.status_code == 403:
        raise HTTPException(status_code=502, detail="Instantly forbidden — missing API scope")
    if res.status_code == 429:
        raise HTTPException(status_code=429, detail="Instantly rate limit exceeded")
    if res.status_code >= 400:
        detail = res.text[:400]
        try:
            payload = res.json()
            detail = str(payload.get("message") or payload.get("error") or payload.get("detail") or detail)
        except Exception:
            report_optional_failure('app.services.instantly:_request:res.json', quiet=False)
        raise HTTPException(status_code=502, detail=f"Instantly error {res.status_code}: {detail}")
    if res.status_code == 204 or not res.content:
        return None
    return res.json()


def status_public() -> dict[str, Any]:
    settings = get_settings()
    return {
        "enabled": bool(settings.instantly_enabled),
        "configured": configured(),
        "api_base": _base(),
        "provider_custom_imap_smtp": PROVIDER_CUSTOM_IMAP_SMTP,
        "docs": "https://developer.instantly.ai/",
        "ancap_docs": "/docs/INSTANTLY_API.md",
        "endpoints": {
            "status": "GET /v1/mail/instantly/status",
            "list_accounts": "GET /v1/mail/instantly/accounts",
            "create_account": "POST /v1/mail/instantly/accounts",
            "connect_local": "POST /v1/mail/accounts",
            "openapi": "https://api.ancap.cloud/docs",
        },
        "note": (
            "Create a V2 API key in Instantly > Settings > Integrations > API Keys "
            "with accounts scopes, then set GitHub secret INSTANTLY_API_KEY (or host INSTANTLY_* env)."
        ),
    }


async def list_accounts(*, limit: int = 20) -> Any:
    limit = max(1, min(int(limit), 100))
    return await _request("GET", f"/accounts?limit={limit}")


async def create_custom_imap_account(
    *,
    email: str,
    first_name: str,
    last_name: str,
    imap_username: str,
    imap_password: str,
    imap_host: str,
    imap_port: int,
    smtp_username: str,
    smtp_password: str,
    smtp_host: str,
    smtp_port: int,
) -> Any:
    """POST /api/v2/accounts with provider_code=1 (Custom IMAP/SMTP)."""
    body = {
        "email": email.strip(),
        "first_name": (first_name or "ANCAP").strip() or "ANCAP",
        "last_name": (last_name or "Mail").strip() or "Mail",
        "provider_code": PROVIDER_CUSTOM_IMAP_SMTP,
        "imap_username": imap_username.strip(),
        "imap_password": imap_password,
        "imap_host": imap_host.strip(),
        "imap_port": int(imap_port),
        "smtp_username": smtp_username.strip(),
        "smtp_password": smtp_password,
        "smtp_host": smtp_host.strip(),
        "smtp_port": int(smtp_port),
    }
    return await _request("POST", "/accounts", json=body)


async def get_account(email: str) -> Any:
    from urllib.parse import quote

    return await _request("GET", f"/accounts/{quote(email.strip(), safe='')}")


async def test_account_vitals(emails: list[str]) -> Any:
    return await _request("POST", "/accounts/test/vitals", json={"accounts": emails})
