"""Robinhood Chain watcher for RobinhoodACP.RedemptionRequested."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx
from eth_abi import decode
from eth_utils import keccak
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import BridgeWatcherCheckpoint, RacpRedemption, RacpRedemptionTransition
from app.services.racp_decimal import is_redeemable_racp_wei, racp_wei_to_acp_smallest

logger = logging.getLogger(__name__)

_CHECKPOINT_KEY = "robinhood_racp"
_ACP_ADDRESS_RE = re.compile(r"^acp1[a-z0-9]{20,100}$")
_REDEMPTION_TOPIC0 = keccak(text="RedemptionRequested(uint256,address,uint256,string)").hex()
_LOG_SCAN_CHUNK = 1000


def is_valid_acp_destination(address: str) -> bool:
    return bool(_ACP_ADDRESS_RE.fullmatch((address or "").strip()))


async def _rpc(rpc_url: str, method: str, params: list[Any]) -> Any:
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(rpc_url, json=body)
        r.raise_for_status()
        data = r.json()
        if data.get("error"):
            raise RuntimeError(str(data["error"]))
        return data["result"]


def decode_redemption_requested(log: dict[str, Any]) -> dict[str, Any] | None:
    topics = log.get("topics") or []
    if len(topics) < 3:
        return None
    topic0 = str(topics[0] or "").lower()
    if topic0.startswith("0x"):
        topic0 = topic0[2:]
    if topic0 != _REDEMPTION_TOPIC0.lower():
        return None
    try:
        redemption_id = int(str(topics[1]), 16)
        holder = f"0x{str(topics[2])[-40:]}".lower()
        payload = bytes.fromhex(str(log.get("data") or "0x")[2:])
        amount, acp_address = decode(["uint256", "string"], payload)
        return {
            "redemption_id": redemption_id,
            "holder": holder,
            "amount": int(amount),
            "acp_address": str(acp_address).strip(),
            "tx_hash": str(log.get("transactionHash") or "").lower(),
            "block_number": int(str(log.get("blockNumber") or "0x0"), 16),
            "log_index": int(str(log.get("logIndex") or "0x0"), 16),
        }
    except Exception:
        return None


async def append_transition(
    session: AsyncSession,
    row: RacpRedemption,
    to_status: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> None:
    from_status = row.status
    row.status = to_status
    row.version = int(row.version or 0) + 1
    row.updated_at = datetime.now(timezone.utc)
    session.add(
        RacpRedemptionTransition(
            id=str(uuid4()),
            redemption_id=row.id,
            from_status=from_status,
            to_status=to_status,
            metadata_json=metadata or {},
        )
    )


async def tick_racp_rh_checkpoint(session: AsyncSession) -> dict[str, Any]:
    settings = get_settings()
    if not settings.racp_redeem_enabled:
        return {"skipped": True, "reason": "racp_redeem_disabled"}
    if settings.racp_redeem_paused:
        return {"skipped": True, "reason": "racp_redeem_paused"}

    rpc = (settings.racp_rpc_url or "").strip()
    contract = (settings.racp_contract or "").strip().lower()
    if not rpc or not contract:
        return {"skipped": True, "reason": "missing_rpc_or_contract"}

    try:
        height = int(await _rpc(rpc, "eth_blockNumber", []), 16)
    except Exception as exc:
        logger.warning("racp rh watcher rpc failed: %s", exc)
        return {"ok": False, "error": str(exc)}

    cp = await session.get(BridgeWatcherCheckpoint, _CHECKPOINT_KEY)
    if cp is None:
        cp = BridgeWatcherCheckpoint(chain_key=_CHECKPOINT_KEY, last_block_height=0)
        session.add(cp)
        await session.flush()

    previous = int(cp.last_block_height or 0)
    confirmations = max(1, int(settings.racp_redeem_rh_confirmations or 1))
    confirmed_height = max(0, height - confirmations + 1)
    if confirmed_height <= previous:
        return {
            "ok": True,
            "chain_key": _CHECKPOINT_KEY,
            "last_block_height": previous,
            "tip": height,
            "matched": 0,
        }

    scan_from = previous + 1
    matched = 0
    rejected = 0
    chain_id = str(settings.racp_chain_id or "4663")

    for start in range(scan_from, confirmed_height + 1, _LOG_SCAN_CHUNK):
        end = min(start + _LOG_SCAN_CHUNK - 1, confirmed_height)
        logs = await _rpc(
            rpc,
            "eth_getLogs",
            [
                {
                    "fromBlock": hex(start),
                    "toBlock": hex(end),
                    "address": contract,
                    "topics": ["0x" + _REDEMPTION_TOPIC0],
                }
            ],
        )
        for log in logs or []:
            decoded = decode_redemption_requested(log)
            if not decoded:
                continue
            acp_address = decoded["acp_address"]
            amount = int(decoded["amount"])
            if not is_valid_acp_destination(acp_address) or not is_redeemable_racp_wei(amount):
                rejected += 1
                logger.warning(
                    "racp redemption rejected id=%s acp=%s amount=%s",
                    decoded["redemption_id"],
                    acp_address[:24],
                    amount,
                )
                continue

            existing = await session.scalar(
                select(RacpRedemption.id).where(
                    RacpRedemption.rh_chain_id == chain_id,
                    RacpRedemption.rh_tx_hash == decoded["tx_hash"],
                    RacpRedemption.rh_log_index == decoded["log_index"],
                )
            )
            if existing is not None:
                continue
            existing_id = await session.scalar(
                select(RacpRedemption.id).where(
                    RacpRedemption.redemption_id == int(decoded["redemption_id"])
                )
            )
            if existing_id is not None:
                continue

            row = RacpRedemption(
                id=str(uuid4()),
                status="BURN_CONFIRMED",
                redemption_id=int(decoded["redemption_id"]),
                holder=decoded["holder"],
                amount_racp_wei=amount,
                amount_acp_smallest=racp_wei_to_acp_smallest(amount),
                user_acp_address=acp_address,
                rh_chain_id=chain_id,
                rh_tx_hash=decoded["tx_hash"],
                rh_log_index=int(decoded["log_index"]),
                rh_block_number=int(decoded["block_number"]),
            )
            session.add(row)
            session.add(
                RacpRedemptionTransition(
                    id=str(uuid4()),
                    redemption_id=row.id,
                    from_status=None,
                    to_status="BURN_CONFIRMED",
                    metadata_json={
                        "tx_hash": decoded["tx_hash"],
                        "log_index": decoded["log_index"],
                        "block_number": decoded["block_number"],
                    },
                )
            )
            matched += 1

    cp.last_block_height = confirmed_height
    cp.updated_at = datetime.now(timezone.utc)
    await session.flush()
    return {
        "ok": True,
        "chain_key": _CHECKPOINT_KEY,
        "last_block_height": confirmed_height,
        "tip": height,
        "scanned_from": scan_from,
        "scanned_to": confirmed_height,
        "matched": matched,
        "rejected": rejected,
    }
