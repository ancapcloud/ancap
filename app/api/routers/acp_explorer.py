"""Public ACP chain explorer API (Blockchair-style read surface)."""
from __future__ import annotations
from app.services.recoverable_errors import report_optional_failure

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession
from app.schemas.acp_explorer import (
    ExplorerAddressEvent,
    ExplorerAddressResponse,
    ExplorerBlockDetailResponse,
    ExplorerBlockSummary,
    ExplorerBlocksResponse,
    ExplorerMempoolResponse,
    ExplorerSearchResponse,
    ExplorerStatsResponse,
    ExplorerTxIo,
    ExplorerTxResponse,
    ExplorerUtxoItem,
)
from app.services.acp_amounts import rpc_amount_units
from app.services.acp_explorer_index import (
    address_history,
    explorer_index_status,
    units_to_acp_str,
)
from app.services.acp_explorer_search import classify_explorer_query
from app.services.acp_rpc import acp_rpc_call
from app.services.acp_tokenomics import OPERATOR_ROLE_WALLETS, _address_balance_acp

router = APIRouter(prefix="/acp/explorer", tags=["ACP Explorer"])

_ROLE_BY_ADDR = {addr: (key, label) for key, label, addr, _ in OPERATOR_ROLE_WALLETS}


def _units_str(units: int) -> str:
    return str(int(units))


async def _lean_status() -> dict[str, Any]:
    try:
        height = await acp_rpc_call("getblockcount", [])
        best_hash = await acp_rpc_call("getbestblockhash", [])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    lean = {
        "protocol_profile": "lean-v1.4",
        "energy_model": "ultra-light-assembler",
        "signing_security": "hybrid-ed25519-dilithium2",
        "encryption_security": "xwing-draft10-ml-kem-768-x25519-hkdf-sha256-xchacha20poly1305-v1",
        "encryption_status": "experimental-off-chain-envelope",
        "privacy_profile": "unlinkable-subaddr-v1",
        "target_block_time_sec": 5,
        "max_block_bytes": 2 * 1024 * 1024,
        "design_tps_hint": 102,
        "pow": False,
    }
    try:
        net = await acp_rpc_call("getnetworkinfo", [])
        if isinstance(net, dict):
            for key in (
                "protocol_profile",
                "energy_model",
                "signing_security",
                "encryption_security",
                "encryption_status",
                "privacy_profile",
                "target_block_time_sec",
                "max_block_bytes",
                "max_txs_per_block",
                "design_tps_hint",
                "miner_interval_secs",
                "miner_heartbeat_enabled",
                "pow",
                "mempool_size",
                "version",
            ):
                if key in net:
                    lean[key] = net[key]
    except RuntimeError:
        report_optional_failure('app.api.routers.acp_explorer:_lean_status:60', quiet=True)
    return {
        "status": "ok",
        "chain_id": 1001,
        "block_height": int(height or 0),
        "best_block_hash": best_hash,
        "lean": lean,
    }


@router.get("/status")
async def explorer_status():
    return await _lean_status()


@router.get("/efficiency")
async def explorer_efficiency():
    status = await _lean_status()
    lean = status.get("lean") if isinstance(status, dict) else {}
    mempool = None
    try:
        mempool = await acp_rpc_call("getmempoolinfo", [])
    except RuntimeError:
        mempool = None
    return {
        "status": "ok",
        "block_height": status.get("block_height"),
        "lean": lean,
        "mempool": mempool,
        "market_alignment_2026": {
            "security": [
                "Hybrid Ed25519 + Dilithium2 signatures (post-quantum ready)",
                (
                    "X-Wing draft-10 (X25519 + FIPS 203 ML-KEM-768) off-chain envelopes "
                    "(experimental; independent review pending)"
                ),
                "No PoW hash race / ASIC arms race attack surface",
                "Fee floor + packed-block anti-spam",
            ],
            "speed": [
                "Target 5s block cadence (aligned miner interval)",
                "Fee-prioritized multi-tx packing up to 512 txs / 2 MB",
                "Design capacity hint ~100 TPS under full packs",
            ],
            "energy": [
                "Ultra-light assembler (orders of magnitude below Bitcoin PoW)",
                "Idle heartbeat throttled (~60s) — no continuous hash burn",
                "Comparable philosophy to post-Merge PoS efficiency without heavy validator re-execution yet",
            ],
            "privacy": [
                "Unlinkable receive subaddresses (never reuse recommended)",
                "Explorer/wallet redaction by default",
                "Transparent ledger honesty: amounts still auditable by full nodes — not a mixer",
            ],
            "vs_peers_note": (
                "Ethereum focuses L1 zkEVM / energy-efficient PoS; Solana optimizes monolithic TPS; "
                "privacy coins hide amounts. ACP Lean targets AI-workflow settlement: PQC-ready security, "
                "low energy, packed throughput, unlinkable receives."
            ),
        },
    }


