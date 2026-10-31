"""Account-wide credentials. One row per owner; rotation preserves usage history."""
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Agent, ApiKey, User
from app.db.session import async_session_maker
from app.schemas.keys import AccountApiKeyPublic
from app.services.api_keys import generate_key, resolve_key_record
from app.services.recoverable_errors import report_optional_failure


def public_key_status(row: ApiKey | None) -> AccountApiKeyPublic:
    if row is None:
        return AccountApiKeyPublic(active=False)
    return AccountApiKeyPublic(
        active=row.revoked_at is None,
        key_prefix=row.key_prefix,
        created_at=row.created_at,
        revoked_at=row.revoked_at,
        last_used_at=row.last_used_at,
        requests=row.request_count,
        successful_requests=row.success_count,
        failed_requests=row.error_count,
    )


async def account_key(session: AsyncSession, user_id: str) -> ApiKey | None:
    return (await session.execute(select(ApiKey).where(ApiKey.owner_user_id == user_id))).scalar_one_or_none()


async def change_account_key(session: AsyncSession, user_id: str, *, rotate: bool = False) -> tuple[ApiKey, str]:
    # Serializes create/rotate/revoke, including the first issuance with no key row.
    user = (await session.execute(select(User).where(User.id == user_id).with_for_update())).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Account not found")
    row = await account_key(session, user_id)
    active = row is not None and row.revoked_at is None
    if active and not rotate:
        raise HTTPException(status_code=409, detail="Account already has an API key. Rotate it to replace it.")
    if not active and rotate:
        raise HTTPException(status_code=404, detail="No active API key")
    raw, prefix, digest = generate_key()
    if row is None:
        # Compatibility identity for existing agent-based commerce endpoints.
        # No wallet/private signing key is retained and no user agent choice is required.
        public = Ed25519PrivateKey.generate().public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
        agent = Agent(display_name="Account API", public_key=public, roles=["buyer"],
                      owner_user_id=user_id, metadata_={"account_api_identity": True})
        session.add(agent)
        await session.flush()
        row = ApiKey(owner_user_id=user_id, agent_id=agent.id, name="Platform API", scope="account",
                     key_prefix=prefix, key_hash=digest)
        session.add(row)
    else:
        row.key_prefix = prefix
        row.key_hash = digest
        row.created_at = datetime.now(timezone.utc)
        row.revoked_at = None
        row.expires_at = None
    await session.flush()
    await session.refresh(row)
    return row, raw


async def revoke_account_key(session: AsyncSession, user_id: str) -> None:
    await session.execute(select(User.id).where(User.id == user_id).with_for_update())
    # Preserve accounting and statistics. A revoked row cannot authenticate.
    await session.execute(update(ApiKey).where(ApiKey.owner_user_id == user_id, ApiKey.revoked_at.is_(None))
                          .values(revoked_at=datetime.now(timezone.utc)))
    await session.flush()


async def metered_key_id(raw: str | None) -> str | None:
    if not raw or not raw.startswith("ancap_"):
        return None
    try:
        async with async_session_maker() as session:
            resolved = await resolve_key_record(session, raw)
            return str(resolved.row_id) if resolved and resolved.owner_user_id else None
    except Exception:
        report_optional_failure("account_api_key.meter_lookup")
        return None


async def record_key_request(key_id: str | None, status: int) -> None:
    if key_id is None:
        return
    try:
        async with async_session_maker() as session:
            await session.execute(update(ApiKey).where(ApiKey.id == key_id).values(
                request_count=ApiKey.request_count + 1,
                success_count=ApiKey.success_count + int(status < 400),
                error_count=ApiKey.error_count + int(status >= 400),
                last_used_at=datetime.now(timezone.utc),
            ))
            await session.commit()
    except Exception:
        # Metering must not undo a completed payment or expose credentials in logs.
        report_optional_failure("account_api_key.meter_record")
