"""Incremental ACP UTXO index for fast wallet balance probes.

Interactive wallet UI must not tip-scan ~30k blocks via walletd. This module
keeps a per-process + Redis-backed unspent map for watched addresses and advances
it in chunks from jobs/tick (and a startup catch-up thread).
"""
from __future__ import annotations
from app.services.recoverable_errors import report_optional_failure

import json
import logging
import threading
import time
from decimal import Decimal
from typing import Any, Iterable

import httpx

from app.services.acp_rpc import acp_rpc_headers
from app.services.acp_amounts import rpc_amount_units
from app.services.acp_tokenomics import OPERATOR_ROLE_ADDRESSES
from app.config import get_settings

logger = logging.getLogger("acp_utxo_index")

_UNITS_PER_ACP = Decimal(100_000_000)
_REDIS_WM_KEY = "acp:utxo_idx:wm"
_REDIS_UNSPENT_KEY = "acp:utxo_idx:unspent"
_REDIS_BAL_PREFIX = "acp:utxo_idx:bal:"
_REDIS_BAL_TTL_S = 86_400
_CHUNK_DEFAULT = 400
_RPC_TIMEOUT_S = 20.0

# Process-local state (API workers each maintain their own; Redis is shared truth).
_lock = threading.Lock()
_state: dict[str, Any] = {
    "wm": 0,
    "tip_hash": None,
    "unspent": {},  # outpoint -> (address, units)
    "watch": set(OPERATOR_ROLE_ADDRESSES),
    "catchup_inflight": False,
}


def _units_to_acp_str(units: int) -> str:
    acp = (Decimal(units) / _UNITS_PER_ACP).quantize(Decimal("0.00000001"))
    return format(acp, "f")


def _amount_to_units(raw: object) -> int:
    """Parse node RPC amounts, which are always integer base units."""
    return rpc_amount_units(raw)


def _rpc(rpc_url: str, method: str, params: list | dict | None = None) -> Any:
    body = {"jsonrpc": "2.0", "id": "acp-utxo-index", "method": method, "params": params or []}
    r = httpx.post(rpc_url, json=body, headers=acp_rpc_headers(), timeout=_RPC_TIMEOUT_S)
    payload = r.json()
    if r.status_code != 200 or payload.get("error"):
        raise RuntimeError(str(payload.get("error") or f"status={r.status_code}"))
    return payload.get("result")


def _require_rpc_url() -> str:
    url = (get_settings().acp_rpc_url or "").strip()
    if not url:
        raise RuntimeError("ACP RPC URL is not configured")
    return url


def set_watch_addresses(addresses: Iterable[str]) -> None:
    cleaned = {str(a).strip() for a in addresses if str(a or "").strip()}
    cleaned |= set(OPERATOR_ROLE_ADDRESSES)
    with _lock:
        _state["watch"] = cleaned


def watched_addresses() -> set[str]:
    with _lock:
        return set(_state["watch"] or set(OPERATOR_ROLE_ADDRESSES))


def _balance_payload(address: str, units: int, utxo_count: int, *, source: str, height: int) -> dict[str, Any]:
    return {
        "address": address,
        "units": str(int(units)),
        "acp": _units_to_acp_str(int(units)),
        "utxo_count": int(utxo_count),
        "source": source,
        "chain_height": int(height),
        "indexed": True,
    }


def _aggregate_locked(address: str) -> tuple[int, int]:
    units = 0
    count = 0
    for addr, amt in (_state.get("unspent") or {}).values():
        if addr == address:
            units += int(amt)
            count += 1
    return units, count


def get_indexed_balance(address: str) -> dict[str, Any] | None:
    """Return balance from local/Redis index when watermark > 0; else None."""
    target = (address or "").strip()
    if not target:
        return None
    with _lock:
        wm = int(_state.get("wm") or 0)
        local_n = len(_state.get("unspent") or {})
    if wm <= 0 or local_n == 0:
        _redis_load_sync()
    # Prefer published per-address Redis balance (multi-worker safe, cheap).
    try:
        from app.services.cache import cache_get_json_sync

        cached = cache_get_json_sync(_REDIS_BAL_PREFIX + target)
        if isinstance(cached, dict) and str(cached.get("address") or "").strip() == target:
            # Prefer cached when it has a height at least as fresh as local wm.
            try:
                cached_h = int(cached.get("chain_height") or 0)
            except Exception:
                cached_h = 0
            with _lock:
                local_wm = int(_state.get("wm") or 0)
            if cached_h > 0 and cached_h >= local_wm:
                return dict(cached)
    except Exception:
        report_optional_failure('app.services.acp_utxo_index:get_indexed_balance:fallback', quiet=False)
    with _lock:
        wm = int(_state.get("wm") or 0)
        if wm <= 0 or target not in (_state.get("watch") or set()):
            # A partial index cannot prove zero for an address it never scanned.
            # Let the caller perform its live walletd probe instead.
            return None
        units, count = _aggregate_locked(target)
        return _balance_payload(target, units, count, source="utxo_index", height=wm)