@router.get("/search", response_model=ExplorerSearchResponse)
async def explorer_search(q: str = Query(..., min_length=1, max_length=256)):
    classified = classify_explorer_query(q)
    if classified["type"] != "tx":
        return ExplorerSearchResponse(**classified)

    txid = str(classified["id"] or "").lower()
    # Prefer live tx; fallback to block hash
    try:
        await acp_rpc_call("getrawtransaction", {"txid": txid, "verbose": 1})
        return ExplorerSearchResponse(**classified)
    except RuntimeError:
        report_optional_failure('app.api.routers.acp_explorer:explorer_search:154', quiet=True)
    try:
        block = await acp_rpc_call("getblock", {"blockhash": txid, "verbose": True})
        height = None
        if isinstance(block, dict):
            height = block.get("height")
            if height is None and isinstance(block.get("header"), dict):
                height = block["header"].get("height")
        return ExplorerSearchResponse(
            query=q,
            type="block_hash",
            id=txid,
            canonical_path=f"/explorer/block/{txid}",
            notes=[f"resolved as block hash (height={height})"],
        )
    except RuntimeError:
        return ExplorerSearchResponse(
            query=q,
            type="unknown",
            id=txid,
            canonical_path=None,
            notes=["hex64 matched neither tx nor block"],
        )


@router.get("/blocks", response_model=ExplorerBlocksResponse)
async def list_blocks(
    limit: int = Query(default=12, ge=1, le=100),
    before_height: int | None = Query(default=None, ge=0),
):
    try:
        tip = int(await acp_rpc_call("getblockcount", []) or 0)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    start = tip if before_height is None else min(tip, before_height)
    items: list[ExplorerBlockSummary] = []
    for h in range(start, max(-1, start - limit), -1):
        if h < 0:
            break
        try:
            block_hash = await acp_rpc_call("getblockhash", {"height": h})
            block = await acp_rpc_call("getblock", {"blockhash": block_hash, "verbose": True}) or {}
            tx_list = block.get("tx", []) if isinstance(block, dict) else []
            header = block.get("header") if isinstance(block.get("header"), dict) else {}
            time_v = header.get("time") or block.get("time")
            size_v = block.get("size") or block.get("bytes")
            items.append(
                ExplorerBlockSummary(
                    height=h,
                    hash=str(block_hash) if block_hash else None,
                    tx_count=len(tx_list),
                    time=int(time_v) if time_v is not None else None,
                    size=int(size_v) if size_v is not None else None,
                )
            )
        except (RuntimeError, TypeError, ValueError):
            items.append(ExplorerBlockSummary(height=h, hash=None, tx_count=0))
    next_before = None
    if items:
        lowest = items[-1].height
        if lowest > 0:
            next_before = lowest - 1
    return ExplorerBlocksResponse(block_height=tip, items=items, next_before_height=next_before)


