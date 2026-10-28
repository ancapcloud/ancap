"""Connect and verify user IMAP/SMTP provider accounts (single account)."""
from __future__ import annotations
from app.services.recoverable_errors import report_optional_failure

import base64
import hashlib
import imaplib
import os
import smtplib
from datetime import datetime, timezone
from uuid import uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import MailProviderAccount
from app.schemas.mail_accounts import (
    MailAccountStatus,
    MailImapSmtpConnect,
    MailImapSmtpTestRequest,
    MailImapSmtpTestResult,
    MailProviderAccountPublic,
    MailProviderDefaultsPublic,
    MailProviderKind,
)
from app.services import instantly as instantly_svc


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _secret_key_bytes() -> bytes:
    from app.services.crypto_secrets import resolve_secret_material

    get_settings()
    material = resolve_secret_material(
        dedicated=None,
        secret_key_suffix=b"|mail-provider-accounts-v1",
        development_fallback=b"ancap-dev-mail-account-key|mail-provider-accounts-v1",
        purpose="Mail account crypto",
    )
    return hashlib.sha256(material).digest()


def _encrypt_secret(plaintext: str) -> str:
    key = _secret_key_bytes()
    nonce = os.urandom(12)
    ct = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.urlsafe_b64encode(nonce + ct).decode("ascii")


def _decrypt_secret(blob: str) -> str:
    raw = base64.urlsafe_b64decode(blob.encode("ascii"))
    nonce, ct = raw[:12], raw[12:]
    pt = AESGCM(_secret_key_bytes()).decrypt(nonce, ct, None)
    return pt.decode("utf-8")


def _test_imap(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    use_ssl: bool,
    timeout: float = 12.0,
) -> None:
    client: imaplib.IMAP4 | imaplib.IMAP4_SSL
    if use_ssl:
        client = imaplib.IMAP4_SSL(host, port, timeout=timeout)
    else:
        client = imaplib.IMAP4(host, port, timeout=timeout)
    try:
        typ, _ = client.login(username, password)
        if typ != "OK":
            raise RuntimeError("IMAP login failed")
        client.select("INBOX", readonly=True)
    finally:
        try:
            client.logout()
        except Exception:
            report_optional_failure('app.services.mail_accounts:_test_imap:82', quiet=True)


def _test_smtp(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    use_tls: bool,
    use_ssl: bool,
    timeout: float = 12.0,
) -> None:
    if use_ssl:
        server: smtplib.SMTP = smtplib.SMTP_SSL(host, port, timeout=timeout)
    else:
        server = smtplib.SMTP(host, port, timeout=timeout)
    try:
        server.ehlo()
        if use_tls and not use_ssl:
            server.starttls()
            server.ehlo()
        server.login(username, password)
    finally:
        try:
            server.quit()
        except Exception:
            report_optional_failure('app.services.mail_accounts:_test_smtp:109', quiet=True)


def defaults() -> MailProviderDefaultsPublic:
    inst = instantly_svc.status_public()
    return MailProviderDefaultsPublic(
        instantly_enabled=bool(inst.get("enabled")),
        instantly_configured=bool(inst.get("configured")),
        instantly_api_base=str(inst.get("api_base") or "https://api.instantly.ai/api/v2"),
    )


