"""BSC JSON-RPC watcher checkpoint + mint confirmation progression."""
from __future__ import annotations
from app.services.recoverable_errors import report_optional_failure

import logging
from typing import Any

import httpx
from eth_abi import decode
from eth_utils import keccak
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import BridgeAuditEvent, BridgeOperation, BridgeWatcherCheckpoint
from app.services.bridge_orchestrator import append_transition

logger = logging.getLogger(__name__)


async def _rpc(rpc_url: str, method: str, params: list[Any]) -> Any:
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(rpc_url, json=body)
        r.raise_for_status()
        data = r.json()
        if data.get("error"):
            raise RuntimeError(str(data["error"]))
        return data["result"]


async def _eth_block_number(rpc_url: str) -> int:
    return int(await _rpc(rpc_url, "eth_blockNumber", []), 16)


async def _eth_get_transaction_receipt(rpc_url: str, tx_hash: str) -> dict[str, Any] | None:
    normalized = (tx_hash or "").strip()
    if normalized and not normalized.startswith("0x"):
        normalized = f"0x{normalized}"
    res = await _rpc(rpc_url, "eth_getTransactionReceipt", [normalized])
    return res


async def _eth_get_logs(rpc_url: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    res = await _rpc(rpc_url, "eth_getLogs", [params])
    return list(res or [])


_RELEASE_REQUESTED_TOPIC0 = keccak(text="ReleaseRequested(uint256,address,string,uint256)").hex()
_BSC_RELEASE_LOG_SCAN_CHUNK = 1000
_BSC_RELEASE_LOG_RECOVERY_LOOKBACK = 64


def _decode_release_requested(log: dict[str, Any]) -> dict[str, Any] | None:
    topics = log.get("topics") or []
    if len(topics) < 3:
        return None
    topic0 = str(topics[0] or "").lower()
    if topic0.startswith("0x"):
        topic0 = topic0[2:]
    if topic0 != _RELEASE_REQUESTED_TOPIC0.lower():
        return None

    try:
        request_id = int(str(topics[1]), 16)
        from_topic = str(topics[2])
        from_addr = f"0x{from_topic[-40:]}".lower()
        payload = bytes.fromhex(str(log.get("data") or "0x")[2:])
        acp_address, amount = decode(["string", "uint256"], payload)
        tx_hash = str(log.get("transactionHash") or "")
        block_number = int(str(log.get("blockNumber") or "0x0"), 16)
        log_index = int(str(log.get("logIndex") or "0x0"), 16)
        return {
            "request_id": request_id,
            "from": from_addr,
            "acp_address": str(acp_address),
            "amount": int(amount),
            "tx_hash": tx_hash,
            "block_number": block_number,
            "log_index": log_index,
        }
    except Exception:
        return None


async def tick_bsc_checkpoint(session: AsyncSession) -> dict[str, Any]:
    settings = get_settings()
    if not settings.bridge_rail_enabled:
        return {"skipped": True, "reason": "bridge_rail_disabled"}
    rpc = (settings.bridge_bsc_rpc_url or "").strip()
    if not rpc:
        return {"skipped": True, "reason": "no_bsc_rpc"}
    try:
        height = await _eth_block_number(rpc)
    except Exception as exc:
        logger.warning("bsc watcher rpc failed: %s", exc)
        return {"ok": False, "error": str(exc)}

    row = await session.get(BridgeWatcherCheckpoint, "bsc")
    if row is None:
        row = BridgeWatcherCheckpoint(chain_key="bsc", last_block_height=0)
        session.add(row)
    previous_height = int(row.last_block_height or 0)

    confirmed = 0
    matched_releases = 0
    release_scan_from: int | None = None
    release_scan_to: int | None = None

    gateway_addr = (settings.bridge_gateway_contract or "").strip().lower()
    confirmed_height = max(0, height - int(settings.bridge_bsc_confirmations) + 1)
    if gateway_addr and confirmed_height > 0:
        has_pending_reverse = (
            await session.scalar(
                select(BridgeOperation.id)
                .where(
                    BridgeOperation.direction == "bsc_to_acp",
                    BridgeOperation.status == "PENDING_BURN",
                    BridgeOperation.bsc_tx_hash_burn.is_(None),
                )
                .limit(1)
            )
            is not None
        )
        scan_from = previous_height + 1
        if has_pending_reverse:
            recovery_from = max(1, confirmed_height - _BSC_RELEASE_LOG_RECOVERY_LOOKBACK + 1)
            scan_from = min(scan_from, recovery_from)
        if scan_from <= confirmed_height:
            release_scan_from = scan_from
            last_successful_to = scan_from - 1
            try:
                chunk_start = scan_from
                while chunk_start <= confirmed_height:
                    chunk_end = min(chunk_start + _BSC_RELEASE_LOG_SCAN_CHUNK - 1, confirmed_height)
                    logs = await _eth_get_logs(
                        rpc,
                        {
                            "fromBlock": hex(chunk_start),
                            "toBlock": hex(chunk_end),
                            "address": gateway_addr,
                            "topics": [f"0x{_RELEASE_REQUESTED_TOPIC0}"],
                        },
                    )
                    for raw_log in logs:
                        decoded = _decode_release_requested(raw_log)
                        if not decoded:
                            continue
                        tx_hash = str(decoded["tx_hash"] or "")
                        log_index = int(decoded["log_index"])
                        dup = await session.scalar(
                            select(BridgeOperation.id).where(
                                BridgeOperation.bsc_tx_hash_burn == tx_hash,
                                BridgeOperation.bsc_log_index == log_index,
                            )
                        )
                        if dup is not None:
                            continue
                        op = (
                            await session.execute(
                                select(BridgeOperation)
                                .where(
                                    BridgeOperation.direction == "bsc_to_acp",
                                    BridgeOperation.status == "PENDING_BURN",
                                    BridgeOperation.bsc_tx_hash_burn.is_(None),
                                    BridgeOperation.user_bsc_address == str(decoded["from"]),
                                    BridgeOperation.user_acp_address == str(decoded["acp_address"]),
                                    BridgeOperation.amount_wacp_wei == int(decoded["amount"]),
                                )
                                .order_by(BridgeOperation.created_at.asc())
                                .limit(1)
                            )
                        ).scalars().first()
                        if op is None:
                            session.add(
                                BridgeAuditEvent(
                                    operation_id=None,
                                    event_type="bsc_release_unmatched",
                                    payload_json=decoded,
                                )
                            )
                            continue
                        op.bsc_tx_hash_burn = tx_hash
                        op.bsc_log_index = log_index
                        op.correlation_id = str(decoded["request_id"])
                        session.add(
                            BridgeAuditEvent(
                                operation_id=op.id,
                                event_type="bsc_release_requested",
                                payload_json=decoded,
                            )
                        )
                        await append_transition(
                            session,
                            op,
                            "BURN_CONFIRMED",
                            metadata={
                                "tx_hash": tx_hash,
                                "log_index": log_index,
                                "request_id": decoded["request_id"],
                                "block_number": decoded["block_number"],
                                "confirmations": max(0, height - int(decoded["block_number"]) + 1),
                            },
                        )
                        matched_releases += 1
                    last_successful_to = chunk_end
                    chunk_start = chunk_end + 1
                row.last_block_height = confirmed_height
                release_scan_to = confirmed_height
            except Exception as exc:
                row.last_block_height = max(0, last_successful_to)
                release_scan_to = max(0, last_successful_to)
                logger.warning("bsc release watcher failed: %s", exc)
        elif previous_height > confirmed_height:
            row.last_block_height = confirmed_height

    confirmed = 0
    ops = (
        await session.execute(
            select(BridgeOperation).where(
                BridgeOperation.direction == "acp_to_bsc",
                BridgeOperation.status == "MINT_REQUESTED",
                BridgeOperation.bsc_tx_hash_mint.is_not(None),
            )
        )
    ).scalars().all()

    for op in ops:
        try:
            receipt = await _eth_get_transaction_receipt(rpc, str(op.bsc_tx_hash_mint))
            if not receipt:
                continue
            status_hex = receipt.get("status")
            if int(status_hex, 16) != 1:
                session.add(
                    BridgeAuditEvent(
                        operation_id=op.id,
                        event_type="bsc_mint_failed",
                        payload_json={"tx_hash": op.bsc_tx_hash_mint, "receipt": receipt},
                    )
                )
                await append_transition(
                    session,
                    op,
                    "FAILED",
                    metadata={"reason": "bsc_mint_failed", "tx_hash": op.bsc_tx_hash_mint},
                )
                continue
            block_number = int(receipt.get("blockNumber"), 16)
            confirmations = max(0, height - block_number + 1)
            if confirmations < int(settings.bridge_bsc_confirmations):
                continue
            logs = receipt.get("logs") or []
            if logs:
                try:
                    op.bsc_log_index = int(logs[0].get("logIndex"), 16)
                except Exception:
                    report_optional_failure('app.services.bridge_bsc_watcher:tick_bsc_checkpoint:int', quiet=False)
            await append_transition(
                session,
                op,
                "MINTED_ON_BSC",
                metadata={
                    "tx_hash": op.bsc_tx_hash_mint,
                    "confirmations": confirmations,
                    "block_number": block_number,
                },
            )
            session.add(
                BridgeAuditEvent(
                    operation_id=op.id,
                    event_type="bsc_mint_confirmed",
                    payload_json={
                        "tx_hash": op.bsc_tx_hash_mint,
                        "confirmations": confirmations,
                        "block_number": block_number,
                        "log_index": op.bsc_log_index,
                    },
                )
            )
            await append_transition(
                session,
                op,
                "COMPLETED",
                metadata={
                    "tx_hash": op.bsc_tx_hash_mint,
                    "confirmations": confirmations,
                    "block_number": block_number,
                },
            )
            confirmed += 1
        except Exception as exc:
            logger.warning("bsc mint confirmation failed for %s: %s", op.id, exc)

    await session.flush()
    return {
        "ok": True,
        "chain_key": "bsc",
        "last_block_height": int(row.last_block_height or 0),
        "latest_block_height": height,
        "confirmed_height": confirmed_height,
        "confirmed_mints": confirmed,
        "matched_releases": matched_releases,
        "release_scan_from": release_scan_from,
        "release_scan_to": release_scan_to,
    }
