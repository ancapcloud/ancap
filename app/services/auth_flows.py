from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import PasswordResetToken, User, UserEvmWallet


WALLET_LOCAL_EMAIL_SUFFIX = "@wallet.ancap.local"
from app.services.mail import can_receive_system_email, send_email


RESET_TOKEN_BYTES = 32


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_password_reset(session: AsyncSession, user: User) -> tuple[str, PasswordResetToken]:
    settings = get_settings()
    raw_token = secrets.token_urlsafe(RESET_TOKEN_BYTES)
    token_hash = _hash_token(raw_token)
    expires_at = utc_now() + timedelta(minutes=settings.password_reset_token_ttl_minutes)

    existing = await session.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
    )
    for row in existing.scalars().all():
        row.used_at = utc_now()

    reset = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    session.add(reset)
    await session.flush()
    return raw_token, reset


async def get_password_reset_token(session: AsyncSession, token: str) -> PasswordResetToken:
    token_hash = _hash_token(token)
    result = await session.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    reset = result.scalar_one_or_none()
    if reset is None:
        raise ValueError("Password reset token is invalid")
    if reset.used_at is not None:
        raise ValueError("Password reset token was already used")
    expires_at = reset.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < utc_now():
        raise ValueError("Password reset token expired")
    return reset


def mark_password_reset_token_used(reset: PasswordResetToken) -> None:
    reset.used_at = utc_now()


async def consume_password_reset_token(session: AsyncSession, token: str) -> PasswordResetToken:
    reset = await get_password_reset_token(session, token)
    mark_password_reset_token_used(reset)
    return reset


async def find_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is not None:
        return user
    from sqlalchemy import func

    candidates = (
        await session.execute(select(User).where(func.lower(User.email) == email.lower()).limit(2))
    ).scalars().all()
    return candidates[0] if len(candidates) == 1 else None


async def send_password_reset_email(request: Request, user: User, raw_token: str) -> bool:
    settings = get_settings()
    if not can_receive_system_email(user.email):
        return False

    origin = (settings.public_app_url or "").strip().rstrip("/")
    if not origin:
        forwarded_host = (request.headers.get("x-forwarded-host") or "").split(",")[0].strip()
        host = forwarded_host or (request.headers.get("host") or "ancap.cloud").split(",")[0].strip()
        forwarded_proto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
        scheme = forwarded_proto or (request.url.scheme or "https").strip().lower()
        if scheme not in {"http", "https"}:
            scheme = "https"
        origin = f"{scheme}://{host}"

    reset_url = f"{origin}/reset-password?token={raw_token}"
    subject = "ANCAP password reset"
    text_body = (
        "We received a request to reset your ANCAP password.\n\n"
        f"Open this link to continue: {reset_url}\n\n"
        f"The link expires in {settings.password_reset_token_ttl_minutes} minutes.\n"
        "If you did not request this, you can ignore this email."
    )
    html_body = (
        "<p>We received a request to reset your ANCAP password.</p>"
        f"<p><a href=\"{reset_url}\">Reset password</a></p>"
        f"<p>The link expires in {settings.password_reset_token_ttl_minutes} minutes.</p>"
        "<p>If you did not request this, you can ignore this email.</p>"
    )
    return send_email(to_email=user.email, subject=subject, text_body=text_body, html_body=html_body)


async def send_login_alert(*, user: User, request: Request, via: str) -> bool:
    settings = get_settings()
    if not settings.login_alerts_enabled or not can_receive_system_email(user.email):
        return False

    ip = (
        (request.headers.get("cf-connecting-ip") or "").split(",")[0].strip()
        or (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
        or (request.client.host if request.client else "")
        or "unknown"
    )
    ua = (request.headers.get("user-agent") or "unknown").strip()
    ts = utc_now().strftime("%Y-%m-%d %H:%M:%S UTC")
    subject = f"ANCAP login alert ({via})"
    text_body = (
        "A new login to your ANCAP account was detected.\n\n"
        f"Method: {via}\n"
        f"Time: {ts}\n"
        f"IP: {ip}\n"
        f"User-Agent: {ua}\n\n"
        "If this was not you, change your password immediately."
    )
    html_body = (
        "<p>A new login to your ANCAP account was detected.</p>"
        f"<ul><li><strong>Method:</strong> {via}</li><li><strong>Time:</strong> {ts}</li><li><strong>IP:</strong> {ip}</li><li><strong>User-Agent:</strong> {ua}</li></ul>"
        "<p>If this was not you, change your password immediately.</p>"
    )
    return send_email(to_email=user.email, subject=subject, text_body=text_body, html_body=html_body)


async def link_wallet_to_user(session: AsyncSession, *, user: User, wallet_address: str, chain_id: int | None) -> UserEvmWallet:
    normalized = wallet_address.strip().lower()
    existing = await session.execute(select(UserEvmWallet).where(UserEvmWallet.wallet_address == normalized))
    link = existing.scalar_one_or_none()
    if link is not None and str(link.user_id) != str(user.id):
        existing_user_result = await session.execute(select(User).where(User.id == link.user_id))
        existing_user = existing_user_result.scalar_one_or_none()
        expected_shadow_email = f"{normalized.removeprefix('0x')}{WALLET_LOCAL_EMAIL_SUFFIX}"
        if (
            existing_user is not None
            and (existing_user.email or "").strip().lower() == expected_shadow_email
        ):
            other_refs = await session.execute(
                select(UserEvmWallet).where(UserEvmWallet.user_id == existing_user.id)
            )
            linked_wallets = other_refs.scalars().all()
            if len(linked_wallets) == 1 and linked_wallets[0].wallet_address == normalized:
                link.user_id = user.id
                if chain_id is not None and link.chain_id != chain_id:
                    link.chain_id = chain_id
                await session.flush()
                return link
        raise ValueError("This wallet is already linked to another account")
    if link is None:
        link = UserEvmWallet(user_id=user.id, wallet_address=normalized, chain_id=chain_id)
        session.add(link)
        await session.flush()
    elif chain_id is not None and link.chain_id != chain_id:
        link.chain_id = chain_id
    return link