def get_indexed_balance_sync_prefer_redis(address: str) -> dict[str, Any] | None:
    """Sync helper for balance probes: Redis bal key first, then local aggregate."""
    target = (address or "").strip()
    if not target:
        return None
    try:
        from app.services.cache import cache_get_json_sync

        cached = cache_get_json_sync(_REDIS_BAL_PREFIX + target)
        if isinstance(cached, dict) and str(cached.get("address") or "").strip() == target:
            return dict(cached)
    except Exception:
        report_optional_failure('app.services.acp_utxo_index:get_indexed_balance_sync_prefer_redis:fallback', quiet=False)
    return get_indexed_balance(target)


def _redis_load_sync() -> None:
    """Best-effort sync hydrate from Redis (safe to call from withdraw worker threads)."""
    try:
        from app.services.cache import cache_get_json_sync, _redis_sync_module
        from app.config import get_settings
    except Exception:
        return
    settings = get_settings()
    if not settings.redis_url:
        return
    mod = _redis_sync_module()
    if mod is None:
        return
    client = None
    try:
        wm_raw = cache_get_json_sync(_REDIS_WM_KEY)
        wm = 0
        tip_hash: str | None = None
        if isinstance(wm_raw, dict):
            wm = int(wm_raw.get("height") or 0)
            tip_hash = str(wm_raw.get("blockhash") or "").strip() or None
        elif wm_raw is not None:
            try:
                wm = int(wm_raw)
            except Exception:
                wm = 0
        client = mod.from_url(settings.redis_url, decode_responses=True)
        raw_map = client.hgetall(_REDIS_UNSPENT_KEY) or {}
        unspent: dict[str, tuple[str, int]] = {}
        for outpoint, val in raw_map.items():
            try:
                addr, units_s = str(val).split("|", 1)
                unspent[str(outpoint)] = (addr, int(units_s))
            except Exception:
                continue
        with _lock:
            if wm > int(_state.get("wm") or 0) or (wm > 0 and not _state.get("unspent")):
                _state["wm"] = wm
                _state["tip_hash"] = tip_hash
                _state["unspent"] = unspent
    except Exception:
        return
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                report_optional_failure('app.services.acp_utxo_index:_redis_load_sync:client.close', quiet=False)


def list_indexed_utxos(address: str) -> list[dict[str, Any]]:
    """Return indexed unspent outs for address as [{txid,vout,units}, ...] largest-first."""
    target = (address or "").strip()
    if not target:
        return []
    with _lock:
        wm = int(_state.get("wm") or 0)
        local_n = len(_state.get("unspent") or {})
    if wm <= 0 or local_n == 0:
        _redis_load_sync()
    rows: list[tuple[str, int, int]] = []
    with _lock:
        wm = int(_state.get("wm") or 0)
        if wm <= 0:
            return []
        for outpoint, (addr, units) in (_state.get("unspent") or {}).items():
            if addr != target:
                continue
            try:
                txid, vout_s = str(outpoint).rsplit(":", 1)
                vout = int(vout_s)
                rows.append((txid, vout, int(units)))
            except Exception:
                continue
    rows.sort(key=lambda r: r[2], reverse=True)
    return [{"txid": t, "vout": v, "units": u} for t, v, u in rows]


def index_status() -> dict[str, Any]:
    with _lock:
        return {
            "watermark": int(_state.get("wm") or 0),
            "tip_hash": _state.get("tip_hash"),
            "unspent_outs": len(_state.get("unspent") or {}),
            "watch_count": len(_state.get("watch") or {}),
            "catchup_inflight": bool(_state.get("catchup_inflight")),
        }


async def _redis_load() -> None:
    from app.services.cache import cache_get_json, get_redis_client

    wm_raw = await cache_get_json(_REDIS_WM_KEY)
    client = await get_redis_client()
    unspent: dict[str, tuple[str, int]] = {}
    if client is not None:
        try:
            raw_map = await client.hgetall(_REDIS_UNSPENT_KEY)
            for outpoint, val in (raw_map or {}).items():
                try:
                    addr, units_s = str(val).split("|", 1)
                    unspent[str(outpoint)] = (addr, int(units_s))
                except Exception:
                    continue
        finally:
            await client.aclose()
    tip_hash: str | None = None
    wm = int(wm_raw or 0) if not isinstance(wm_raw, dict) else int(wm_raw.get("height") or 0)
    if isinstance(wm_raw, dict):
        wm = int(wm_raw.get("height") or 0)
        tip_hash = str(wm_raw.get("blockhash") or "").strip() or None
    elif wm_raw is not None:
        try:
            wm = int(wm_raw)
        except Exception:
            wm = 0
    with _lock:
        if wm > int(_state.get("wm") or 0) or (wm > 0 and not _state.get("unspent")):
            _state["wm"] = wm
            _state["tip_hash"] = tip_hash
            _state["unspent"] = unspent


