"""Public rACP redemption status + row serialization."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import RacpRedemption
from app.schemas.racp_redeem import RacpRedeemPublicStatus, RacpRedemptionPublic
from app.services.racp_decimal import RACP_PER_ACP, racp_wei_to_human


def serialize_redemption(row: RacpRedemption) -> RacpRedemptionPublic:
    return RacpRedemptionPublic(
        id=str(row.id),
        status=str(row.status),
        redemption_id=int(row.redemption_id),
        holder=str(row.holder),
        amount_racp_wei=str(int(row.amount_racp_wei)),
        amount_racp=racp_wei_to_human(int(row.amount_racp_wei)),
        amount_acp_smallest=str(int(row.amount_acp_smallest)),
        amount_acp=format(Decimal(int(row.amount_acp_smallest)) / Decimal("100000000"), "f"),
        user_acp_address=str(row.user_acp_address),
        rh_tx_hash=str(row.rh_tx_hash),
        rh_log_index=int(row.rh_log_index),
        rh_block_number=int(row.rh_block_number) if row.rh_block_number is not None else None,
        acp_tx_hash=str(row.acp_tx_hash) if row.acp_tx_hash else None,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def public_status(session: AsyncSession) -> RacpRedeemPublicStatus:
    settings = get_settings()
    enabled = bool(settings.racp_redeem_enabled)
    paused = bool(settings.racp_redeem_paused)
    reserve = (settings.racp_reserve_acp_address or "").strip()
    notes = [
        "1 ACP = 10 rACP. Burn via requestRedemption on Robinhood Chain; ACP pays from exclusive reserve.",
        "Destination is the acp1 address in the on-chain event. Recipients pay ETH gas on Robinhood Chain.",
        "Exclusive reserve is not the wACP bridge hot wallet.",
    ]
    if not enabled:
        notes.append("RACP_REDEEM_ENABLED is false — automated payouts stay off.")
    elif paused:
        notes.append("RACP_REDEEM_PAUSED is true — watcher/payout ticks skip.")
    if settings.racp_redeem_dry_run:
        notes.append("RACP_REDEEM_DRY_RUN is true — payouts record dryrun txids only.")

    reserve_balance_acp: str | None = None
    if reserve:
        try:
            from app.api.routers.wallet_acp import _require_acp_rpc_url, _run_walletd

            rpc = _require_acp_rpc_url()
            bal = _run_walletd(["balance", "--rpc", rpc, "--address", reserve], timeout_s=30)
            reserve_balance_acp = str(bal.get("acp") or "")
        except Exception:
            reserve_balance_acp = None

    open_liability = int(
        await session.scalar(
            select(func.count())
            .select_from(RacpRedemption)
            .where(RacpRedemption.status.in_(("BURN_CONFIRMED", "ACP_PAYOUT_SENT", "DISPUTED")))
        )
        or 0
    )
    completed = int(
        await session.scalar(
            select(func.count())
            .select_from(RacpRedemption)
            .where(RacpRedemption.status == "COMPLETED")
        )
        or 0
    )

    return RacpRedeemPublicStatus(
        enabled=enabled and not paused,
        configured=enabled,
        paused=paused,
        dry_run=bool(settings.racp_redeem_dry_run),
        chain_id=int(settings.racp_chain_id or 4663),
        token_contract=(settings.racp_contract or "").strip(),
        reserve_acp_address=reserve,
        reserve_balance_acp=reserve_balance_acp,
        racp_per_acp=RACP_PER_ACP,
        open_liability_count=open_liability,
        completed_count=completed,
        notes=notes,
    )


async def get_by_tx(session: AsyncSession, tx_hash: str) -> RacpRedemption | None:
    normalized = (tx_hash or "").strip().lower()
    if not normalized.startswith("0x"):
        normalized = f"0x{normalized}"
    return await session.scalar(
        select(RacpRedemption)
        .where(RacpRedemption.rh_tx_hash == normalized)
        .order_by(RacpRedemption.rh_log_index.asc())
        .limit(1)
    )


async def get_by_onchain_id(session: AsyncSession, redemption_id: int) -> RacpRedemption | None:
    return await session.scalar(
        select(RacpRedemption).where(RacpRedemption.redemption_id == int(redemption_id))
    )


async def list_open(session: AsyncSession, *, limit: int = 100) -> list[RacpRedemption]:
    rows = (
        await session.execute(
            select(RacpRedemption)
            .where(RacpRedemption.status.in_(("BURN_CONFIRMED", "ACP_PAYOUT_SENT", "DISPUTED")))
            .order_by(RacpRedemption.created_at.asc())
            .limit(limit)
        )
    ).scalars().all()
    return list(rows)
