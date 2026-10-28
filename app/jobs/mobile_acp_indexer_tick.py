"""Mobile ACP indexer tick: DB-backed tx history for watched addresses.

Phase 6.2: replaces full-chain scan with incremental block-indexed history.
Called from POST /v1/system/jobs/tick.
"""
from __future__ import annotations

import logging
from datetime import datetime, UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    MobileAcpTx,
    MobileAddressIndexerState,
    UserAcpAddressBinding,
    UserAcpPrivacyAddress,
    UserAcpWallet,
)

logger = logging.getLogger("mobile_acp_indexer")


# Reuse the same cache TTL as the wallet_acp router


async def build_address_watchlist(session: AsyncSession) -> list[str]:
    """Union of active wallets, privacy receives, and historical bindings."""
    addrs: set[str] = set()

    for (addr,) in (await session.execute(select(UserAcpWallet.address))).all():
        cleaned = (addr or "").strip()
        if cleaned:
            addrs.add(cleaned)

    for (addr,) in (await session.execute(select(UserAcpPrivacyAddress.address))).all():
        cleaned = (addr or "").strip()
        if cleaned:
            addrs.add(cleaned)

    # Active + historical bindings (unbound_at may be set)
    for (addr,) in (await session.execute(select(UserAcpAddressBinding.address))).all():
        cleaned = (addr or "").strip()
        if cleaned:
            addrs.add(cleaned)

    return sorted(addrs)


async def mobile_acp_indexer_tick(
    session: AsyncSession,
    *,
    extra_addresses: list[str] | None = None,
) -> dict:
    """Scan ACP chain from last watermark and upsert tx history for watched addresses."""

    # 1. Load or create watermark state
    state_row = await session.execute(select(MobileAddressIndexerState).where(MobileAddressIndexerState.id == 1))
    state = state_row.scalar_one_or_none()
    if state is None:
        state = MobileAddressIndexerState(id=1, last_scanned_height=0, indexed_addresses=[])
        session.add(state)
        await session.flush()

    # 2. Always refresh watchlist from wallets + privacy + bindings (active + historical)
    addresses_to_watch = await build_address_watchlist(session)
    for raw in extra_addresses or []:
        cleaned = (raw or "").strip()
        if cleaned and cleaned not in addresses_to_watch:
            addresses_to_watch.append(cleaned)
    addresses_to_watch = sorted(set(addresses_to_watch))
    state.indexed_addresses = addresses_to_watch
    await session.flush()

    # 3. Poll chain for new blocks from last_scanned_height + 1
    # Non-interactive: build/refresh cache synchronously so the indexer can progress.
    from app.api.routers import wallet_acp as wa
    try:
        best_height, _, tx_index = wa._scan_chain_transactions(interactive=False)
    except Exception as exc:
        logger.warning("mobile_acp_indexer_tick: chain scan failed: %s", exc)
        return {
            "indexed": 0,
            "skipped": 0,
            "error": str(exc),
            "addresses_watched": len(addresses_to_watch),
        }

    if best_height <= state.last_scanned_height:
        return {
            "indexed": 0,
            "skipped": len(addresses_to_watch),
            "best_height": best_height,
            "last_scanned_height": state.last_scanned_height,
            "addresses_watched": len(addresses_to_watch),
        }

    indexed = 0
    errors = 0

    for txid, tx in tx_index.items():
        block_height = int(tx.get("block_height") or 0)
        if block_height <= state.last_scanned_height:
            continue

        block_time = str(tx.get("block_time") or "")
        raw_tx_json = tx

        for addr in addresses_to_watch:
            # Check inputs (sent)
            sent_units = sum(
                int(i.get("units") or 0)
                for i in tx.get("inputs", [])
                if i.get("address") == addr
            )
            # Check outputs (received)
            received_units = sum(
                int(o.get("units") or 0)
                for o in tx.get("outputs", [])
                if o.get("address") == addr
            )

            if sent_units == 0 and received_units == 0:
                continue

            if sent_units > 0 and received_units > 0 and received_units - sent_units == 0:
                direction = "self"
            elif received_units > sent_units:
                direction = "in"
            else:
                direction = "out"

            net_units = received_units - sent_units

            # Check if already indexed
            existing = await session.execute(
                select(MobileAcpTx).where(MobileAcpTx.txid == txid, MobileAcpTx.address == addr)
            )
            if existing.scalar_one_or_none() is not None:
                continue

            row = MobileAcpTx(
                address=addr,
                txid=txid,
                block_height=block_height,
                block_time=block_time,
                direction=direction,
                sent_units=sent_units,
                received_units=received_units,
                net_units=net_units,
                fee_units=int(tx.get("fee_units") or 0),
                confirmations=max(0, best_height - block_height + 1) if best_height > 0 else 0,
                raw_tx_json=raw_tx_json,
                scanned_at=datetime.now(UTC),
            )
            session.add(row)
            indexed += 1

    # 4. Update watermark
    state.last_scanned_height = best_height
    state.last_scanned_at = datetime.now(UTC)
    await session.flush()

    logger.info(
        "mobile_acp_indexer_tick: scanned to %s, indexed=%s errors=%s addresses=%s",
        best_height,
        indexed,
        errors,
        len(addresses_to_watch),
    )
    return {
        "indexed": indexed,
        "errors": errors,
        "best_height": best_height,
        "last_scanned_height": state.last_scanned_height,
        "addresses_watched": len(addresses_to_watch),
    }