async def _redis_save() -> None:
    from app.services.cache import cache_set_json, get_redis_client

    with _lock:
        wm = int(_state.get("wm") or 0)
        tip_hash = str(_state.get("tip_hash") or "").strip() or None
        unspent = dict(_state.get("unspent") or {})
        watch = set(_state.get("watch") or set())

    await cache_set_json(
        _REDIS_WM_KEY,
        {"height": wm, "blockhash": tip_hash},
        ttl_seconds=_REDIS_BAL_TTL_S,
    )
    client = await get_redis_client()
    if client is None:
        return
    try:
        pipe = client.pipeline()
        pipe.delete(_REDIS_UNSPENT_KEY)
        if unspent:
            mapping = {k: f"{addr}|{units}" for k, (addr, units) in unspent.items()}
            pipe.hset(_REDIS_UNSPENT_KEY, mapping=mapping)
        pipe.expire(_REDIS_UNSPENT_KEY, _REDIS_BAL_TTL_S)
        # Publish per-address balances for other workers / fast path.
        for addr in watch | set(OPERATOR_ROLE_ADDRESSES):
            units = 0
            count = 0
            for a, amt in unspent.values():
                if a == addr:
                    units += int(amt)
                    count += 1
            payload = _balance_payload(addr, units, count, source="utxo_index", height=wm)
            pipe.set(_REDIS_BAL_PREFIX + addr, json.dumps(payload), ex=_REDIS_BAL_TTL_S)
        await pipe.execute()
    finally:
        await client.aclose()


async def get_balance_fast(address: str) -> dict[str, Any] | None:
    """Prefer local index, then Redis published balance."""
    local = get_indexed_balance(address)
    if local is not None:
        return local
    from app.services.cache import cache_get_json

    cached = await cache_get_json(_REDIS_BAL_PREFIX + (address or "").strip())
    if isinstance(cached, dict) and cached.get("address"):
        return cached
    return None


def _apply_block(unspent: dict[str, tuple[str, int]], watch: set[str], block: dict) -> None:
    txs = block.get("tx") or []
    for tx in txs:
        txid = str(tx.get("txid") or "")
        if not txid:
            continue
        for vin in tx.get("vin") or []:
            prev_txid = vin.get("prev_txid")
            prev_vout = vin.get("vout")
            if prev_txid is None or prev_vout is None:
                continue
            unspent.pop(f"{prev_txid}:{int(prev_vout)}", None)
        for idx, vout in enumerate(tx.get("vout") or []):
            addr = str(vout.get("recipient_address") or "").strip()
            if not addr or addr not in watch:
                continue
            units = _amount_to_units(vout.get("amount"))
            if units <= 0:
                continue
            unspent[f"{txid}:{idx}"] = (addr, units)


