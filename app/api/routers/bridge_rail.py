"""wACP / BSC custodial clearing rail HTTP surface (docs/bridge-spec-v1.md)."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_auth, require_platform_admin
from app.config import get_settings
from app.db.models import (
    BridgeAllowlistAddress,
    BridgeAuditEvent,
    BridgeOperation,
    BridgeReserveSnapshot,
    BridgeWatcherCheckpoint,
)
from app.db.session import get_db
from app.schemas.bridge_rail import (
    BridgeAdminForwardBindDepositRequest,
    BridgeAdminForwardRequeueMintRequest,
    BridgeAdminReverseBindBurnRequest,
    BridgeAdminReverseBindPayoutRequest,
    BridgeAdminReverseMarkDisputedRequest,
    BridgeAdminReverseRequeuePayoutRequest,
    BridgeAllowlistAddRequest,
    BridgeIntentAcpToBscCreate,
    BridgeIntentBscToAcpCreate,
    BridgeOperationPublic,
    BridgeRedeemQuoteRequest,
    BridgeRedeemQuoteResponse,
    BridgeReserveSummaryResponse,
    BridgeReverseLiabilitySummaryResponse,
    BridgeSnapshotResponse,
    BridgeAlertsResponse,
    BridgeStatusResponse,
    WacpPublicStatusResponse,
    WacpReserveProofResponse,
)
from app.services.bridge_decimal import (
    acp_smallest_to_wacp_wei,
    wacp_wei_to_acp_smallest_ceil,
    wacp_wei_to_acp_smallest_floor,
)
from app.services.bridge_reconciliation import (
    PUBLIC_SNAPSHOT_FRESH_MINUTES,
    check_reconciliation_mismatch_alert,
    check_stale_snapshots,
    latest_reserve_snapshot,
)
from app.services.bridge_reconciliation import (
    check_reconciliation_mismatch_alert,
    check_stale_snapshots,
    run_reconciliation,
)
from app.services.wacp_supply import erc20_total_supply_wei

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bridge", tags=["Bridge (wACP)"])


def _num_to_str(value: object) -> str:
    if value is None:
        return "0"
    if isinstance(value, Decimal):
        return format(value, "f").split(".")[0]
    return str(value)


WACP_PAIR_ADDRESS = "0xF391ca2bcBaB93Afa23326ebF1e35DB950841601"
WACP_PAIR_URL = "https://pancakeswap.finance/liquidity/pool/bsc/0xF391ca2bcBaB93Afa23326ebF1e35DB950841601"
WACP_V3_POOL_ADDRESS = "0xe626bd3ef516c4f784e5d5fb46e297d9c0d7f5e1"
WACP_V3_POOL_URL = (
    "https://pancakeswap.finance/liquidity/pool/bsc/0xe626bd3ef516c4f784e5d5fb46e297d9c0d7f5e1"
)
WACP_SWAP_URL = "https://pancakeswap.finance/swap?inputCurrency=0x55d398326f99059fF775485246999027B3197955&outputCurrency=0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402"
WACP_LIQUIDITY_TX = "0x82458ec2b17e5aa58201a625169e493bb5ce8159487d66846906d9de69587503"
WACP_FIRST_SWAP_BUY_TX = "0xe6b867346d6acfdef7e0a34c457dd48c9bf572c7e0aa94224c705dc83c1a504c"
WACP_FIRST_SWAP_SELL_TX = "0x02ff5659d584aabf7bfe19c508c7673ba449ff89c1df07069cc272a6a8ab6795"


def _public_docs() -> dict[str, str]:
    s = get_settings()
    docs = {
        "overview": "https://ancap.cloud/docs/wacp",
        "bridge": "https://ancap.cloud/docs/wacp/bridge",
        "reserve": "https://ancap.cloud/docs/wacp/reserve",
        "risks": "https://ancap.cloud/docs/wacp/risks",
        "contracts": "https://ancap.cloud/docs/wacp/contracts",
        "listing_playbook": "https://ancap.cloud/docs/wacp/pancakeswap",
        "liquidity_v3_playbook": "https://ancap.cloud/docs/wacp/pancakeswap",
        "v2_pair": WACP_PAIR_URL,
        "golden_path_spend": "https://ancap.cloud/buy-acp",
    }
    v3_url = (s.wacp_v3_pool_url or "").strip() or WACP_V3_POOL_URL
    docs["v3_pool"] = v3_url
    docs["v3_pool_address"] = (s.wacp_v3_pool or "").strip().lower() or WACP_V3_POOL_ADDRESS
    docs["v3_bootstrap_shallow"] = "true"
    docs["oracle_use_v3"] = "true" if getattr(s, "wacp_oracle_use_v3", False) else "false"
    return docs


def _norm_bsc(addr: str) -> str:
    a = addr.strip().lower()
    if not re.fullmatch(r"0x[a-f0-9]{40}", a):
        raise HTTPException(status_code=400, detail="Invalid BSC address (expected 0x + 40 hex)")
    return a


def _norm_acp(addr: str) -> str:
    a = addr.strip()
    if len(a) < 3:
        raise HTTPException(status_code=400, detail="Invalid ACP address")
    return a


async def _allowlist_allows(session: AsyncSession, bsc_norm: str) -> bool:
    total = (
        await session.scalar(select(func.count()).select_from(BridgeAllowlistAddress))
    ) or 0
    if int(total) == 0:
        return True
    hit = await session.scalar(
        select(BridgeAllowlistAddress.id).where(BridgeAllowlistAddress.bsc_address == bsc_norm)
    )
    return hit is not None


def _quote_bsc_to_acp(amount_wacp: str) -> BridgeRedeemQuoteResponse:
    try:
        raw = Decimal(str(amount_wacp).strip())
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid amount_wacp") from exc
    if raw <= 0:
        raise HTTPException(status_code=400, detail="amount_wacp must be positive")
    wacp_wei = int((raw * Decimal(10) ** 18).to_integral_value(rounding=ROUND_DOWN))
    if wacp_wei <= 0:
        raise HTTPException(status_code=400, detail="amount too small after 18dp quantization")
    acp_smallest, remainder = wacp_wei_to_acp_smallest_floor(wacp_wei)
    if acp_smallest <= 0:
        raise HTTPException(status_code=400, detail="amount too small to redeem into ACP smallest units")
    acp_amount_floor = format(Decimal(acp_smallest) / (Decimal(10) ** 8), "f")
    remainder_wacp = format(Decimal(remainder) / (Decimal(10) ** 18), "f")
    return BridgeRedeemQuoteResponse(
        amount_wacp=str(raw),
        amount_wacp_wei=str(wacp_wei),
        acp_amount_floor=acp_amount_floor,
        acp_smallest_floor=str(acp_smallest),
        remainder_wacp_wei=str(remainder),
        remainder_wacp=remainder_wacp,
        policy="Floor to ACP 8 decimals; keep 18->8 decimal remainder in reserve-side buffer.",
    )


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_operation(op: BridgeOperation) -> BridgeOperationPublic:
    return BridgeOperationPublic(
        id=str(op.id),
        direction=op.direction,
        status=op.status,
        user_bsc_address=op.user_bsc_address,
        user_acp_address=op.user_acp_address,
        amount_acp_smallest=_num_to_str(op.amount_acp_smallest),
        amount_wacp_wei=_num_to_str(op.amount_wacp_wei),
        remainder_wacp_wei=_num_to_str(op.remainder_wacp_wei),
        acp_tx_hash=op.acp_tx_hash,
        bsc_tx_hash_mint=op.bsc_tx_hash_mint,
        bsc_tx_hash_burn=op.bsc_tx_hash_burn,
        deposit_ref_hex=op.deposit_ref_hex,
        bsc_log_index=op.bsc_log_index,
        version=op.version,
        created_at=op.created_at,
    )


def _require_bridge_operator_secret(settings_secret: str | None, provided_secret: str | None) -> None:
    secret = (settings_secret or "").strip()
    if not secret or (provided_secret or "").strip() != secret:
        raise HTTPException(status_code=403, detail="Invalid bridge operator secret")


async def _reverse_liability_summary(session: AsyncSession) -> BridgeReverseLiabilitySummaryResponse:
    counts_rows = await session.execute(
        select(BridgeOperation.status, func.count())
        .where(BridgeOperation.direction == "bsc_to_acp")
        .group_by(BridgeOperation.status)
    )
    counts = {str(st): int(c) for st, c in counts_rows.all()}

    def _sum_query(statuses: tuple[str, ...], column_name: str) -> select:
        column = getattr(BridgeOperation, column_name)
        return select(func.coalesce(func.sum(column), 0)).where(
            BridgeOperation.direction == "bsc_to_acp",
            BridgeOperation.status.in_(statuses),
        )

    pending_burn_wacp = int((await session.scalar(_sum_query(("PENDING_BURN",), "amount_wacp_wei"))) or 0)
    confirmed_burn_wacp = int((await session.scalar(_sum_query(("BURN_CONFIRMED",), "amount_wacp_wei"))) or 0)
    confirmed_burn_acp = int((await session.scalar(_sum_query(("BURN_CONFIRMED",), "amount_acp_smallest"))) or 0)
    payout_sent_wacp = int((await session.scalar(_sum_query(("ACP_PAYOUT_SENT",), "amount_wacp_wei"))) or 0)
    payout_sent_acp = int((await session.scalar(_sum_query(("ACP_PAYOUT_SENT",), "amount_acp_smallest"))) or 0)
    disputed_wacp = int((await session.scalar(_sum_query(("DISPUTED",), "amount_wacp_wei"))) or 0)
    disputed_acp = int((await session.scalar(_sum_query(("DISPUTED",), "amount_acp_smallest"))) or 0)
    completed_wacp = int((await session.scalar(_sum_query(("COMPLETED",), "amount_wacp_wei"))) or 0)
    completed_acp = int((await session.scalar(_sum_query(("COMPLETED",), "amount_acp_smallest"))) or 0)

    notes = [
        "Outstanding operator ACP liability is tracked as BURN_CONFIRMED + ACP_PAYOUT_SENT + DISPUTED reverse operations.",
        "PENDING_BURN is not yet an ACP payout liability until a confirmed ReleaseRequested burn is bound or detected.",
        "COMPLETED reverse operations are excluded from outstanding liability once ACP watcher confirmation lands.",
    ]

    return BridgeReverseLiabilitySummaryResponse(
        reverse_enabled_runtime=True,
        reverse_public_mode="live",
        counts_by_status=counts,
        total_pending_burn_wacp_wei=str(pending_burn_wacp),
        total_confirmed_burn_wacp_wei=str(confirmed_burn_wacp),
        total_confirmed_burn_acp_smallest=str(confirmed_burn_acp),
        total_payout_sent_wacp_wei=str(payout_sent_wacp),
        total_payout_sent_acp_smallest=str(payout_sent_acp),
        total_disputed_wacp_wei=str(disputed_wacp),
        total_disputed_acp_smallest=str(disputed_acp),
        total_completed_wacp_wei=str(completed_wacp),
        total_completed_acp_smallest=str(completed_acp),
        outstanding_operator_liability_acp_smallest=str(confirmed_burn_acp + payout_sent_acp + disputed_acp),
        notes=notes,
    )


async def _get_operation_or_404(session: AsyncSession, operation_id: str) -> BridgeOperation:
    try:
        op_uuid = UUID(operation_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid operation_id") from exc
    op = await session.get(BridgeOperation, op_uuid)
    if op is None:
        raise HTTPException(status_code=404, detail="Bridge operation not found")
    return op


async def _live_reserve_proof_payload(session: AsyncSession) -> WacpReserveProofResponse:
    s = get_settings()

    notes: list[str] = []
    completed_wacp_wei = 0
    try:
        completed_wacp_wei = int(
            await session.scalar(
                select(func.coalesce(func.sum(BridgeOperation.amount_wacp_wei), 0)).where(
                    BridgeOperation.direction == "acp_to_bsc",
                    BridgeOperation.status == "COMPLETED",
                )
            )
            or 0
        )
    except (ProgrammingError, DBAPIError, OSError) as exc:
        logger.warning("live_reserve_proof total supply summary skipped: %s", exc)
        await session.rollback()

    total_wacp = completed_wacp_wei
    supply_source = "completed_operations_fallback"
    if s.bridge_bsc_rpc_url and s.bridge_wacp_contract:
        try:
            total_wacp = await erc20_total_supply_wei(
                s.bridge_bsc_rpc_url,
                s.bridge_wacp_contract,
            )
            supply_source = "bsc_totalSupply"
            if total_wacp != completed_wacp_wei:
                notes.append(
                    "BSC totalSupply differs from completed bridge-operation accounting "
                    f"(on-chain={total_wacp}, operations={completed_wacp_wei})."
                )
        except Exception as exc:
            notes.append(
                "Authoritative BSC totalSupply lookup failed; completed-operation "
                f"accounting is shown as a degraded fallback ({exc})."
            )
    else:
        notes.append(
            "BSC RPC or wACP contract is not configured; completed-operation "
            "accounting is shown as a degraded fallback."
        )

    cp_acp = None
    cp_bsc = None
    try:
        cp_acp = await session.get(BridgeWatcherCheckpoint, "acp")
        cp_bsc = await session.get(BridgeWatcherCheckpoint, "bsc")
    except (ProgrammingError, DBAPIError, OSError) as exc:
        logger.warning("live_reserve_proof checkpoints skipped: %s", exc)
        await session.rollback()

    reserve_balance_smallest_int: int | None = None
    # ACP has 8 decimals and wACP has 18. Round the aggregate liability up,
    # otherwise a fractional remainder can make reserve proof understate debt.
    total_supply_acp_smallest = wacp_wei_to_acp_smallest_ceil(total_wacp)
    try:
        buffer_acp = Decimal(str(s.bridge_operational_buffer_acp))
        scaled_buffer = buffer_acp * (Decimal(10) ** 8)
        if (
            not buffer_acp.is_finite()
            or buffer_acp < 0
            or scaled_buffer != scaled_buffer.to_integral_value()
        ):
            raise ValueError("must be non-negative with at most 8 decimals")
        operational_buffer_smallest = int(scaled_buffer)
        buffer_config_valid = True
    except Exception as exc:
        operational_buffer_smallest = 0
        buffer_config_valid = False
        notes.append(f"Operational reserve buffer configuration is invalid ({exc}).")
    backing_ratio: str | None = None
    status = "pending"
    reserve_health = "pending"
    last_updated_at: datetime | None = None

    if not s.bridge_rail_enabled:
        status = "disabled"
        reserve_health = "disabled"
    elif s.bridge_rail_paused:
        status = "paused"
        reserve_health = "paused"

    if not s.bridge_reserve_acp_address:
        notes.append("Reserve ACP address is not configured.")
    else:
        try:
            from app.api.routers.wallet_acp import _require_acp_rpc_url, _run_walletd

            rpc_url = _require_acp_rpc_url()
            res = _run_walletd(["balance", "--rpc", rpc_url, "--address", s.bridge_reserve_acp_address], timeout_s=180)
            reserve_balance_smallest_int = int(str(res.get("units") or "0"))
            last_updated_at = _utc_now()
            if total_wacp > 0:
                backing_ratio_dec = Decimal(reserve_balance_smallest_int) / Decimal(total_supply_acp_smallest or 1)
                backing_ratio = format(backing_ratio_dec, "f")
                required_with_buffer = total_supply_acp_smallest + operational_buffer_smallest
                if reserve_balance_smallest_int >= required_with_buffer:
                    status = "healthy" if s.bridge_rail_enabled and not s.bridge_rail_paused else status
                    reserve_health = "healthy" if s.bridge_rail_enabled and not s.bridge_rail_paused else reserve_health
                elif reserve_balance_smallest_int >= total_supply_acp_smallest:
                    status = "degraded" if s.bridge_rail_enabled and not s.bridge_rail_paused else status
                    reserve_health = "degraded" if s.bridge_rail_enabled and not s.bridge_rail_paused else reserve_health
                    notes.append(
                        "Reserve covers wACP supply but is below the configured "
                        "reverse-payout fee buffer."
                    )
                else:
                    status = "critical" if s.bridge_rail_enabled and not s.bridge_rail_paused else status
                    reserve_health = "critical" if s.bridge_rail_enabled and not s.bridge_rail_paused else reserve_health
                    notes.append("Reserve balance is below on-chain wACP supply.")
            else:
                status = "healthy" if s.bridge_rail_enabled and not s.bridge_rail_paused else status
                reserve_health = "healthy" if s.bridge_rail_enabled and not s.bridge_rail_paused else reserve_health
                notes.append("Reserve balance is live; completed wACP supply is currently zero or not backfilled.")
        except HTTPException as exc:
            notes.append(f"Reserve balance lookup unavailable: {exc.detail}")
        except Exception as exc:
            notes.append(f"Reserve balance lookup failed: {exc}")

    if not s.bridge_wacp_contract:
        notes.append("wACP production contract is not configured.")

    if reserve_balance_smallest_int is None and s.bridge_rail_enabled and not s.bridge_rail_paused:
        status = "pending"
        reserve_health = "pending"
        notes.append("Reserve proof endpoint is live, but ACP reserve balance could not be sourced right now.")

    cp_acp_height = int(cp_acp.last_block_height) if cp_acp else None
    cp_bsc_height = int(cp_bsc.last_block_height) if cp_bsc else None

    latest_snapshot: BridgeReserveSnapshot | None = None
    try:
        latest_snapshot = await latest_reserve_snapshot(session)
    except Exception as exc:
        logger.warning("live_reserve_proof snapshot lookup skipped: %s", exc)
        if hasattr(session, "rollback"):
            await session.rollback()

    if latest_snapshot is not None:
        snap_age_minutes = (_utc_now() - latest_snapshot.snapshot_at).total_seconds() / 60.0
        if snap_age_minutes <= PUBLIC_SNAPSHOT_FRESH_MINUTES:
            if (
                reserve_balance_smallest_int is None
                and int(latest_snapshot.reserve_balance_acp_smallest or 0) > 0
            ):
                reserve_balance_smallest_int = int(latest_snapshot.reserve_balance_acp_smallest)
                last_updated_at = latest_snapshot.snapshot_at
                notes.append(
                    f"Reserve balance sourced from fresh snapshot ({round(snap_age_minutes, 1)} min old)."
                )
            if reserve_balance_smallest_int is not None and total_wacp > 0:
                backing_ratio_dec = Decimal(reserve_balance_smallest_int) / Decimal(
                    total_supply_acp_smallest or 1
                )
                backing_ratio = format(backing_ratio_dec, "f")
                required_with_buffer = total_supply_acp_smallest + operational_buffer_smallest
                if reserve_balance_smallest_int >= required_with_buffer:
                    status = "healthy" if s.bridge_rail_enabled and not s.bridge_rail_paused else status
                    reserve_health = "healthy" if s.bridge_rail_enabled and not s.bridge_rail_paused else reserve_health
                elif reserve_balance_smallest_int >= total_supply_acp_smallest:
                    status = "degraded" if s.bridge_rail_enabled and not s.bridge_rail_paused else status
                    reserve_health = "degraded" if s.bridge_rail_enabled and not s.bridge_rail_paused else reserve_health
                else:
                    status = "critical" if s.bridge_rail_enabled and not s.bridge_rail_paused else status
                    reserve_health = "critical" if s.bridge_rail_enabled and not s.bridge_rail_paused else reserve_health
            if latest_snapshot.last_acp_block_height is not None:
                cp_acp_height = int(latest_snapshot.last_acp_block_height)
            else:
                cp_acp_height = int(cp_acp.last_block_height) if cp_acp else None
            if latest_snapshot.last_bsc_block_number is not None:
                cp_bsc_height = int(latest_snapshot.last_bsc_block_number)
            else:
                cp_bsc_height = int(cp_bsc.last_block_height) if cp_bsc else None

    try:
        stale_alert = await check_stale_snapshots(session)
        if stale_alert:
            notes.append(
                f"Stale reserve snapshot: {stale_alert.get('age_minutes')} min "
                f"(threshold {stale_alert.get('threshold_minutes')} min)."
            )
            if reserve_health == "healthy":
                reserve_health = "degraded"
                if status == "healthy":
                    status = "degraded"
        mismatch_alert = await check_reconciliation_mismatch_alert(session)
        if mismatch_alert:
            notes.append(
                "Reconciliation mismatch on latest snapshot: "
                f"delta_wacp_wei={mismatch_alert.get('delta_wacp_wei')}."
            )
            if reserve_health not in {"disabled", "paused", "critical"}:
                reserve_health = "critical"
                status = "critical"
    except Exception as exc:
        logger.warning("live_reserve_proof alert checks skipped: %s", exc)
        if hasattr(session, "rollback"):
            await session.rollback()

    notes.append(f"wACP supply source: {supply_source}.")

    from app.services.wacp_mint_envelope import compute_mint_envelope

    envelope = compute_mint_envelope(
        acp_reserve_balance_smallest=str(reserve_balance_smallest_int or 0),
        wacp_total_supply_acp_smallest=str(total_supply_acp_smallest),
        operational_buffer_smallest=str(operational_buffer_smallest),
    )
    mint_envelope_notes = list(envelope.notes)
    if not envelope.gate_a_pass:
        mint_envelope_notes.append("Gate A: no additional mint headroom under current reserve proof.")
    max_additional_mint_acp_smallest = str(envelope.max_additional_mint_acp_smallest)

    if s.bridge_rail_enabled and not s.bridge_rail_paused:
        if supply_source != "bsc_totalSupply" and reserve_health == "healthy":
            reserve_health = "degraded"
            status = "degraded"
        if not buffer_config_valid and reserve_health not in {"critical"}:
            reserve_health = "degraded"
            status = "degraded"

    return WacpReserveProofResponse(
        status=status,
        bridge_enabled=s.bridge_rail_enabled,
        bridge_paused=s.bridge_rail_paused,
        acp_reserve_address=s.bridge_reserve_acp_address,
        acp_reserve_balance_smallest=str(reserve_balance_smallest_int or 0),
        wacp_contract=s.bridge_wacp_contract,
        wacp_total_supply_wei=str(total_wacp),
        wacp_total_supply_acp_smallest=str(total_supply_acp_smallest),
        operational_buffer_smallest=str(operational_buffer_smallest),
        backing_ratio=backing_ratio,
        reserve_health=reserve_health,
        last_acp_block_height=cp_acp_height,
        last_bsc_block_number=cp_bsc_height,
        last_updated_at=last_updated_at,
        notes=notes,
        max_additional_mint_acp_smallest=max_additional_mint_acp_smallest,
        mint_envelope_notes=mint_envelope_notes,
    )


@router.post("/quote/bsc-to-acp", response_model=BridgeRedeemQuoteResponse)
async def quote_bsc_to_acp(body: BridgeRedeemQuoteRequest):
    return _quote_bsc_to_acp(body.amount_wacp)


@router.get("/status", response_model=BridgeStatusResponse)
async def bridge_status(session: AsyncSession = Depends(get_db)):
    s = get_settings()
    counts: dict[str, int] = {}
    if s.bridge_rail_enabled:
        try:
            rows = await session.execute(
                select(BridgeOperation.status, func.count())
                .group_by(BridgeOperation.status)
            )
            for st, c in rows.all():
                counts[str(st)] = int(c)
        except (ProgrammingError, DBAPIError, OSError) as exc:
            logger.warning("bridge_status counts skipped: %s", exc)
            await session.rollback()

    cp_acp = None
    cp_bsc = None
    cp_acp_deposit = None
    try:
        cp_acp = await session.get(BridgeWatcherCheckpoint, "acp")
        cp_bsc = await session.get(BridgeWatcherCheckpoint, "bsc")
        cp_acp_deposit = await session.get(BridgeWatcherCheckpoint, "acp_deposit")
    except (ProgrammingError, DBAPIError, OSError) as exc:
        logger.warning("bridge_status checkpoints skipped (run alembic upgrade head?): %s", exc)
        await session.rollback()

    last_recon = None
    if s.bridge_rail_enabled:
        try:
            r = await session.execute(
                select(BridgeAuditEvent.payload_json)
                .where(BridgeAuditEvent.event_type.in_(("reconciliation_ok", "reconciliation_mismatch")))
                .order_by(BridgeAuditEvent.created_at.desc())
                .limit(1)
            )
            row = r.first()
            if row:
                last_recon = row[0]
        except (ProgrammingError, DBAPIError, OSError) as exc:
            logger.warning("bridge_status last_reconciliation skipped: %s", exc)
            await session.rollback()

    return BridgeStatusResponse(
        new_wacp_intents_allowed=not s.external_token_racp_only and s.bridge_rail_enabled and not s.bridge_rail_paused,
        bridge_rail_enabled=s.bridge_rail_enabled,
        bridge_rail_paused=s.bridge_rail_paused,
        dry_run=s.bridge_dry_run,
        wacp_contract=s.bridge_wacp_contract,
        gateway_contract=s.bridge_gateway_contract,
        reserve_acp_address=s.bridge_reserve_acp_address,
        confirmations_acp=s.bridge_acp_confirmations,
        confirmations_bsc=s.bridge_bsc_confirmations,
        bsc_explorer_base=s.bsc_explorer_base,
        acp_explorer_tx_base=s.acp_explorer_tx_base,
        counts_by_status=counts,
        checkpoint_acp=int(cp_acp.last_block_height) if cp_acp else None,
        checkpoint_bsc=int(cp_bsc.last_block_height) if cp_bsc else None,
        checkpoint_acp_deposit=int(cp_acp_deposit.last_block_height) if cp_acp_deposit else None,
        last_reconciliation=last_recon,
    )


@router.get("/wacp/reserve-proof", response_model=WacpReserveProofResponse)
@router.get("/reserve-proof", response_model=WacpReserveProofResponse, include_in_schema=False)
async def wacp_reserve_proof(session: AsyncSession = Depends(get_db)):
    return await _live_reserve_proof_payload(session)


@router.get("/wacp/status", response_model=WacpPublicStatusResponse)
@router.get("/status-public", response_model=WacpPublicStatusResponse, include_in_schema=False)
async def wacp_public_status(session: AsyncSession = Depends(get_db)):
    s = get_settings()

    counts: dict[str, int] = {}
    try:
        rows = await session.execute(select(BridgeOperation.status, func.count()).group_by(BridgeOperation.status))
        for st, c in rows.all():
            counts[str(st)] = int(c)
    except (ProgrammingError, DBAPIError, OSError) as exc:
        logger.warning("wacp_public_status counts skipped: %s", exc)
        await session.rollback()

    cp_acp = None
    cp_bsc = None
    try:
        cp_acp = await session.get(BridgeWatcherCheckpoint, "acp")
        cp_bsc = await session.get(BridgeWatcherCheckpoint, "bsc")
    except (ProgrammingError, DBAPIError, OSError) as exc:
        logger.warning("wacp_public_status checkpoints skipped: %s", exc)
        await session.rollback()

    reserve = await _live_reserve_proof_payload(session)

    notes: list[str] = []
    if not s.bridge_wacp_contract:
        notes.append("Production wACP contract is not configured.")
    else:
        notes.append("wACP production contract source has been matched on BscScan; public trust copy and labels can still be improved.")
    notes.append("PancakeSwap V2 technical liquidity bootstrap is live with a micro-liquidity pool; treat it as a smoke-test market, not a deep-liquidity launch.")
    notes.append("BSC -> ACP redeem path is live with funded reserve and automated payout processing; public UX and metadata can still be improved.")
    notes.append("Token metadata / logo inclusion on Pancake-related surfaces is still pending manual review by external platforms.")
    for item in reserve.notes:
        if item not in notes:
            notes.append(item)
    if s.external_token_racp_only:
        notes = ["Archived ANCAP BSC token test. rACP is the current external token. Historical redemption remains separate.", *reserve.notes]

    overall_status = "live"
    reserve_proof_status = reserve.status
    reserve_health = reserve.reserve_health
    if not s.bridge_rail_enabled:
        overall_status = "disabled"
    elif s.bridge_rail_paused:
        overall_status = "paused"
    elif reserve_health == "critical":
        overall_status = "degraded"

    return WacpPublicStatusResponse(
        status="test_archive" if s.external_token_racp_only else overall_status,
        bridge_enabled=s.bridge_rail_enabled,
        bridge_paused=s.bridge_rail_paused,
        mint_available=bool(not s.external_token_racp_only and s.bridge_rail_enabled and not s.bridge_rail_paused),
        redeem_available=bool(s.bridge_rail_enabled and not s.bridge_rail_paused and reserve_health != "critical"),
        redeem_mode="live" if bool(s.bridge_rail_enabled and not s.bridge_rail_paused and reserve_health != "critical") else "disabled",
        reserve_proof_status=reserve_proof_status,
        reserve_health=reserve_health,
        wacp_contract=s.bridge_wacp_contract,
        gateway_contract=s.bridge_gateway_contract,
        reserve_acp_address=s.bridge_reserve_acp_address,
        confirmations_acp=s.bridge_acp_confirmations,
        confirmations_bsc=s.bridge_bsc_confirmations,
        bsc_explorer_base=s.bsc_explorer_base,
        acp_explorer_tx_base=s.acp_explorer_tx_base,
        checkpoint_acp=int(cp_acp.last_block_height) if cp_acp else None,
        checkpoint_bsc=int(cp_bsc.last_block_height) if cp_bsc else None,
        last_updated_at=reserve.last_updated_at,
        pair_live=True,
        pair_dex="PancakeSwap V2",
        pair_symbol="wACP/USDT",
        pair_address=WACP_PAIR_ADDRESS,
        pair_url=WACP_PAIR_URL,
        swap_url="" if s.external_token_racp_only else WACP_SWAP_URL,
        liquidity_tx_hash=WACP_LIQUIDITY_TX,
        first_swap_buy_tx_hash=WACP_FIRST_SWAP_BUY_TX,
        first_swap_sell_tx_hash=WACP_FIRST_SWAP_SELL_TX,
        bsc_contract_verified=bool(s.bridge_bsc_contract_verified and (s.bridge_wacp_contract or "").strip()),
        token_metadata_live=bool(s.bridge_token_metadata_live),
        docs=_public_docs(),
        counts_by_status=counts,
        notes=notes,
    )


@router.get("/reserve-summary", response_model=BridgeReserveSummaryResponse)
async def bridge_reserve_summary(session: AsyncSession = Depends(get_db)):
    s = get_settings()
    if not s.bridge_rail_enabled:
        raise HTTPException(status_code=503, detail="Bridge rail is disabled")

    active_forward_statuses = (
        "PENDING_DEPOSIT",
        "CONFIRMED_ON_ACP",
        "MINT_REQUESTED",
        "MINTED_ON_BSC",
    )
    locked_forward_statuses = (*active_forward_statuses, "COMPLETED")

    pending = await session.scalar(
        select(func.count())
        .select_from(BridgeOperation)
        .where(
            BridgeOperation.direction == "acp_to_bsc",
            BridgeOperation.status.in_(active_forward_statuses),
        )
    )
    completed = await session.scalar(
        select(func.count())
        .select_from(BridgeOperation)
        .where(
            BridgeOperation.direction == "acp_to_bsc",
            BridgeOperation.status == "COMPLETED",
        )
    )
    total_acp = await session.scalar(
        select(func.coalesce(func.sum(BridgeOperation.amount_acp_smallest), 0)).where(
            BridgeOperation.direction == "acp_to_bsc",
            BridgeOperation.status.in_(locked_forward_statuses),
        )
    )
    total_wacp = await session.scalar(
        select(func.coalesce(func.sum(BridgeOperation.amount_wacp_wei), 0)).where(
            BridgeOperation.direction == "acp_to_bsc",
            BridgeOperation.status == "COMPLETED",
        )
    )
    from app.services.bridge_decimal import (
        ACP_DECIMALS,
        WACP_DECIMALS,
        WACP_PER_ACP,
        display_acp_from_smallest,
    )

    acp_smallest = int(total_acp or 0)
    wacp_wei = int(total_wacp or 0)
    acp_display = format(display_acp_from_smallest(acp_smallest), f".{ACP_DECIMALS}f")
    wacp_display = format(
        Decimal(wacp_wei) / (Decimal(10) ** WACP_DECIMALS),
        f".{WACP_DECIMALS}f",
    )
    return BridgeReserveSummaryResponse(
        total_acp_smallest_locked_intent=str(acp_smallest),
        total_wacp_wei_completed_mints=str(wacp_wei),
        total_acp_display=acp_display,
        total_wacp_display=wacp_display,
        wacp_per_acp=WACP_PER_ACP,
        operations_pending=int(pending or 0),
        operations_completed=int(completed or 0),
    )


# --- Reserve snapshot + operator alerting endpoints (Phase 5 maturity) ---

@router.get(
    "/admin/snapshots",
    response_model=list[BridgeSnapshotResponse],
)
async def list_reserve_snapshots(
    session: AsyncSession = Depends(get_db),
    admin_user_id: str = Depends(require_platform_admin),
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
    limit: int = 24,
):
    """List recent bridge reserve snapshots (operator use).

    Returns the most recent N snapshot records, newest first.
    Use to observe reserve health history and detect stale periods.
    """
    _ = admin_user_id
    s = get_settings()
    _require_bridge_operator_secret(s.bridge_operator_secret, x_bridge_operator_secret)
    from sqlalchemy import desc, select as sa_select

    rows = await session.execute(
        sa_select(BridgeReserveSnapshot)
        .order_by(desc(BridgeReserveSnapshot.snapshot_at))
        .limit(limit)
    )
    snapshots = rows.scalars().all()
    return [
        BridgeSnapshotResponse(
            id=str(s.id),
            snapshot_at=s.snapshot_at,
            reserve_balance_acp_smallest=int(s.reserve_balance_acp_smallest),
            total_wacp_wei_completed=str(int(s.total_wacp_wei_completed or 0)),
            total_wacp_wei_implied=str(int(s.total_wacp_wei_implied or 0)),
            backing_ratio=float(s.backing_ratio) if s.backing_ratio else None,
            delta_wacp_wei=str(int(s.delta_wacp_wei or 0)),
            reconciliation_ok=s.reconciliation_ok,
            status=s.status,
            reserve_health=s.reserve_health,
            notes=list(s.notes) if s.notes else [],
            last_acp_block_height=int(s.last_acp_block_height) if s.last_acp_block_height else None,
            last_bsc_block_number=int(s.last_bsc_block_number) if s.last_bsc_block_number else None,
        )
        for s in snapshots
    ]


@router.get(
    "/admin/alerts",
    response_model=BridgeAlertsResponse,
)
async def get_bridge_alerts(
    session: AsyncSession = Depends(get_db),
    admin_user_id: str = Depends(require_platform_admin),
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
):
    """Run stale-snapshot and reconciliation-mismatch checks.

    Returns any active alerts. Call after /admin/reconcile to confirm
    the latest snapshot is healthy.
    """
    _ = admin_user_id
    s = get_settings()
    _require_bridge_operator_secret(s.bridge_operator_secret, x_bridge_operator_secret)
    stale = await check_stale_snapshots(session)
    mismatch = await check_reconciliation_mismatch_alert(session)
    return BridgeAlertsResponse(
        stale_snapshot=stale,
        reconciliation_mismatch=mismatch,
    )


@router.post("/intents/acp-to-bsc", response_model=BridgeOperationPublic)
async def create_intent_acp_to_bsc(
    body: BridgeIntentAcpToBscCreate,
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    s = get_settings()
    if s.external_token_racp_only:
        raise HTTPException(status_code=409, detail="New ACP to wACP intents are closed. Use rACP on Robinhood Chain; legacy wACP redemption remains separate.")
    if not s.bridge_rail_enabled:
        raise HTTPException(status_code=503, detail="Bridge rail is disabled")
    if s.bridge_rail_paused:
        raise HTTPException(status_code=503, detail="Bridge rail is paused")

    bsc = _norm_bsc(body.user_bsc_address)
    if not await _allowlist_allows(session, bsc):
        raise HTTPException(status_code=403, detail="BSC address not on bridge allowlist")

    try:
        raw = Decimal(str(body.amount_acp).strip())
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid amount_acp") from exc
    if raw <= 0:
        raise HTTPException(status_code=400, detail="amount_acp must be positive")
    smallest = int((raw * Decimal(10) ** 8).to_integral_value(rounding=ROUND_DOWN))
    if smallest <= 0:
        raise HTTPException(status_code=400, detail="amount too small after 8dp quantization")
    wacp_wei = acp_smallest_to_wacp_wei(smallest)

    op = BridgeOperation(
        id=uuid4(),
        user_id=UUID(user_id),
        direction="acp_to_bsc",
        status="PENDING_DEPOSIT",
        user_bsc_address=bsc,
        user_acp_address=(body.user_acp_address or "").strip() or None,
        amount_acp_smallest=smallest,
        amount_wacp_wei=wacp_wei,
        remainder_wacp_wei=0,
    )
    session.add(op)
    await session.flush()
    session.add(
        BridgeAuditEvent(
            operation_id=op.id,
            event_type="intent_created",
            payload_json={"direction": "acp_to_bsc", "amount_acp_smallest": smallest},
        )
    )
    await session.flush()
    await session.refresh(op)
    return _serialize_operation(op)


@router.post("/intents/bsc-to-acp", response_model=BridgeOperationPublic)
async def create_intent_bsc_to_acp(
    body: BridgeIntentBscToAcpCreate,
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    s = get_settings()
    if not s.bridge_rail_enabled:
        raise HTTPException(status_code=503, detail="Bridge rail is disabled")
    if s.bridge_rail_paused:
        raise HTTPException(status_code=503, detail="Bridge rail is paused")

    bsc = _norm_bsc(body.user_bsc_address)
    acp = _norm_acp(body.user_acp_address)
    if not await _allowlist_allows(session, bsc):
        raise HTTPException(status_code=403, detail="BSC address not on bridge allowlist")

    quote = _quote_bsc_to_acp(body.amount_wacp)
    wacp_wei = int(quote.amount_wacp_wei)
    acp_smallest = int(quote.acp_smallest_floor)
    remainder = int(quote.remainder_wacp_wei)

    op = BridgeOperation(
        id=uuid4(),
        user_id=UUID(user_id),
        direction="bsc_to_acp",
        status="PENDING_BURN",
        user_bsc_address=bsc,
        user_acp_address=acp,
        amount_acp_smallest=acp_smallest,
        amount_wacp_wei=wacp_wei,
        remainder_wacp_wei=remainder,
    )
    session.add(op)
    await session.flush()
    session.add(
        BridgeAuditEvent(
            operation_id=op.id,
            event_type="intent_created",
            payload_json={
                "direction": "bsc_to_acp",
                "amount_acp_smallest": acp_smallest,
                "amount_wacp_wei": wacp_wei,
                "remainder_wacp_wei": remainder,
            },
        )
    )
    await session.flush()
    await session.refresh(op)
    return _serialize_operation(op)


@router.get("/intents/me", response_model=list[BridgeOperationPublic])
async def list_my_intents(
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    s = get_settings()
    if not s.bridge_rail_enabled:
        raise HTTPException(status_code=503, detail="Bridge rail is disabled")
    lim = max(1, min(limit, 200))
    r = await session.execute(
        select(BridgeOperation)
        .where(BridgeOperation.user_id == UUID(user_id))
        .order_by(BridgeOperation.created_at.desc())
        .limit(lim)
    )
    out: list[BridgeOperationPublic] = []
    for op in r.scalars().all():
        out.append(_serialize_operation(op))
    return out


@router.post("/intents/{operation_id}/cancel", response_model=BridgeOperationPublic)
async def cancel_my_pending_intent(
    operation_id: str,
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    """Cancel an unpaid forward intent stuck in PENDING_DEPOSIT."""
    s = get_settings()
    if not s.bridge_rail_enabled:
        raise HTTPException(status_code=503, detail="Bridge rail is disabled")
    op = await _get_operation_or_404(session, operation_id)
    if str(op.user_id) != str(user_id):
        raise HTTPException(status_code=404, detail="Operation not found")
    if op.direction != "acp_to_bsc":
        raise HTTPException(status_code=400, detail="Only forward intents can be cancelled here")
    if op.status != "PENDING_DEPOSIT":
        raise HTTPException(status_code=409, detail="Only PENDING_DEPOSIT intents can be cancelled")
    if op.acp_tx_hash:
        raise HTTPException(status_code=409, detail="Deposit already bound; cannot cancel")
    from app.services.bridge_orchestrator import append_transition

    session.add(
        BridgeAuditEvent(
            operation_id=op.id,
            event_type="intent_cancelled_by_user",
            payload_json={},
        )
    )
    await append_transition(session, op, "CANCELLED", metadata={"reason": "user_cancel"})
    await session.flush()
    await session.refresh(op)
    return _serialize_operation(op)


@router.post("/admin/reconcile", response_model=dict)
async def admin_reconcile(
    session: AsyncSession = Depends(get_db),
    admin_user_id: str = Depends(require_platform_admin),
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
):
    s = get_settings()
    if not s.bridge_rail_enabled:
        raise HTTPException(status_code=503, detail="Bridge rail is disabled")
    _require_bridge_operator_secret(s.bridge_operator_secret, x_bridge_operator_secret)
    return await run_reconciliation(session)


@router.post("/admin/allowlist", response_model=dict)
async def admin_allowlist_add(
    body: BridgeAllowlistAddRequest,
    session: AsyncSession = Depends(get_db),
    admin_user_id: str = Depends(require_platform_admin),
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
):
    s = get_settings()
    _require_bridge_operator_secret(s.bridge_operator_secret, x_bridge_operator_secret)
    bsc = _norm_bsc(body.bsc_address)
    dup = await session.scalar(
        select(BridgeAllowlistAddress.id).where(BridgeAllowlistAddress.bsc_address == bsc)
    )
    if dup is not None:
        raise HTTPException(status_code=409, detail="Allowlist entry already exists")
    row = BridgeAllowlistAddress(id=uuid4(), bsc_address=bsc, note=body.note)
    session.add(row)
    await session.flush()
    return {"ok": True, "bsc_address": bsc}


@router.get("/admin/reverse/operations", response_model=list[BridgeOperationPublic])
async def admin_reverse_operations(
    session: AsyncSession = Depends(get_db),
    admin_user_id: str = Depends(require_platform_admin),
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
    status: str | None = None,
    limit: int = 100,
):
    s = get_settings()
    _require_bridge_operator_secret(s.bridge_operator_secret, x_bridge_operator_secret)
    lim = max(1, min(limit, 500))
    q = select(BridgeOperation).where(BridgeOperation.direction == "bsc_to_acp")
    if status:
        q = q.where(BridgeOperation.status == status)
    q = q.order_by(BridgeOperation.created_at.desc()).limit(lim)
    r = await session.execute(q)
    return [_serialize_operation(op) for op in r.scalars().all()]


@router.get("/admin/reverse/liability", response_model=BridgeReverseLiabilitySummaryResponse)
async def admin_reverse_liability(
    session: AsyncSession = Depends(get_db),
    admin_user_id: str = Depends(require_platform_admin),
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
):
    s = get_settings()
    _require_bridge_operator_secret(s.bridge_operator_secret, x_bridge_operator_secret)
    return await _reverse_liability_summary(session)


@router.post("/admin/reverse/bind-burn", response_model=BridgeOperationPublic)
async def admin_reverse_bind_burn(
    body: BridgeAdminReverseBindBurnRequest,
    session: AsyncSession = Depends(get_db),
    admin_user_id: str = Depends(require_platform_admin),
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
):
    s = get_settings()
    _require_bridge_operator_secret(s.bridge_operator_secret, x_bridge_operator_secret)
    op = await _get_operation_or_404(session, body.operation_id)
    if op.direction != "bsc_to_acp":
        raise HTTPException(status_code=400, detail="Operation is not reverse rail")
    if op.status not in {"PENDING_BURN", "BURN_CONFIRMED"}:
        raise HTTPException(status_code=409, detail="Operation is not in a burn-bindable state")
    tx_hash = str(body.bsc_tx_hash_burn).strip()
    dup = await session.scalar(
        select(BridgeOperation.id).where(
            BridgeOperation.id != op.id,
            BridgeOperation.bsc_tx_hash_burn == tx_hash,
            BridgeOperation.bsc_log_index == body.bsc_log_index,
        )
    )
    if dup is not None:
        raise HTTPException(status_code=409, detail="Burn tx/log already bound to another operation")
    op.bsc_tx_hash_burn = tx_hash
    op.bsc_log_index = int(body.bsc_log_index)
    if body.correlation_id is not None:
        op.correlation_id = str(body.correlation_id).strip() or None
    session.add(
        BridgeAuditEvent(
            operation_id=op.id,
            event_type="admin_reverse_bind_burn",
            payload_json={
                "bsc_tx_hash_burn": tx_hash,
                "bsc_log_index": int(body.bsc_log_index),
                "correlation_id": op.correlation_id,
                "note": body.note,
            },
        )
    )
    if op.status == "PENDING_BURN":
        from app.services.bridge_orchestrator import append_transition
        await append_transition(
            session,
            op,
            "BURN_CONFIRMED",
            metadata={
                "admin": True,
                "bsc_tx_hash_burn": tx_hash,
                "bsc_log_index": int(body.bsc_log_index),
                "correlation_id": op.correlation_id,
                "note": body.note,
            },
        )
    await session.flush()
    await session.refresh(op)
    return _serialize_operation(op)


@router.post("/admin/forward/bind-deposit", response_model=BridgeOperationPublic)
async def admin_forward_bind_deposit(
    body: BridgeAdminForwardBindDepositRequest,
    session: AsyncSession = Depends(get_db),
    admin_user_id: str = Depends(require_platform_admin),
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
):
    s = get_settings()
    _require_bridge_operator_secret(s.bridge_operator_secret, x_bridge_operator_secret)
    op = await _get_operation_or_404(session, body.operation_id)
    if op.direction != "acp_to_bsc":
        raise HTTPException(status_code=400, detail="Operation is not forward rail")
    if op.status != "PENDING_DEPOSIT":
        raise HTTPException(status_code=409, detail="Operation is not in PENDING_DEPOSIT")
    tx_hash = str(body.acp_tx_hash).strip().lower()
    dup = await session.scalar(
        select(BridgeOperation.id).where(
            BridgeOperation.id != op.id,
            BridgeOperation.acp_tx_hash == tx_hash,
        )
    )
    if dup is not None:
        raise HTTPException(status_code=409, detail="ACP deposit tx already bound to another operation")
    reserve = (s.bridge_reserve_acp_address or "").strip()
    rpc = (s.acp_rpc_url or "").strip()
    if not reserve or not rpc:
        raise HTTPException(status_code=503, detail="ACP reserve or RPC is not configured")
    from app.services.bridge_acp_watcher import reserve_deposit_units_for_tx
    from app.services.bridge_orchestrator import append_transition

    try:
        deposit = await reserve_deposit_units_for_tx(rpc, reserve, tx_hash)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    expected_units = int(op.amount_acp_smallest or 0)
    received_units = int(deposit.get("received_units") or 0)
    if received_units != expected_units:
        raise HTTPException(
            status_code=409,
            detail=f"Deposit amount mismatch: tx credited {received_units} smallest units, intent expects {expected_units}",
        )
    confirmations = int(deposit.get("confirmations") or 0)
    if confirmations < int(s.bridge_acp_confirmations):
        raise HTTPException(
            status_code=409,
            detail=f"Deposit has {confirmations} confirmations; need {s.bridge_acp_confirmations}",
        )
    op.acp_tx_hash = tx_hash
    op.acp_out_index = 0
    session.add(
        BridgeAuditEvent(
            operation_id=op.id,
            event_type="admin_forward_bind_deposit",
            payload_json={
                "acp_tx_hash": tx_hash,
                "received_units": received_units,
                "confirmations": confirmations,
                "note": body.note,
            },
        )
    )
    session.add(
        BridgeAuditEvent(
            operation_id=op.id,
            event_type="acp_deposit_detected",
            payload_json={
                "txid": tx_hash,
                "confirmations": confirmations,
                "net_units": received_units,
                "admin": True,
            },
        )
    )
    await append_transition(
        session,
        op,
        "CONFIRMED_ON_ACP",
        metadata={"admin": True, "txid": tx_hash, "note": body.note},
    )
    await session.flush()
    await session.refresh(op)
    return _serialize_operation(op)


@router.post("/admin/forward/requeue-mint", response_model=BridgeOperationPublic)
async def admin_forward_requeue_mint(
    body: BridgeAdminForwardRequeueMintRequest,
    session: AsyncSession = Depends(get_db),
    admin_user_id: str = Depends(require_platform_admin),
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
):
    """Requeue a FAILED forward mint after ACP deposit was already bound."""
    s = get_settings()
    _require_bridge_operator_secret(s.bridge_operator_secret, x_bridge_operator_secret)
    op = await _get_operation_or_404(session, body.operation_id)
    if op.direction != "acp_to_bsc":
        raise HTTPException(status_code=400, detail="Operation is not forward rail")
    if op.status != "FAILED":
        raise HTTPException(status_code=409, detail="Only FAILED forward operations can be requeued")
    if not op.acp_tx_hash:
        raise HTTPException(status_code=409, detail="FAILED op has no ACP deposit tx to remint from")
    from app.services.bridge_orchestrator import append_transition

    op.bsc_tx_hash_mint = None
    op.bsc_log_index = None
    op.deposit_ref_hex = None
    session.add(
        BridgeAuditEvent(
            operation_id=op.id,
            event_type="admin_forward_requeue_mint",
            payload_json={"note": body.note, "acp_tx_hash": op.acp_tx_hash},
        )
    )
    await append_transition(
        session,
        op,
        "CONFIRMED_ON_ACP",
        metadata={"admin": True, "requeued_from": "FAILED", "note": body.note},
    )
    await session.flush()
    await session.refresh(op)
    return _serialize_operation(op)


@router.post("/admin/reverse/bind-payout", response_model=BridgeOperationPublic)
async def admin_reverse_bind_payout(
    body: BridgeAdminReverseBindPayoutRequest,
    session: AsyncSession = Depends(get_db),
    admin_user_id: str = Depends(require_platform_admin),
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
):
    s = get_settings()
    _require_bridge_operator_secret(s.bridge_operator_secret, x_bridge_operator_secret)
    op = await _get_operation_or_404(session, body.operation_id)
    if op.direction != "bsc_to_acp":
        raise HTTPException(status_code=400, detail="Operation is not reverse rail")
    if op.status not in {"BURN_CONFIRMED", "ACP_PAYOUT_SENT"}:
        raise HTTPException(status_code=409, detail="Operation is not in a payout-bindable state")
    tx_hash = str(body.acp_tx_hash).strip()
    dup = await session.scalar(
        select(BridgeOperation.id).where(
            BridgeOperation.id != op.id,
            BridgeOperation.acp_tx_hash == tx_hash,
        )
    )
    if dup is not None:
        raise HTTPException(status_code=409, detail="ACP payout tx already bound to another operation")
    op.acp_tx_hash = tx_hash
    op.acp_out_index = 0
    session.add(
        BridgeAuditEvent(
            operation_id=op.id,
            event_type="admin_reverse_bind_payout",
            payload_json={"acp_tx_hash": tx_hash, "note": body.note},
        )
    )
    if op.status == "BURN_CONFIRMED":
        from app.services.bridge_orchestrator import append_transition
        await append_transition(
            session,
            op,
            "ACP_PAYOUT_SENT",
            metadata={"admin": True, "txid": tx_hash, "note": body.note},
        )
    await session.flush()
    await session.refresh(op)
    return _serialize_operation(op)


@router.post("/admin/reverse/requeue-payout", response_model=BridgeOperationPublic)
async def admin_reverse_requeue_payout(
    body: BridgeAdminReverseRequeuePayoutRequest,
    session: AsyncSession = Depends(get_db),
    admin_user_id: str = Depends(require_platform_admin),
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
):
    s = get_settings()
    _require_bridge_operator_secret(s.bridge_operator_secret, x_bridge_operator_secret)
    op = await _get_operation_or_404(session, body.operation_id)
    if op.direction != "bsc_to_acp":
        raise HTTPException(status_code=400, detail="Operation is not reverse rail")
    if op.status != "ACP_PAYOUT_SENT":
        raise HTTPException(status_code=409, detail="Only ACP_PAYOUT_SENT operations can be requeued")
    from app.services.bridge_orchestrator import append_transition
    session.add(
        BridgeAuditEvent(
            operation_id=op.id,
            event_type="admin_reverse_requeue_payout",
            payload_json={"previous_acp_tx_hash": op.acp_tx_hash, "note": body.note},
        )
    )
    op.acp_tx_hash = None
    op.acp_out_index = 0
    await append_transition(
        session,
        op,
        "BURN_CONFIRMED",
        metadata={"admin": True, "requeued_from": "ACP_PAYOUT_SENT", "note": body.note},
    )
    await session.flush()
    await session.refresh(op)
    return _serialize_operation(op)


@router.post("/admin/reverse/mark-disputed", response_model=BridgeOperationPublic)
async def admin_reverse_mark_disputed(
    body: BridgeAdminReverseMarkDisputedRequest,
    session: AsyncSession = Depends(get_db),
    admin_user_id: str = Depends(require_platform_admin),
    x_bridge_operator_secret: str | None = Header(None, alias="X-Bridge-Operator-Secret"),
):
    s = get_settings()
    _require_bridge_operator_secret(s.bridge_operator_secret, x_bridge_operator_secret)
    op = await _get_operation_or_404(session, body.operation_id)
    if op.direction != "bsc_to_acp":
        raise HTTPException(status_code=400, detail="Operation is not reverse rail")
    if op.status == "COMPLETED":
        raise HTTPException(status_code=409, detail="Completed operations cannot be manually disputed here")
    from app.services.bridge_orchestrator import append_transition
    session.add(
        BridgeAuditEvent(
            operation_id=op.id,
            event_type="admin_reverse_mark_disputed",
            payload_json={"note": body.note},
        )
    )
    await append_transition(
        session,
        op,
        "DISPUTED",
        metadata={"admin": True, "note": body.note},
    )
    await session.flush()
    await session.refresh(op)
    return _serialize_operation(op)