async def _resolve_block_id(block_id: str) -> tuple[int, str, dict]:
    raw = (block_id or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="block id required")
    try:
        if raw.isdigit():
            height = int(raw)
            block_hash = str(await acp_rpc_call("getblockhash", {"height": height}) or "")
        else:
            block_hash = raw.lower()
            height = -1
        block = await acp_rpc_call("getblock", {"blockhash": block_hash, "verbose": 2}) or {}
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not isinstance(block, dict):
        raise HTTPException(status_code=404, detail="block not found")
    header = block.get("header") if isinstance(block.get("header"), dict) else {}
    if height < 0:
        try:
            height = int(block.get("height") if block.get("height") is not None else header.get("height") or -1)
        except (TypeError, ValueError):
            height = -1
    if height < 0:
        raise HTTPException(status_code=404, detail="block height unknown")
    return height, block_hash, block


@router.get("/block/{block_id}", response_model=ExplorerBlockDetailResponse)
async def get_block(block_id: str):
    height, block_hash, block = await _resolve_block_id(block_id)
    header = block.get("header") if isinstance(block.get("header"), dict) else {}
    tx_raw = block.get("tx") or []
    txids: list[str] = []
    for item in tx_raw:
        if isinstance(item, str):
            txids.append(item.lower())
        elif isinstance(item, dict) and item.get("txid"):
            txids.append(str(item["txid"]).lower())
    prev_hash = header.get("prev_hash") or header.get("previousblockhash") or block.get("previousblockhash")
    next_hash = None
    try:
        tip = int(await acp_rpc_call("getblockcount", []) or 0)
        if height < tip:
            next_hash = await acp_rpc_call("getblockhash", {"height": height + 1})
    except RuntimeError:
        # An unavailable tip means the next block is unknown, not the current height.
        next_hash = None
    time_v = header.get("time") or block.get("time")
    size_v = block.get("size") or block.get("bytes")
    return ExplorerBlockDetailResponse(
        height=height,
        hash=block_hash,
        previous_hash=str(prev_hash) if prev_hash else None,
        next_hash=str(next_hash) if next_hash else None,
        time=int(time_v) if time_v is not None else None,
        size=int(size_v) if size_v is not None else None,
        tx_count=len(txids),
        txids=txids,
        header={k: header[k] for k in list(header)[:40]} if header else {},
    )


def _io_from_wallet_style(item: dict) -> ExplorerTxIo:
    units = int(item.get("units") or 0)
    return ExplorerTxIo(
        address=item.get("address"),
        units=_units_str(units),
        acp=units_to_acp_str(units),
        vout=int(item["vout"]) if item.get("vout") is not None else None,
    )


