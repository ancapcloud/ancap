"""sACP (Stable ACP) status, intents, reserve snapshots — docs/STABLECOIN_SACP_SPEC.md."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import SacpOperation, SacpReserveSnapshot

_Q = Decimal("0.00000001")
_ACP_DECIMALS = 8
_SACP_DECIMALS = 18


def _api_str(v: Decimal) -> str:
    s = format(v.quantize(_Q, rounding=ROUND_HALF_UP), "f").rstrip("0").rstrip(".")
    return s or "0"


def _dec(raw: str, field: str) -> Decimal:
    try:
        v = Decimal(str(raw).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise HTTPException(status_code=400, detail=f"{field} must be a decimal string") from exc
    if v <= 0:
        raise HTTPException(status_code=400, detail=f"{field} must be > 0")
    return v


def _acp_per_usd() -> Decimal:
    settings = get_settings()
    return Decimal(str(getattr(settings, "sacp_acp_per_usd", None) or "4"))


def _min_ratio() -> Decimal:
    settings = get_settings()
    return Decimal(str(getattr(settings, "sacp_min_collateral_ratio", None) or "1.50"))


def acp_per_usd() -> Decimal:
    return _acp_per_usd()


def min_collateral_ratio() -> Decimal:
    return _min_ratio()


def is_enabled() -> bool:
    settings = get_settings()
    return bool(getattr(settings, "ff_sacp", True))


def is_paused() -> bool:
    settings = get_settings()
    return bool(getattr(settings, "sacp_paused", False))


def _require_live() -> None:
    if not is_enabled():
        raise HTTPException(status_code=503, detail="sACP is disabled")
    if is_paused():
        raise HTTPException(status_code=503, detail="sACP is paused")


def indicative_acp_for_sacp(sacp_amount: Decimal) -> Decimal:
    return (sacp_amount * _acp_per_usd() * _min_ratio()).quantize(_Q, rounding=ROUND_HALF_UP)


def indicative_sacp_for_acp(acp_amount: Decimal) -> Decimal:
    denom = _acp_per_usd() * _min_ratio()
    if denom <= 0:
        return Decimal("0")
    return (acp_amount / denom).quantize(_Q, rounding=ROUND_HALF_UP)


def _to_smallest_acp(acp: Decimal) -> int:
    return int((acp * Decimal(10**_ACP_DECIMALS)).to_integral_value(rounding=ROUND_HALF_UP))


def _to_wei_sacp(sacp: Decimal) -> int:
    return int((sacp * Decimal(10**_SACP_DECIMALS)).to_integral_value(rounding=ROUND_HALF_UP))


def _from_smallest_acp(smallest: Decimal | int) -> Decimal:
    return Decimal(smallest) / Decimal(10**_ACP_DECIMALS)


def _from_wei_sacp(wei: Decimal | int) -> Decimal:
    return Decimal(wei) / Decimal(10**_SACP_DECIMALS)


def public_status() -> dict:
    settings = get_settings()
    enabled = is_enabled()
    paused = is_paused()
    contract = (getattr(settings, "sacp_contract", None) or "").strip()
    gateway = (getattr(settings, "sacp_gateway_contract", None) or "").strip()
    reserve = (getattr(settings, "sacp_reserve_acp_address", None) or "").strip()
    notes: list[str] = [
        "sACP is USD-targeted and ACP-collateralized. It is not a guaranteed fiat redemption.",
        "Distinct from wACP (1 ACP ↔ 10 wACP wrap) and from partner USDC/USDT ramps.",
    ]
    if not contract:
        notes.append("Production sACP contract is not configured yet — set SACP_CONTRACT after DeploySacp.s.sol.")
    redeem_available = enabled and not paused
    mint_available = redeem_available and not settings.external_token_racp_only
    return {
        "status": "ok" if enabled else "disabled",
        "enabled": enabled,
        "paused": paused,
        "mint_available": mint_available,
        "redeem_available": redeem_available,
        "peg_target": "USD",
        "peg_note": (
            f"Target 1 sACP ≈ 1 USD; indicative {_api_str(_acp_per_usd())} ACP per USD "
            f"at min collateral ratio {_api_str(_min_ratio())}."
        ),
        "sacp_contract": contract,
        "gateway_contract": gateway,
        "reserve_acp_address": reserve,
        "acp_per_usd": _api_str(_acp_per_usd()),
        "min_collateral_ratio": _api_str(_min_ratio()),
        "decimals": 18,
        "network": "bsc",
        "bsc_explorer_base": getattr(settings, "bsc_explorer_base", None) or "https://bscscan.com",
        "docs_url": "/docs/sacp",
        "last_updated_at": datetime.now(timezone.utc),
        "notes": notes,
    }


async def latest_snapshot(session: AsyncSession | None) -> SacpReserveSnapshot | None:
    if session is None:
        return None
    result = await session.execute(
        select(SacpReserveSnapshot).order_by(SacpReserveSnapshot.snapshot_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def reserve_proof(session: AsyncSession | None = None) -> dict:
    settings = get_settings()
    enabled = is_enabled()
    paused = is_paused()
    contract = (getattr(settings, "sacp_contract", None) or "").strip()
    reserve = (getattr(settings, "sacp_reserve_acp_address", None) or "").strip()
    rate = _acp_per_usd()
    ratio_min = _min_ratio()
    snap = await latest_snapshot(session) if session is not None else None

    if snap is not None:
        reserve_smallest = Decimal(str(snap.reserve_balance_acp_smallest or 0))
        supply_wei = Decimal(str(snap.sacp_total_supply_wei or 0))
        health = snap.reserve_health or "unknown"
        notes = list(snap.notes or [])
        last_updated = snap.snapshot_at
        implied = snap.implied_collateral_usd
        required = snap.required_collateral_usd
        coll_ratio = snap.collateral_ratio
    else:
        reserve_smallest = Decimal("0")
        supply_wei = Decimal("0")
        health = "not_configured" if not contract else "ok"
        notes = [
            "No sacp_reserve_snapshots yet — POST /v1/sacp/admin/snapshots after deploy/indexer.",
        ]
        last_updated = datetime.now(timezone.utc)
        implied = None
        required = None
        coll_ratio = None

    circulating = _from_wei_sacp(supply_wei)
    acp_balance = _from_smallest_acp(reserve_smallest)
    if implied is None and rate > 0:
        implied = acp_balance / rate
    if required is None:
        required = circulating * ratio_min
    if coll_ratio is None and circulating > 0 and implied is not None:
        coll_ratio = Decimal(str(implied)) / circulating

    if not enabled:
        health = "disabled"
    elif paused:
        health = "paused"

    return {
        "status": "ok" if enabled else "disabled",
        "enabled": enabled,
        "paused": paused,
        "peg_target": "USD",
        "sacp_contract": contract,
        "reserve_acp_address": reserve,
        "acp_reserve_balance_smallest": str(int(reserve_smallest)),
        "acp_reserve_balance_acp": _api_str(acp_balance),
        "sacp_total_supply_wei": str(int(supply_wei)),
        "sacp_circulating": _api_str(circulating),
        "acp_per_usd": _api_str(rate),
        "min_collateral_ratio": _api_str(ratio_min),
        "implied_collateral_usd": _api_str(Decimal(str(implied))) if implied is not None else None,
        "required_collateral_usd": _api_str(Decimal(str(required))) if required is not None else None,
        "collateral_ratio": _api_str(Decimal(str(coll_ratio))) if coll_ratio is not None else None,
        "reserve_health": health,
        "last_updated_at": last_updated,
        "notes": notes,
    }


def serialize_operation(op: SacpOperation) -> dict:
    return {
        "id": str(op.id),
        "direction": op.direction,
        "status": op.status,
        "user_bsc_address": op.user_bsc_address,
        "user_acp_address": op.user_acp_address,
        "amount_acp": _api_str(_from_smallest_acp(op.amount_acp_smallest or 0)),
        "amount_sacp": _api_str(_from_wei_sacp(op.amount_sacp_wei or 0)),
        "acp_per_usd": _api_str(Decimal(str(op.acp_per_usd))),
        "min_collateral_ratio": _api_str(Decimal(str(op.min_collateral_ratio))),
        "acp_tx_hash": op.acp_tx_hash,
        "bsc_tx_hash": op.bsc_tx_hash,
        "collateral_ref_hex": op.collateral_ref_hex,
        "correlation_id": op.correlation_id,
        "notes": list(op.notes or []),
        "created_at": op.created_at,
        "updated_at": op.updated_at,
    }


async def create_mint_intent(
    session: AsyncSession,
    *,
    acp_amount: str,
    user_bsc_address: str,
    user_id: str | None = None,
    correlation_id: str | None = None,
) -> SacpOperation:
    if get_settings().external_token_racp_only:
        raise HTTPException(status_code=409, detail="New BSC sACP issuance is closed; rACP is the primary external token. Existing sACP redemption is separate.")
    _require_live()
    acp = _dec(acp_amount, "acp_amount")
    sacp = indicative_sacp_for_acp(acp)
    if sacp <= 0:
        raise HTTPException(status_code=400, detail="acp_amount too small for min collateral ratio")
    op = SacpOperation(
        id=str(uuid4()),
        user_id=user_id,
        direction="mint",
        status="AWAITING_COLLATERAL",
        user_bsc_address=user_bsc_address.strip(),
        amount_acp_smallest=_to_smallest_acp(acp),
        amount_sacp_wei=_to_wei_sacp(sacp),
        acp_per_usd=_acp_per_usd(),
        min_collateral_ratio=_min_ratio(),
        correlation_id=correlation_id,
        notes=[
            "Lock ACP collateral to reserve, then operator mints sACP via SacpGateway.mintStable.",
        ],
    )
    session.add(op)
    await session.flush()
    return op


async def create_redeem_intent(
    session: AsyncSession,
    *,
    sacp_amount: str,
    user_acp_address: str,
    user_id: str | None = None,
    correlation_id: str | None = None,
) -> SacpOperation:
    _require_live()
    sacp = _dec(sacp_amount, "sacp_amount")
    acp = indicative_acp_for_sacp(sacp)
    op = SacpOperation(
        id=str(uuid4()),
        user_id=user_id,
        direction="redeem",
        status="AWAITING_BURN",
        user_acp_address=user_acp_address.strip(),
        amount_acp_smallest=_to_smallest_acp(acp),
        amount_sacp_wei=_to_wei_sacp(sacp),
        acp_per_usd=_acp_per_usd(),
        min_collateral_ratio=_min_ratio(),
        correlation_id=correlation_id,
        notes=[
            "Burn sACP via SacpGateway.requestRedeem; operator unlocks ACP collateral after event.",
        ],
    )
    session.add(op)
    await session.flush()
    return op


async def get_operation(session: AsyncSession, operation_id: str) -> SacpOperation:
    op = await session.get(SacpOperation, operation_id)
    if op is None:
        raise HTTPException(status_code=404, detail="sACP operation not found")
    return op


async def admin_bind(
    session: AsyncSession,
    operation_id: str,
    *,
    acp_tx_hash: str | None = None,
    bsc_tx_hash: str | None = None,
    collateral_ref_hex: str | None = None,
    note: str | None = None,
) -> SacpOperation:
    op = await get_operation(session, operation_id)
    if acp_tx_hash:
        op.acp_tx_hash = acp_tx_hash.strip()
    if bsc_tx_hash:
        op.bsc_tx_hash = bsc_tx_hash.strip()
    if collateral_ref_hex:
        op.collateral_ref_hex = collateral_ref_hex.strip()
    notes = list(op.notes or [])
    if note:
        notes.append(note)
    op.notes = notes
    if op.direction == "mint":
        if op.acp_tx_hash and op.status == "AWAITING_COLLATERAL":
            op.status = "READY_TO_MINT"
        if op.bsc_tx_hash and op.status in {"READY_TO_MINT", "AWAITING_COLLATERAL"}:
            op.status = "COMPLETED"
    else:
        if op.bsc_tx_hash and op.status == "AWAITING_BURN":
            op.status = "READY_TO_PAYOUT"
        if op.acp_tx_hash and op.status in {"READY_TO_PAYOUT", "AWAITING_BURN"}:
            op.status = "COMPLETED"
    op.updated_at = datetime.now(timezone.utc)
    await session.flush()
    return op


async def record_snapshot(
    session: AsyncSession,
    *,
    reserve_balance_acp_smallest: str = "0",
    sacp_total_supply_wei: str = "0",
    notes: list[str] | None = None,
) -> SacpReserveSnapshot:
    settings = get_settings()
    reserve_smallest = Decimal(str(reserve_balance_acp_smallest or "0"))
    supply_wei = Decimal(str(sacp_total_supply_wei or "0"))
    rate = _acp_per_usd()
    ratio_min = _min_ratio()
    acp_balance = _from_smallest_acp(reserve_smallest)
    circulating = _from_wei_sacp(supply_wei)
    implied = (acp_balance / rate) if rate > 0 else Decimal("0")
    required = circulating * ratio_min
    coll_ratio = (implied / circulating) if circulating > 0 else None
    if circulating == 0:
        health = "ok"
        ok = True
    elif coll_ratio is not None and coll_ratio >= ratio_min:
        health = "ok"
        ok = True
    elif coll_ratio is not None and coll_ratio >= Decimal("1"):
        health = "warning"
        ok = False
    else:
        health = "critical"
        ok = False

    snap = SacpReserveSnapshot(
        id=str(uuid4()),
        snapshot_at=datetime.now(timezone.utc),
        reserve_balance_acp_smallest=int(reserve_smallest),
        sacp_total_supply_wei=int(supply_wei),
        implied_collateral_usd=implied,
        required_collateral_usd=required,
        collateral_ratio=coll_ratio,
        reconciliation_ok=ok,
        acp_reserve_address=(getattr(settings, "sacp_reserve_acp_address", None) or "").strip() or None,
        sacp_contract=(getattr(settings, "sacp_contract", None) or "").strip() or None,
        status="recorded",
        reserve_health=health,
        notes=notes or ["Operator-recorded snapshot"],
    )
    session.add(snap)
    await session.flush()
    return snap
