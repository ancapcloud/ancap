"""Shared dependencies."""
from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db
from app.services.auth import decode_token
from app.services.api_keys import resolve_key, resolve_key_record

security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_db)],
    cookie_token: Annotated[str | None, Cookie(alias="ancap_token")] = None,
    x_requested_with: Annotated[str | None, Header(alias="X-Requested-With")] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> str | None:
    """Resolve user_id from an account API key, user JWT or HttpOnly cookie.

    For cookie-authenticated unsafe methods, require the frontend's same-origin
    X-Requested-With header so cross-site form posts cannot ride the session cookie.
    Bearer-token API clients are unaffected.
    """
    header_token = credentials.credentials if credentials else None
    if x_api_key is not None or (header_token and header_token.startswith("ancap_")):
        resolved = await resolve_key_record(session, x_api_key if x_api_key is not None else header_token)
        if resolved is not None and resolved.owner_user_id is not None:
            if header_token and not header_token.startswith("ancap_") and decode_token(header_token) != str(resolved.owner_user_id):
                return None
            request.state.user_id = str(resolved.owner_user_id)
            return str(resolved.owner_user_id)
        if resolved is not None and header_token and not header_token.startswith("ancap_"):
            # Existing clients may supply both their user JWT and an agent key.
            return decode_token(header_token)
        # Legacy agent/org keys keep their existing scopes, not user privileges.
        # An explicit invalid key must never fall back to a logged-in cookie.
        return None
    if authorization is not None and not authorization.strip():
        cookie_token = None
    if cookie_token and not header_token and request.method.upper() not in {"GET", "HEAD", "OPTIONS"}:
        if (x_requested_with or "").strip().lower() != "xmlhttprequest":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Missing X-Requested-With header for cookie-authenticated request",
            )

    token = header_token or cookie_token
    if not token:
        return None
    sub = decode_token(token)
    return sub


async def require_auth(
    user_id: Annotated[str | None, Depends(get_current_user_id)],
) -> str:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user_id


DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_agent_id_from_api_key(
    session: Annotated[AsyncSession, Depends(get_db)],
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> str | None:
    """Resolve X-API-Key header to agent_id. Returns None if header missing or invalid."""
    if not x_api_key:
        return None
    agent_id = await resolve_key(session, x_api_key)
    return str(agent_id) if agent_id else None


def require_agent_id(
    agent_id_str: Annotated[str | None, Depends(get_agent_id_from_api_key)],
) -> UUID:
    """Require agent identity (X-API-Key). For use in L3 stakes/onboarding."""
    if not agent_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent identity required (X-API-Key)",
        )
    try:
        return UUID(agent_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid agent")


async def is_platform_admin_user(session: AsyncSession, user_id: str) -> bool:
    """True if user_id is on the UUID allowlist or their email is on the email allowlist."""
    settings = get_settings()
    allowed_ids = set(settings.platform_admin_user_ids_allowlist)
    allowed_emails = set(settings.platform_admin_emails_allowlist)
    if not allowed_ids and not allowed_emails:
        return False
    if user_id in allowed_ids:
        return True
    if not allowed_emails:
        return False
    from sqlalchemy import select

    from app.db.models import User

    row = await session.execute(select(User.email).where(User.id == user_id))
    email = row.scalar_one_or_none()
    return bool(email and email.strip().lower() in allowed_emails)


async def require_platform_admin(
    user_id: Annotated[str, Depends(require_auth)],
    session: DbSession,
) -> str:
    """Require a platform operator account for admin-only actions.

    Production must configure PLATFORM_ADMIN_USER_IDS and/or PLATFORM_ADMIN_EMAILS.
    If both allowlists are empty, fail closed.
    """
    settings = get_settings()
    allowed_ids = set(settings.platform_admin_user_ids_allowlist)
    allowed_emails = set(settings.platform_admin_emails_allowlist)
    if not allowed_ids and not allowed_emails:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Platform admin access is not configured",
        )
    if await is_platform_admin_user(session, user_id):
        return user_id
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform admin required")


async def require_admin(
    user_id: Annotated[str, Depends(require_platform_admin)],
) -> str:
    """Compatibility name for the fail-closed platform admin dependency."""
    return user_id