@router.get("/tx/{txid}", response_model=ExplorerTxResponse)
async def get_transaction(txid: str, view: str = Query(default="full")):
    txid_norm = (txid or "").strip().lower()
    if len(txid_norm) < 16:
        raise HTTPException(status_code=400, detail="txid looks invalid")
    mode = (view or "full").strip().lower()

    # Prefer structured wallet chain scan (includes block linkage)
    try:
        from app.api.routers.wallet_acp import _chain_transaction_details

        details = _chain_transaction_details(txid_norm)
    except Exception:
        details = None

    if details is not None:
        payload = details.model_dump() if hasattr(details, "model_dump") else dict(details)
        if mode in ("redacted", "privacy", "summary"):
            from app.services import acp_privacy as privacy_svc

            for io in payload.get("inputs") or []:
                if isinstance(io, dict) and io.get("address"):
                    io["address"] = privacy_svc.redact_address(str(io["address"]))
            for io in payload.get("outputs") or []:
                if isinstance(io, dict) and io.get("address"):
                    io["address"] = privacy_svc.redact_address(str(io["address"]))
            return ExplorerTxResponse(
                txid=txid_norm,
                view="redacted",
                status="confirmed" if int(payload.get("confirmations") or 0) > 0 else "unknown",
                block_height=payload.get("block_height"),
                block_hash=payload.get("block_hash"),
                block_time=payload.get("block_time"),
                confirmations=int(payload.get("confirmations") or 0),
                total_input_units=str(payload.get("total_input_units")),
                total_input_acp=str(payload.get("total_input_acp")),
                total_output_units=str(payload.get("total_output_units")),
                total_output_acp=str(payload.get("total_output_acp")),
                fee_units=str(payload.get("fee_units")),
                fee_acp=str(payload.get("fee_acp")),
                inputs=[_io_from_wallet_style(x) for x in (payload.get("inputs") or []) if isinstance(x, dict)],
                outputs=[_io_from_wallet_style(x) for x in (payload.get("outputs") or []) if isinstance(x, dict)],
                privacy_profile=privacy_svc.PRIVACY_PROFILE,
                hint="Pass ?view=full for unredacted addresses.",
            )
        return ExplorerTxResponse(
            txid=txid_norm,
            view="full",
            status="confirmed" if int(payload.get("confirmations") or 0) > 0 else "unknown",
            block_height=payload.get("block_height"),
            block_hash=payload.get("block_hash"),
            block_time=payload.get("block_time"),
            confirmations=int(payload.get("confirmations") or 0),
            total_input_units=str(payload.get("total_input_units")),
            total_input_acp=str(payload.get("total_input_acp")),
            total_output_units=str(payload.get("total_output_units")),
            total_output_acp=str(payload.get("total_output_acp")),
            fee_units=str(payload.get("fee_units")),
            fee_acp=str(payload.get("fee_acp")),
            inputs=[_io_from_wallet_style(x) for x in (payload.get("inputs") or []) if isinstance(x, dict)],
            outputs=[_io_from_wallet_style(x) for x in (payload.get("outputs") or []) if isinstance(x, dict)],
        )

    # Fallback: raw RPC (+ mempool)
    try:
        tx = await acp_rpc_call("getrawtransaction", {"txid": txid_norm, "verbose": 1})
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    decoded = tx.get("decoded") if isinstance(tx, dict) else None
    body = decoded if isinstance(decoded, dict) else (tx if isinstance(tx, dict) else {})
    inputs = []
    outputs = []
    out_units = 0
    for idx, vout in enumerate(body.get("vout") or []):
        if not isinstance(vout, dict):
            continue
        amt = rpc_amount_units(vout.get("amount"))
        out_units += amt
        outputs.append(
            ExplorerTxIo(
                address=str(vout.get("recipient_address") or "") or None,
                units=_units_str(amt),
                acp=units_to_acp_str(amt),
                vout=idx,
            )
        )
    if mode in ("redacted", "privacy", "summary"):
        from app.services.acp_privacy import explorer_tx_redacted, PRIVACY_PROFILE

        return ExplorerTxResponse(
            txid=txid_norm,
            view="redacted",
            status="mempool",
            inputs=inputs,
            outputs=outputs,
            total_output_units=_units_str(out_units),
            total_output_acp=units_to_acp_str(out_units),
            privacy_profile=PRIVACY_PROFILE,
            summary=explorer_tx_redacted(body),
            hint="Pass ?view=full to reveal decoded wire.",
        )
    return ExplorerTxResponse(
        txid=txid_norm,
        view="full",
        status="mempool",
        inputs=inputs,
        outputs=outputs,
        total_output_units=_units_str(out_units),
        total_output_acp=units_to_acp_str(out_units),
        transaction=body,
    )


@router.get("/tokenomics/snapshot")
async def tokenomics_snapshot():
    try:
        from app.services.acp_tokenomics import build_tokenomics_snapshot

        return await build_tokenomics_snapshot()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/supply-layout")
async def supply_layout():
    from app.services.acp_tokenomics import acp_supply_layout

    return {"status": "ok", **acp_supply_layout()}