def advance_index_sync(*, chunk: int = _CHUNK_DEFAULT) -> dict[str, Any]:
    """Scan up to `chunk` new blocks into the local unspent map. Sync (jobs/thread)."""
    # Always hydrate from Redis first so a cold worker does not restart from height 0
    # and clobber a healthy shared watermark on the next save.
    with _lock:
        wm0 = int(_state.get("wm") or 0)
        n0 = len(_state.get("unspent") or {})
    if wm0 <= 0 or n0 == 0:
        _redis_load_sync()

    rpc_url = _require_rpc_url()
    tip = int(_rpc(rpc_url, "getblockcount", []) or 0)
    if tip <= 0:
        return {"ok": False, "error": "tip_unavailable", "tip": tip}

    with _lock:
        wm = int(_state.get("wm") or 0)
        checkpoint_hash = str(_state.get("tip_hash") or "").strip() or None
        unspent = dict(_state.get("unspent") or {})
        watch = set(_state.get("watch") or set(OPERATOR_ROLE_ADDRESSES))

    if not watch:
        watch = set(OPERATOR_ROLE_ADDRESSES)

    # A numeric height alone cannot identify a chain. Reset on regenesis/reorg,
    # and rebuild once for legacy Redis watermarks that had no block hash.
    reset_reason: str | None = None
    if wm > tip:
        reset_reason = "tip_behind_watermark"
    elif wm > 0 and not checkpoint_hash:
        reset_reason = "checkpoint_hash_missing"
    elif wm > 0:
        live_checkpoint = str(_rpc(rpc_url, "getblockhash", {"height": wm}) or "")
        if live_checkpoint != checkpoint_hash:
            reset_reason = "checkpoint_hash_mismatch"
    if reset_reason:
        logger.warning("acp_utxo_index reset: %s", reset_reason)
        wm = 0
        checkpoint_hash = None
        unspent = {}

    start = wm + 1
    if start > tip:
        return {
            "ok": True,
            "tip": tip,
            "watermark": wm,
            "tip_hash": checkpoint_hash,
            "scanned": 0,
            "caught_up": True,
        }

    end = min(tip, wm + max(1, int(chunk)))
    scanned = 0
    for height in range(start, end + 1):
        bh = _rpc(rpc_url, "getblockhash", {"height": height})
        block = _rpc(rpc_url, "getblock", {"blockhash": bh, "verbose": 2}) or {}
        _apply_block(unspent, watch, block)
        scanned += 1
        wm = height
        checkpoint_hash = str(bh)

    with _lock:
        _state["wm"] = wm
        _state["tip_hash"] = checkpoint_hash
        _state["unspent"] = unspent
        _state["watch"] = watch

    return {
        "ok": True,
        "tip": tip,
        "watermark": wm,
        "tip_hash": checkpoint_hash,
        "scanned": scanned,
        "caught_up": wm >= tip,
        "unspent_outs": len(unspent),
        "watch_count": len(watch),
    }


async def acp_utxo_index_tick(
    *,
    extra_addresses: list[str] | None = None,
    chunk: int = _CHUNK_DEFAULT,
    max_chunks: int = 3,
) -> dict[str, Any]:
    """Advance the UTXO index and publish balances. Called from jobs/tick."""
    try:
        await _redis_load()
    except Exception as exc:
        logger.warning("acp_utxo_index redis load failed: %s", exc)

    watch = set(OPERATOR_ROLE_ADDRESSES)
    if extra_addresses:
        watch |= {str(a).strip() for a in extra_addresses if str(a or "").strip()}
    set_watch_addresses(watch)

    summary = {"chunks": [], "ok": True}
    caught_up = False
    try:
        for _ in range(max(1, int(max_chunks))):
            step = advance_index_sync(chunk=chunk)
            summary["chunks"].append(step)
            if not step.get("ok"):
                summary["ok"] = False
                break
            if step.get("caught_up"):
                caught_up = True
                break
        await _redis_save()
    except Exception as exc:
        logger.warning("acp_utxo_index tick failed: %s", exc)
        summary["ok"] = False
        summary["error"] = str(exc)[:200]
    summary["caught_up"] = caught_up
    summary["status"] = index_status()
    return summary


def _catchup_loop() -> None:
    try:
        # Best-effort bootstrap without Redis await in a plain thread:
        # keep scanning until caught up or too many errors.
        errors = 0
        while errors < 8:
            try:
                step = advance_index_sync(chunk=_CHUNK_DEFAULT)
            except Exception as exc:
                errors += 1
                logger.warning("acp_utxo_index catchup error: %s", exc)
                time.sleep(2.0)
                continue
            if not step.get("ok"):
                errors += 1
                time.sleep(2.0)
                continue
            errors = 0
            if step.get("caught_up"):
                break
            # Yield briefly so request threads stay responsive.
            time.sleep(0.05)
        # Persist via a short-lived event loop if possible.
        try:
            import asyncio

            asyncio.run(_redis_save())
        except Exception:
            report_optional_failure('app.services.acp_utxo_index:_catchup_loop:fallback', quiet=False)
    finally:
        with _lock:
            _state["catchup_inflight"] = False


def schedule_utxo_index_catchup() -> bool:
    with _lock:
        if _state.get("catchup_inflight"):
            return False
        _state["catchup_inflight"] = True
    threading.Thread(target=_catchup_loop, name="acp-utxo-index-catchup", daemon=True).start()
    return True


def seed_from_out_index(
    out_index: dict[tuple[str, int], tuple[str, int]],
    *,
    height: int,
) -> None:
    """Optional bridge: hydrate from wallet_acp chain-scan out_index when warm."""
    if height <= 0 or not out_index:
        return
    watch = watched_addresses()
    unspent: dict[str, tuple[str, int]] = {}
    for (txid, vout), (addr, units) in out_index.items():
        if addr in watch and int(units) > 0:
            unspent[f"{txid}:{int(vout)}"] = (str(addr), int(units))
    with _lock:
        if height >= int(_state.get("wm") or 0):
            _state["wm"] = int(height)
            _state["tip_hash"] = None
            _state["unspent"] = unspent
