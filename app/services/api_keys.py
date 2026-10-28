"""API key generation, hashing and lookup."""
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ApiKey

PREFIX = "ancap_"
PREFIX_LEN = 6  # len("ancap_")
RANDOM_BYTES = 24  # 32 chars base64
KEY_PREFIX_DISPLAY_LEN = PREFIX_LEN + 12  # ancap_ + 12 chars for lookup


@dataclass(slots=True)
class ResolvedApiKey:
    row_id: UUID
    agent_id: UUID | None
    org_id: UUID | None
    scope: str | None
    key_prefix: str


def generate_key() -> tuple[str, str, str]:
    """Generate a new API key. Returns (full_key, key_prefix, key_hash)."""
    raw = secrets.token_urlsafe(RANDOM_BYTES)
    full_key = PREFIX + raw
    prefix = full_key[:KEY_PREFIX_DISPLAY_LEN]
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, prefix, key_hash


def hash_key(key: str) -> str:
    """Return SHA-256 hex digest of the key."""
    return hashlib.sha256(key.encode()).hexdigest()


async def create_key(
    session: AsyncSession,
    agent_id: UUID | None,
    scope: str | None = None,
    expires_at: datetime | None = None,
) -> tuple[ApiKey, str]:
    """Create and persist an API key. agent_id=None for org-owned keys."""
    full_key, key_prefix, key_hash = generate_key()
    row = ApiKey(
        agent_id=agent_id,
        key_prefix=key_prefix,
        key_hash=key_hash,
        scope=scope,
        expires_at=expires_at,
    )
    session.add(row)
    await session.flush()
    return row, full_key


async def resolve_key_record(session: AsyncSession, raw_key: str) -> ResolvedApiKey | None:
    """
    Resolve raw API key to its persisted record context. Returns None if invalid or expired.
    Key must start with PREFIX; we look up by prefix then verify hash.
    """
    if not raw_key or not raw_key.startswith(PREFIX) or len(raw_key) < KEY_PREFIX_DISPLAY_LEN:
        return None
    prefix = raw_key[:KEY_PREFIX_DISPLAY_LEN]
    key_hash = hash_key(raw_key)
    q = select(ApiKey).where(ApiKey.key_prefix == prefix)
    r = await session.execute(q)
    row = r.scalar_one_or_none()
    if not row or not hmac.compare_digest(row.key_hash, key_hash):
        return None
    if row.expires_at is not None:
        exp = row.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            return None
    return ResolvedApiKey(
        row_id=UUID(str(row.id)),
        agent_id=UUID(str(row.agent_id)) if row.agent_id else None,
        org_id=UUID(str(row.org_id)) if row.org_id else None,
        scope=row.scope,
        key_prefix=row.key_prefix,
    )


async def resolve_key(session: AsyncSession, raw_key: str) -> UUID | None:
    """
    Resolve raw API key to agent_id. Returns None if invalid, expired, or org-owned.
    """
    resolved = await resolve_key_record(session, raw_key)
    return resolved.agent_id if resolved else None
