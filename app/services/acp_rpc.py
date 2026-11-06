"""Shared ACP node JSON-RPC helpers."""
from __future__ import annotations

import os
from typing import Any

import httpx

from app.config import get_settings

# Cloudflare in front of acp1.ancap.cloud rejects POSTs without a User-Agent (403).
ACP_RPC_USER_AGENT = "ancap-backend/1.0"


def acp_rpc_headers() -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": ACP_RPC_USER_AGENT,
    }
    token = os.getenv("ACP_RPC_TOKEN", "").strip()
    if token:
        headers["x-acp-rpc-token"] = token
    return headers


async def acp_rpc_call(method: str, params: list | dict | None = None) -> Any:
    settings = get_settings()
    rpc_url = (settings.acp_rpc_url or "").strip()
    if not rpc_url:
        raise RuntimeError("ACP RPC URL is not configured")
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params if params is not None else []}
    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.post(rpc_url, json=body, headers=acp_rpc_headers())
    payload = response.json()
    if payload.get("error"):
        raise RuntimeError(str(payload["error"]))
    return payload.get("result")
