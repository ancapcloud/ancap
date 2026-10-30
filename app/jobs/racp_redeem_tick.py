"""Periodic tick: Robinhood burn pickup, ACP payout, ACP confirm for rACP redeem."""
from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.racp_redeem_acp import tick_racp_acp_confirm
from app.services.racp_redeem_orchestrator import tick_racp_orchestrator
from app.services.racp_redeem_watcher import tick_racp_rh_checkpoint

logger = logging.getLogger(__name__)


async def _safe_step(name: str, fn, session: AsyncSession) -> dict:
    try:
        return await fn(session)
    except Exception as exc:
        logger.exception("racp redeem step failed: %s", name)
        return {"ok": False, "error": str(exc), "step": name}


async def racp_redeem_tick(session: AsyncSession) -> dict:
    settings = get_settings()
    if not settings.racp_redeem_enabled:
        return {"skipped": True, "reason": "racp_redeem_disabled"}

    rh = await _safe_step("rh_watcher", tick_racp_rh_checkpoint, session)
    orch = await _safe_step("orchestrator", tick_racp_orchestrator, session)
    acp = await _safe_step("acp_confirm", tick_racp_acp_confirm, session)
    return {"rh": rh, "orchestrator": orch, "acp": acp}
