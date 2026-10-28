from __future__ import annotations
from app.services.recoverable_errors import report_optional_failure

import json
from functools import lru_cache
from typing import Any

from app.config import get_settings


@lru_cache
def _redis_module():
    try:
        import redis.asyncio as redis  # type: ignore

        return redis
    except Exception:
        return None


async def get_redis_client():
    settings = get_settings()
    if not settings.redis_url:
        return None
    redis = _redis_module()
    if redis is None:
        return None
    return redis.from_url(settings.redis_url, decode_responses=True)


async def redis_ping() -> tuple[bool, str | None]:
    client = await get_redis_client()
    if client is None:
        return False, "redis_not_configured"
    try:
        pong = await client.ping()
        await client.aclose()
        return bool(pong), None
    except Exception as exc:
        return False, str(exc)


async def cache_get_json(key: str) -> Any | None:
    client = await get_redis_client()
    if client is None:
        return None
    try:
        raw = await client.get(key)
        await client.aclose()
        return json.loads(raw) if raw else None
    except Exception:
        return None


async def cache_set_json(key: str, value: Any, *, ttl_seconds: int) -> None:
    client = await get_redis_client()
    if client is None:
        return
    try:
        await client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
    finally:
        await client.aclose()


@lru_cache
def _redis_sync_module():
    try:
        import redis as redis_sync  # type: ignore

        return redis_sync
    except Exception:
        return None


def cache_set_json_sync(key: str, value: Any, *, ttl_seconds: int) -> None:
    """Thread-safe Redis write for background workers (no event loop required)."""
    settings = get_settings()
    if not settings.redis_url:
        return
    mod = _redis_sync_module()
    if mod is None:
        return
    client = None
    try:
        client = mod.from_url(settings.redis_url, decode_responses=True)
        client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
    except Exception:
        return
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                report_optional_failure('app.services.cache:cache_set_json_sync:client.close', quiet=True)


def cache_get_json_sync(key: str) -> Any | None:
    settings = get_settings()
    if not settings.redis_url:
        return None
    mod = _redis_sync_module()
    if mod is None:
        return None
    client = None
    try:
        client = mod.from_url(settings.redis_url, decode_responses=True)
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                report_optional_failure('app.services.cache:cache_get_json_sync:client.close', quiet=True)