def _public(row: MailProviderAccount) -> MailProviderAccountPublic:
    meta = row.metadata_json if isinstance(row.metadata_json, dict) else {}
    return MailProviderAccountPublic(
        id=row.id,
        display_name=row.display_name,
        email_address=row.email_address,
        provider_kind=MailProviderKind(row.provider_kind),
        imap_host=row.imap_host,
        imap_port=row.imap_port,
        imap_username=row.imap_username,
        imap_use_ssl=bool(row.imap_use_ssl),
        smtp_host=row.smtp_host,
        smtp_port=row.smtp_port,
        smtp_username=row.smtp_username,
        smtp_use_tls=bool(row.smtp_use_tls),
        smtp_use_ssl=bool(row.smtp_use_ssl),
        status=MailAccountStatus(row.status),
        last_verified_at=row.last_verified_at,
        last_error=row.last_error,
        instantly_email=meta.get("instantly_email"),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def get_account(session: AsyncSession, *, user_id: str) -> MailProviderAccountPublic | None:
    stmt = select(MailProviderAccount).where(MailProviderAccount.owner_user_id == user_id)
    row = (await session.execute(stmt)).scalar_one_or_none()
    return _public(row) if row else None


def test_connection(body: MailImapSmtpTestRequest) -> MailImapSmtpTestResult:
    imap_ok = False
    smtp_ok: bool | None = None
    try:
        _test_imap(
            host=body.imap_host.strip(),
            port=body.imap_port,
            username=body.imap_username.strip(),
            password=body.imap_password,
            use_ssl=body.imap_use_ssl,
        )
        imap_ok = True
    except Exception as exc:  # noqa: BLE001 — surface provider errors to client
        return MailImapSmtpTestResult(
            ok=False,
            imap_ok=False,
            smtp_ok=None,
            detail=f"IMAP failed: {exc}",
        )

    if body.test_smtp and body.smtp_host:
        smtp_user = (body.smtp_username or body.imap_username).strip()
        smtp_pass = body.smtp_password if body.smtp_password is not None else body.imap_password
        try:
            _test_smtp(
                host=body.smtp_host.strip(),
                port=body.smtp_port,
                username=smtp_user,
                password=smtp_pass,
                use_tls=body.smtp_use_tls,
                use_ssl=body.smtp_use_ssl,
            )
            smtp_ok = True
        except Exception as exc:  # noqa: BLE001
            return MailImapSmtpTestResult(
                ok=False,
                imap_ok=True,
                smtp_ok=False,
                detail=f"SMTP failed: {exc}",
            )

    return MailImapSmtpTestResult(
        ok=True,
        imap_ok=imap_ok,
        smtp_ok=smtp_ok,
        detail="Connection verified",
    )


async def connect_account(
    session: AsyncSession, *, user_id: str, body: MailImapSmtpConnect
) -> MailProviderAccountPublic:
    smtp_user = (body.smtp_username or body.imap_username).strip()
    smtp_pass = body.smtp_password if body.smtp_password is not None else body.imap_password

    if body.verify:
        result = test_connection(
            MailImapSmtpTestRequest(
                imap_username=body.imap_username,
                imap_password=body.imap_password,
                imap_host=body.imap_host,
                imap_port=body.imap_port,
                imap_use_ssl=body.imap_use_ssl,
                smtp_username=smtp_user,
                smtp_password=smtp_pass,
                smtp_host=body.smtp_host,
                smtp_port=body.smtp_port,
                smtp_use_tls=body.smtp_use_tls,
                smtp_use_ssl=body.smtp_use_ssl,
                test_smtp=True,
            )
        )
        if not result.ok:
            raise HTTPException(status_code=400, detail=result.detail)

    now = _utcnow()
    stmt = select(MailProviderAccount).where(MailProviderAccount.owner_user_id == user_id)
    existing = (await session.execute(stmt)).scalar_one_or_none()

    if existing is None:
        existing = MailProviderAccount(
            id=str(uuid4()),
            owner_user_id=user_id,
            created_at=now,
        )
        session.add(existing)

    existing.display_name = (body.display_name or "").strip() or None
    existing.email_address = body.email_address.strip()
    existing.provider_kind = MailProviderKind.imap_smtp.value
    existing.imap_host = body.imap_host.strip()
    existing.imap_port = body.imap_port
    existing.imap_username = body.imap_username.strip()
    existing.imap_password_enc = _encrypt_secret(body.imap_password)
    existing.imap_use_ssl = body.imap_use_ssl
    existing.smtp_host = body.smtp_host.strip()
    existing.smtp_port = body.smtp_port
    existing.smtp_username = smtp_user
    existing.smtp_password_enc = _encrypt_secret(smtp_pass)
    existing.smtp_use_tls = body.smtp_use_tls
    existing.smtp_use_ssl = body.smtp_use_ssl
    existing.status = MailAccountStatus.connected.value
    existing.last_verified_at = now if body.verify else existing.last_verified_at
    existing.last_error = None
    existing.updated_at = now

    meta = dict(existing.metadata_json or {}) if isinstance(existing.metadata_json, dict) else {}
    instantly_note: str | None = None
    if body.push_to_instantly:
        if not instantly_svc.configured():
            raise HTTPException(
                status_code=503,
                detail="Instantly not configured (set INSTANTLY_ENABLED and INSTANTLY_API_KEY)",
            )
        first = (body.first_name or "").strip()
        last = (body.last_name or "").strip()
        if not first and body.display_name:
            parts = body.display_name.strip().split(None, 1)
            first = parts[0] if parts else "ANCAP"
            last = parts[1] if len(parts) > 1 else "Mail"
        try:
            created = await instantly_svc.create_custom_imap_account(
                email=body.email_address,
                first_name=first or "ANCAP",
                last_name=last or "Mail",
                imap_username=body.imap_username,
                imap_password=body.imap_password,
                imap_host=body.imap_host,
                imap_port=body.imap_port,
                smtp_username=smtp_user,
                smtp_password=smtp_pass,
                smtp_host=body.smtp_host,
                smtp_port=body.smtp_port,
            )
            meta["instantly_email"] = body.email_address.strip()
            meta["instantly_provider_code"] = instantly_svc.PROVIDER_CUSTOM_IMAP_SMTP
            if isinstance(created, dict):
                meta["instantly_raw_email"] = created.get("email") or body.email_address.strip()
            instantly_note = "Also registered in Instantly (Custom IMAP/SMTP)"
        except HTTPException as exc:
            existing.last_error = str(exc.detail)
            meta["instantly_error"] = str(exc.detail)
            instantly_note = f"ANCAP saved; Instantly failed: {exc.detail}"
    existing.metadata_json = meta

    await session.flush()
    public = _public(existing)
    if instantly_note:
        # surface via last_error only when Instantly failed; success stays clean
        if existing.last_error and "Instantly failed" in (instantly_note or ""):
            pass
    return public


async def delete_account(session: AsyncSession, *, user_id: str) -> None:
    stmt = select(MailProviderAccount).where(MailProviderAccount.owner_user_id == user_id)
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="No connected mail account")
    await session.delete(row)
    await session.flush()