@router.get("/address/{address}", response_model=ExplorerAddressResponse)
async def get_address_summary(
    address: str,
    session: DbSession,
    history_limit: int = Query(default=50, ge=0, le=100),
    history_offset: int = Query(default=0, ge=0),
):
    target = address.strip()
    if not target:
        raise HTTPException(status_code=400, detail="address is required")
    try:
        balance, utxo_count = await _address_balance_acp(target)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    role = _ROLE_BY_ADDR.get(target)
    utxos: list[ExplorerUtxoItem] = []
    try:
        from app.services.acp_utxo_index import list_indexed_utxos

        for item in list_indexed_utxos(target)[:100]:
            units = int(item.get("units") or 0)
            utxos.append(
                ExplorerUtxoItem(
                    txid=str(item.get("txid") or ""),
                    vout=int(item.get("vout") or 0),
                    units=_units_str(units),
                    acp=units_to_acp_str(units),
                    height=item.get("height"),
                )
            )
    except Exception:
        utxos = []

    history_rows: list[ExplorerAddressEvent] = []
    history_total = 0
    index_height = None
    try:
        rows, history_total = await address_history(
            session, target, limit=history_limit or 50, offset=history_offset
        )
        history_rows = [ExplorerAddressEvent(**r) for r in rows]
        st = await explorer_index_status(session)
        index_height = st.get("last_scanned_height")
    except Exception:
        history_rows = []
        history_total = 0

    next_offset = None
    if history_offset + len(history_rows) < history_total:
        next_offset = history_offset + len(history_rows)

    bal_units = int((balance * Decimal(100_000_000)).to_integral_value())
    return ExplorerAddressResponse(
        address=target,
        balance_acp=format(balance.quantize(Decimal("0.00000001")), "f").rstrip("0").rstrip(".") or "0",
        balance_units=_units_str(bal_units),
        utxo_count=utxo_count,
        role_key=role[0] if role else None,
        role_label=role[1] if role else None,
        utxos=utxos,
        history=history_rows,
        history_total=history_total,
        next_offset=next_offset,
        index_height=index_height,
    )


@router.get("/mempool", response_model=ExplorerMempoolResponse)
async def explorer_mempool():
    info: dict[str, Any] = {}
    txids: list[str] = []
    fee_estimate = None
    try:
        raw_info = await acp_rpc_call("getmempoolinfo", [])
        if isinstance(raw_info, dict):
            info = raw_info
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    try:
        raw = await acp_rpc_call("getrawmempool", [])
        if isinstance(raw, list):
            txids = [str(x).lower() for x in raw[:200]]
        elif isinstance(raw, dict):
            txids = [str(k).lower() for k in list(raw.keys())[:200]]
    except RuntimeError:
        txids = []
    try:
        fee_estimate = await acp_rpc_call("getfeeestimate", [])
        if not isinstance(fee_estimate, dict):
            fee_estimate = {"raw": fee_estimate}
    except RuntimeError:
        fee_estimate = None
    return ExplorerMempoolResponse(info=info, txids=txids, fee_estimate=fee_estimate)


@router.get("/stats", response_model=ExplorerStatsResponse)
async def explorer_stats(session: DbSession):
    status = await _lean_status()
    txoutset = None
    try:
        txoutset = await acp_rpc_call("gettxoutsetinfo", [])
    except RuntimeError:
        txoutset = None
    tokenomics = None
    try:
        from app.services.acp_tokenomics import build_tokenomics_snapshot

        snap = await build_tokenomics_snapshot()
        tokenomics = snap.model_dump() if hasattr(snap, "model_dump") else dict(snap)
    except Exception:
        tokenomics = None
    free_dist = None
    try:
        from app.services.free_distribution import free_distribution_status

        free_dist = await free_distribution_status(session)
    except Exception:
        free_dist = None
    try:
        index = await explorer_index_status(session)
    except Exception as exc:
        index = {"error": str(exc)[:200]}
    return ExplorerStatsResponse(
        status="ok",
        chain={
            "chain_id": status.get("chain_id"),
            "block_height": status.get("block_height"),
            "best_block_hash": status.get("best_block_hash"),
        },
        txoutset=txoutset if isinstance(txoutset, dict) else None,
        tokenomics=tokenomics,
        free_distribution=free_dist,
        index=index,
        lean=status.get("lean"),
    )
