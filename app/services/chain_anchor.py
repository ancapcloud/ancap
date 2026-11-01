"""L3: On-chain anchoring. Mock driver stores in DB; ACP driver calls chain RPC; other drivers pluggable."""
from __future__ import annotations

from typing import Awaitable, Callable

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChainAnchor


async def anchor_mock(
    session: AsyncSession,
    *,
    chain_id: str,
    payload_type: str,
    payload_hash: str,
    payload_json: dict | None = None,
) -> ChainAnchor:
    """Store anchor in DB; mock tx_hash = deterministic from payload_hash."""
    rec = ChainAnchor(
        chain_id=chain_id,
        tx_hash=f"0x{mock_tx_hash(payload_hash)}",
        payload_type=payload_type,
        payload_hash=payload_hash,
        payload_json=payload_json,
    )
    session.add(rec)
    await session.flush()
    return rec


def mock_tx_hash(payload_hash: str) -> str:
    """Deterministic mock tx hash from payload hash."""
    return (payload_hash + "0" * 64)[:64]


def _parse_tx_hash_from_rpc_result(result: str | dict | None) -> str:
    if result is None:
        raise ValueError("RPC returned no result")
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        tx_hash = result.get("tx_hash") or result.get("txHash") or result.get("signature")
        if tx_hash:
            return tx_hash
        raise ValueError("RPC result missing tx_hash/signature")
    return str(result)


async def _anchor_via_rpc(
    session: AsyncSession,
    *,
    rpc_url: str,
    driver_label: str,
    chain_id: str,
    payload_type: str,
    payload_hash: str,
    payload_json: dict | None = None,
) -> ChainAnchor:
    """Submit anchor via JSON-RPC (method ancap_anchor). On success create ChainAnchor with returned tx_hash/signature."""
    url = (rpc_url or "").strip()
    if not url:
        raise ValueError(f"{driver_label} RPC URL not configured")
    payload = {
        "jsonrpc": "2.0",
        "method": "ancap_anchor",
        "params": {
            "chain_id": chain_id,
            "payload_type": payload_type,
            "payload_hash": payload_hash,
        },
        "id": 1,
    }
    try:
        from app.services.acp_rpc import acp_rpc_headers

        headers = acp_rpc_headers() if driver_label == "ACP" else {
            "Content-Type": "application/json",
            "User-Agent": "ancap-backend/1.0",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(url, json=payload, headers=headers, timeout=15.0)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        raise ValueError(f"{driver_label} RPC request failed: {e}") from e
    except Exception as e:
        raise ValueError(f"{driver_label} RPC error: {e}") from e

    if data.get("error"):
        err = data["error"]
        raise ValueError(f"{driver_label} RPC error: {err.get('message', err)}")
    tx_hash = _parse_tx_hash_from_rpc_result(data.get("result"))
    if not tx_hash.startswith("0x") and not tx_hash.startswith("0X"):
        tx_hash = f"0x{tx_hash}"

    rec = ChainAnchor(
        chain_id=chain_id,
        tx_hash=tx_hash,
        payload_type=payload_type,
        payload_hash=payload_hash,
        payload_json=payload_json,
    )
    session.add(rec)
    await session.flush()
    return rec


async def anchor_acp(
    session: AsyncSession,
    *,
    chain_id: str,
    payload_type: str,
    payload_hash: str,
    payload_json: dict | None = None,
) -> ChainAnchor:
    """Submit anchor via ACP RPC (JSON-RPC method ancap_anchor)."""
    from app.config import get_settings
    settings = get_settings()
    return await _anchor_via_rpc(
        session,
        rpc_url=settings.acp_rpc_url or "",
        driver_label="ACP",
        chain_id=chain_id,
        payload_type=payload_type,
        payload_hash=payload_hash,
        payload_json=payload_json,
    )


async def anchor_ethereum(
    session: AsyncSession,
    *,
    chain_id: str,
    payload_type: str,
    payload_hash: str,
    payload_json: dict | None = None,
) -> ChainAnchor:
    """Submit anchor via Ethereum RPC (JSON-RPC method ancap_anchor; endpoint must support it)."""
    from app.config import get_settings
    settings = get_settings()
    return await _anchor_via_rpc(
        session,
        rpc_url=settings.ethereum_rpc_url or "",
        driver_label="Ethereum",
        chain_id=chain_id or "ethereum",
        payload_type=payload_type,
        payload_hash=payload_hash,
        payload_json=payload_json,
    )


async def anchor_solana(
    session: AsyncSession,
    *,
    chain_id: str,
    payload_type: str,
    payload_hash: str,
    payload_json: dict | None = None,
) -> ChainAnchor:
    """Submit anchor via Solana RPC (JSON-RPC method ancap_anchor; endpoint must support it)."""
    from app.config import get_settings
    settings = get_settings()
    return await _anchor_via_rpc(
        session,
        rpc_url=settings.solana_rpc_url or "",
        driver_label="Solana",
        chain_id=chain_id or "solana",
        payload_type=payload_type,
        payload_hash=payload_hash,
        payload_json=payload_json,
    )


AnchorDriver = Callable[..., Awaitable[ChainAnchor]]


def get_anchor_driver(driver_name: str) -> AnchorDriver | None:
    """Return anchor driver for driver_name (mock, acp, ethereum, solana)."""
    if driver_name == "mock":
        return anchor_mock
    if driver_name == "acp":
        return anchor_acp
    if driver_name == "ethereum":
        return anchor_ethereum
    if driver_name == "solana":
        return anchor_solana
    return None
