from app.services.recoverable_errors import report_optional_failure
import json
import os
import subprocess
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
import shutil
from decimal import Decimal, InvalidOperation
from uuid import uuid4

import httpx
from fastapi import APIRouter, Header, HTTPException, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.api.deps import require_auth
from app.services.cache import cache_get_json, cache_get_json_sync, cache_set_json_sync
from app.db.models import (
    Agent,
    Stake,
    StakeStatusEnum,
    Account,
    LedgerEvent,
    AcpSwapOrder,
    UserAcpPrivacyAddress,
    AcpOtcIntakeOrder,
    MobileAcpTx,
)
from app.db.session import get_db
from app.services.acp_wallet import get_wallet_for_user
from app.services.acp_wallet import decrypt_mnemonic
from app.services.acp_wallet import decode_wallet_secret
from app.services.acp_wallet import personalize_hot_bound_wallet
from app.services.acp_wallet import user_is_custodial_hot_holder
from app.services.acp_wallet import upsert_address_binding, BINDING_KIND_PRIVACY
from app.services.acp_amounts import rpc_amount_units
from app.services.acp_tokenomics import (
    CUSTODIAL_HOT_ADDRESS,
    OPERATOR_ROLE_ADDRESSES,
    OPERATOR_ROLE_WALLETS,
    acp_supply_layout,
)
from app.services import acp_privacy as privacy_svc
from app.services import otc_intake as otc_svc
from app.schemas.otc_intake import (
    OtcCatalogPublic,
    OtcMetalQuoteRequest,
    OtcGoodsQuoteRequest,
    OtcCommodityQuoteRequest,
    OtcQuoteResponse,
    OtcIntakeCreateRequest,
    OtcIntakeConfirmRequest,
    OtcIntakeOrderPublic,
    OtcRealEstateQuoteRequest,
    OtcSpaceQuoteRequest,
    OtcIpQuoteRequest,
)
from app.schemas import (
    AcpBalanceResponse,
    AcpDepositAddressResponse,
    AcpPersonalizeWalletRequest,
    AcpPersonalizeWalletResponse,
    AcpPrivacyDepositRequest,
    AcpPrivacyStatusPublic,
    AcpTokenomicsBucket,
    AcpWithdrawRequest,
    AcpWithdrawResponse,
    AcpWithdrawJobResponse,
    AcpTransactionPublic,
    AcpTransactionDetailsPublic,
    AcpTransactionIoPublic,
    AcpSwapQuoteRequest,
    AcpSwapQuoteResponse,
    AcpSwapOrderCreateRequest,
    AcpSwapOrderConfirmRequest,
    AcpSwapOrderPublic,
    AcpSwapCompleteResponse,
    AcpSwapCompleteRequest,
)


router = APIRouter(prefix="/wallet/acp", tags=["Wallet (ACP)"])

_CHAIN_SCAN_CACHE_TTL_S = 120.0
_chain_scan_cache: dict[str, object] = {
    "expires_at": 0.0,
    "data": None,
}
_chain_scan_lock = threading.Lock()
_chain_scan_state: dict[str, bool] = {"inflight": False}

_CHAIN_BALANCE_CACHE_TTL_S = 30.0
_CHAIN_BALANCE_NEGATIVE_CACHE_TTL_S = 5.0
_chain_balance_cache: dict[str, tuple[float, dict]] = {}

# Interactive wallet UI must stay snappy. Full tip scans (~30k blocks) belong in
# a background warmer, never on the request path.
_INTERACTIVE_WALLETD_TIMEOUT_S = 5
# Operator role wallets need a longer probe than retail UI, but aggregate
# probes must stay inside the frontend balance AbortSignal (~45s).
_OPERATOR_ROLE_WALLETD_TIMEOUT_S = 15
_OPERATOR_AGGREGATE_BUDGET_S = 30.0
_OPERATOR_AGGREGATE_PER_ROLE_S = 10
_INTERACTIVE_RPC_TIMEOUT_S = 5.0
_ACP_SUPPLY_CAP_UNITS = 210_000_000 * 100_000_000


def _walletd_cmd() -> list[str]:
    """
    Uses a dedicated helper binary implemented in ACP-crypto/acp-wallet/src/bin/walletd.rs.
    For production set ACP_WALLETD_PATH to the compiled binary path.
    """
    p = os.getenv("ACP_WALLETD_PATH", "").strip()
    if p:
        return [p]
    # Fallback to PATH lookup to simplify container deployments where walletd is mounted into /usr/local/bin.
    if shutil.which("walletd"):
        return ["walletd"]
    raise HTTPException(
        status_code=503,
        detail="ACP wallet helper is not configured (set ACP_WALLETD_PATH or make 'walletd' available in PATH)",
    )


def _run_walletd(args: list[str], timeout_s: int = 90) -> dict:
    try:
        r = subprocess.run(
            _walletd_cmd() + args,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="ACP wallet helper timed out")

    out = (r.stdout or "").strip()
    try:
        payload = json.loads(out) if out else {}
    except Exception:
        raise HTTPException(status_code=502, detail=f"ACP wallet helper returned non-JSON output: {out[:200]}")

    if r.returncode != 0 or not payload.get("ok"):
        err = payload.get("error") or (r.stderr or "").strip() or "unknown"
        raise HTTPException(status_code=502, detail=f"ACP wallet helper failed: {err}")
    return payload["result"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _require_non_empty(value: str, field_name: str) -> str:
    out = (value or "").strip()
    if not out:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")
    return out


_ACP_ADDRESS_RE = re.compile(r"^acp1[a-z0-9]{20,100}$")
# Grouping helpers for pasted amounts (withdraw / fees / quotes).
_US_GROUPED_DECIMAL_RE = re.compile(r"^-?\d{1,3}(,\d{3})+(\.\d*)?$")
_EU_GROUPED_DECIMAL_RE = re.compile(r"^-?\d{1,3}(\.\d{3})+(,\d+)?$")


def _normalize_user_decimal_string(raw: object) -> str:
    """
    Strip wrappers and grouping so Decimal() accepts common user input:
    1,000,000 · 1.234.567,89 · 12,34 · trailing 'ACP' / NBSP.
    """
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    for ch in ("\u00a0", "\u202f", "\u2009", "\u2007", " "):
        s = s.replace(ch, "")
    s = s.replace("\u2212", "-").replace("−", "-").replace("＋", "+")
    s = re.sub(r"(?i)(?:acp|токен)\s*$", "", s).strip()
    if not s:
        return ""

    if _US_GROUPED_DECIMAL_RE.fullmatch(s):
        return s.replace(",", "")
    if _EU_GROUPED_DECIMAL_RE.fullmatch(s):
        if "," in s:
            body, frac = s.rsplit(",", 1)
            return body.replace(".", "") + "." + frac
        return s.replace(".", "")

    if "," in s and "." not in s:
        parts = s.split(",")
        if len(parts) == 2:
            left, right = parts
            ld = left.lstrip("-")
            if ld.isdigit() and right.isdigit():
                if len(right) <= 2:
                    return f"{left}.{right}"
                if len(right) == 3 and len(ld) <= 3:
                    return f"{left}{right}"
                return f"{left}.{right}"
        return s.replace(",", "")

    return s


def _parse_positive_decimal(value: object, field_name: str) -> Decimal:
    normalized = _normalize_user_decimal_string(value)
    if not normalized:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")
    try:
        d = Decimal(normalized)
    except (InvalidOperation, ValueError):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")
    if d <= 0:
        raise HTTPException(status_code=400, detail=f"{field_name} must be > 0")
    return d


def _validate_acp_address(value: str, field_name: str) -> str:
    out = _require_non_empty(value, field_name)
    if not _ACP_ADDRESS_RE.fullmatch(out):
        raise HTTPException(
            status_code=400,
            detail=(
                f"{field_name} is invalid; expected ACP bech32-like address "
                "starting with 'acp1' and containing lowercase letters/digits"
            ),
        )
    return out


def _require_acp_rpc_url() -> str:
    settings = get_settings()
    rpc = (settings.acp_rpc_url or "").strip()
    if not rpc:
        raise HTTPException(status_code=503, detail="ACP RPC URL is not configured")
    return rpc


def _swap_rate() -> Decimal:
    from app.services.market_economy import usdt_to_acp_desk_rate

    return usdt_to_acp_desk_rate()


def _decimal_to_api_str(value: Decimal, scale: str = "0.00000001") -> str:
    """
    Render Decimal as plain string (no scientific notation) with trailing zeros trimmed.
    """
    q = value.quantize(Decimal(scale))
    s = format(q, "f").rstrip("0").rstrip(".")
    return s or "0"


def _units_to_acp_str(units: int) -> str:
    return _decimal_to_api_str(Decimal(units) / Decimal(100_000_000))


def _acp_timestamp(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat().replace("+00:00", "Z")


def _json_chain_amount_to_int(value: object) -> int:
    """Parse exact integer units from ACP node JSON-RPC."""
    return rpc_amount_units(value)


def _parse_decimal_or_zero(value: str | int | float | Decimal | None) -> Decimal:
    try:
        if value is None:
            return Decimal(0)
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal(0)


async def _in_work_breakdown_for_user(
    session: AsyncSession, user_id: str
) -> tuple[Decimal, Decimal, Decimal]:
    """
    Return (total_in_work, staked_acp, ledger_positive_net_acp).

    `staked_acp` counts active ACP stakes on user-owned agents.
    `ledger_positive_net_acp` sums max(net, 0) per user + those agents’ ledger accounts
    (fluid balances still on-platform). Together they cap what we allow to withdraw on-chain
    so the same ACP is not spent twice.
    """
    try:
        owner_user_id = user_id.strip()
    except Exception:
        return (Decimal(0), Decimal(0), Decimal(0))
    if not owner_user_id:
        return (Decimal(0), Decimal(0), Decimal(0))
    stake_q = (
        select(func.coalesce(func.sum(Stake.amount_value), 0))
        .select_from(Stake)
        .join(Agent, Agent.id == Stake.agent_id)
        .where(
            Agent.owner_user_id == owner_user_id,
            Stake.status == StakeStatusEnum.active,
            Stake.amount_currency == "ACP",
        )
    )
    stake_result = await session.execute(stake_q)
    staked_acp = _parse_decimal_or_zero(stake_result.scalar())

    agent_ids = (
        await session.execute(select(Agent.id).where(Agent.owner_user_id == owner_user_id))
    ).scalars().all()
    owner_filters = [(Account.owner_type == "user", Account.owner_id == owner_user_id)]
    if agent_ids:
        owner_filters.append((Account.owner_type == "agent", Account.owner_id.in_(agent_ids)))

    account_ids = []
    for owner_type_cond, owner_id_cond in owner_filters:
        rows = (
            await session.execute(
                select(Account.id).where(owner_type_cond, owner_id_cond)
            )
        ).scalars().all()
        account_ids.extend(rows)

    # Stable unique ordering; avoids double-counting if a bug ever duplicates ids.
    account_ids = list(dict.fromkeys(account_ids))

    if not account_ids:
        return (staked_acp, staked_acp, Decimal(0))

    credits_rows = (
        await session.execute(
            select(LedgerEvent.dst_account_id, func.coalesce(func.sum(LedgerEvent.amount_value), 0))
            .where(
                LedgerEvent.amount_currency == "ACP",
                LedgerEvent.dst_account_id.in_(account_ids),
            )
            .group_by(LedgerEvent.dst_account_id)
        )
    ).all()
    debits_rows = (
        await session.execute(
            select(LedgerEvent.src_account_id, func.coalesce(func.sum(LedgerEvent.amount_value), 0))
            .where(
                LedgerEvent.amount_currency == "ACP",
                LedgerEvent.src_account_id.in_(account_ids),
            )
            .group_by(LedgerEvent.src_account_id)
        )
    ).all()

    credits = {str(k): _parse_decimal_or_zero(v) for k, v in credits_rows}
    debits = {str(k): _parse_decimal_or_zero(v) for k, v in debits_rows}
    ledger_reserved_acp = Decimal(0)
    for acc_id in account_ids:
        key = str(acc_id)
        bal = credits.get(key, Decimal(0)) - debits.get(key, Decimal(0))
        if bal > 0:
            ledger_reserved_acp += bal

    total = staked_acp + ledger_reserved_acp
    return (total, staked_acp, ledger_reserved_acp)


async def _in_work_acp_for_user(session: AsyncSession, user_id: str) -> Decimal:
    total, _, _ = await _in_work_breakdown_for_user(session, user_id)
    return total


def _format_balance_note(real_acp: Decimal, in_work_acp: Decimal, available_acp: Decimal) -> str:
    return (
        f"Real account balance: {_decimal_to_api_str(real_acp)} ACP; "
        f"in work: {_decimal_to_api_str(in_work_acp)} ACP; "
        f"available for withdraw: {_decimal_to_api_str(available_acp)} ACP."
    )


def _units_from_acp(acp: Decimal) -> str:
    return str(int((acp * Decimal(100_000_000)).to_integral_value()))


def _custodial_balance_view(
    on_chain_acp: Decimal,
    staked_acp: Decimal,
    ledger_acp: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    """Map mixed custodial hot UTXOs to ledger-backed user entitlement."""
    entitlement = staked_acp + ledger_acp
    if entitlement <= 0:
        available = on_chain_acp - staked_acp
        if available < 0:
            available = Decimal(0)
        return on_chain_acp, staked_acp + ledger_acp, available
    display_acp = min(on_chain_acp, entitlement)
    available = min(ledger_acp, max(on_chain_acp - staked_acp, Decimal(0)))
    if available < 0:
        available = Decimal(0)
    return display_acp, entitlement, available


def _personal_balance_view(
    on_chain_acp: Decimal,
    staked_acp: Decimal,
    ledger_acp: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    """Personal UTXOs are not capped to a share of the shared hot wallet.

    Keep existing platform reservations unavailable, so they cannot also be spent
    on-chain. A separate ledger withdrawal/unstake must release those claims first.
    """
    total = max(on_chain_acp, Decimal(0))
    reserved = max(staked_acp, Decimal(0)) + max(ledger_acp, Decimal(0))
    return total, reserved, max(total - reserved, Decimal(0))


def _creator_vesting_monthly_unlock_acp() -> Decimal:
    # 69,300,000 ACP over 72 months after a 12-month cliff.
    return Decimal("962500")


# `acp_crypto::protocol_params::{GENESIS_ACP_CREATOR, UNITS_PER_ACP}`.
_GENESIS_ACP_CREATOR_AMOUNT_ACP: int = 69_300_000
_UNITS_PER_ACP: int = 100_000_000
_GENESIS_CREATOR_OUTPUT_UNITS: int = _GENESIS_ACP_CREATOR_AMOUNT_ACP * _UNITS_PER_ACP


_creator_vesting_genesis_cache: dict[str, object] = {
    "expires_at": 0.0,
    "creator_address": None,
    "genesis_time": 0,
    "eligible": False,
}


def _creator_vesting_snapshot(address: str, now_ts: int | None = None) -> tuple[Decimal, Decimal] | None:
    """
    Return (unlocked_acp, locked_acp) for the canonical creator genesis vout, otherwise None.

    The node applies vesting only to genesis tx vout 0. UI must not treat every
    genesis payee as the vested creator (e.g. a 1,000,000 ACP dev allocation on vout 0).
    We only return fields when vout 0 is exactly 69,300,000 ACP to the queried address.
    """
    target = (address or "").strip()
    if not target:
        return None

    now_mono = time.monotonic()
    cached_addr = _creator_vesting_genesis_cache.get("creator_address")
    if now_mono < float(_creator_vesting_genesis_cache.get("expires_at") or 0.0):
        if not _creator_vesting_genesis_cache.get("eligible"):
            return None
        if cached_addr != target:
            return None
        genesis_time = int(_creator_vesting_genesis_cache.get("genesis_time") or 0)
        creator_total_acp = Decimal(_GENESIS_ACP_CREATOR_AMOUNT_ACP)
        now = int(now_ts or datetime.now(timezone.utc).timestamp())
        if now <= genesis_time:
            return (Decimal(0), creator_total_acp)
        elapsed = now - genesis_time
        seconds_per_month = 30 * 24 * 60 * 60
        cliff_months = 12
        linear_months = 72
        if elapsed <= cliff_months * seconds_per_month:
            unlocked = Decimal(0)
        else:
            months_after_cliff = min(
                (elapsed - cliff_months * seconds_per_month) // seconds_per_month,
                linear_months,
            )
            unlocked = _creator_vesting_monthly_unlock_acp() * Decimal(months_after_cliff)
            if unlocked > creator_total_acp:
                unlocked = creator_total_acp
        locked = creator_total_acp - unlocked
        if locked < 0:
            locked = Decimal(0)
        return (unlocked, locked)

    rpc_url = _require_acp_rpc_url()
    try:
        bh = _rpc_call(rpc_url, "getblockhash", {"height": 1}, timeout_s=_INTERACTIVE_RPC_TIMEOUT_S)
        block = _rpc_call(rpc_url, "getblock", {"blockhash": bh, "verbose": 2}, timeout_s=_INTERACTIVE_RPC_TIMEOUT_S) or {}
    except HTTPException:
        return None
    txs = block.get("tx") or []
    if not txs:
        _creator_vesting_genesis_cache.update(
            {"expires_at": now_mono + 300.0, "eligible": False, "creator_address": None, "genesis_time": 0}
        )
        return None
    genesis_tx = txs[0] or {}
    outputs = genesis_tx.get("vout") or []
    if not outputs:
        _creator_vesting_genesis_cache.update(
            {"expires_at": now_mono + 300.0, "eligible": False, "creator_address": None, "genesis_time": 0}
        )
        return None
    vout0 = outputs[0] or {}
    creator_addr = str(vout0.get("recipient_address") or "").strip()
    try:
        creator_total_units = _json_chain_amount_to_int(vout0.get("amount"))
    except (TypeError, ValueError):
        creator_total_units = 0
    eligible = bool(creator_addr) and creator_total_units == _GENESIS_CREATOR_OUTPUT_UNITS
    genesis_time = int(block.get("time") or 0)
    _creator_vesting_genesis_cache.update(
        {
            "expires_at": now_mono + 300.0,
            "eligible": eligible,
            "creator_address": creator_addr if eligible else None,
            "genesis_time": genesis_time,
        }
    )
    if not eligible or creator_addr != target:
        return None

    creator_total_acp = Decimal(creator_total_units) / Decimal(100_000_000)
    now = int(now_ts or datetime.now(timezone.utc).timestamp())

    if now <= genesis_time:
        return (Decimal(0), creator_total_acp)

    elapsed = now - genesis_time
    seconds_per_month = 30 * 24 * 60 * 60
    cliff_months = 12
    linear_months = 72

    if elapsed <= cliff_months * seconds_per_month:
        unlocked = Decimal(0)
    else:
        months_after_cliff = min((elapsed - cliff_months * seconds_per_month) // seconds_per_month, linear_months)
        unlocked = _creator_vesting_monthly_unlock_acp() * Decimal(months_after_cliff)
        if unlocked > creator_total_acp:
            unlocked = creator_total_acp
    locked = creator_total_acp - unlocked
    if locked < 0:
        locked = Decimal(0)
    return (unlocked, locked)


def _probe_source_failed(raw: dict | None) -> bool:
    return str((raw or {}).get("source") or "") in {"timeout", "error", "degraded", "unavailable"}


async def _privacy_receive_snapshot(
    session: AsyncSession,
    user_id: str,
    primary_address: str,
) -> tuple[Decimal | None, list[str]]:
    """Sum live UTXOs on this login's one-time receive addresses.

    The primary deposit address is excluded so it is not counted twice.
    None means a registered address could not be probed; do not treat that as zero.
    """
    rows = (
        await session.execute(
            select(UserAcpPrivacyAddress.address).where(UserAcpPrivacyAddress.user_id == user_id)
        )
    ).all()
    primary = (primary_address or "").strip()
    addresses: list[str] = []
    seen: set[str] = set()
    for (addr,) in rows:
        cleaned = (addr or "").strip()
        if not cleaned or cleaned == primary or cleaned in seen:
            continue
        seen.add(cleaned)
        addresses.append(cleaned)
        if len(addresses) >= privacy_svc.DEFAULT_SUBADDR_SCAN_WINDOW:
            break
    if not addresses:
        return Decimal(0), []
    total = Decimal(0)
    for addr in addresses:
        try:
            probed = _load_balance_result(addr, interactive=True)
        except HTTPException:
            return None, addresses
        if _probe_source_failed(probed):
            return None, addresses
        total += _parse_decimal_or_zero(probed.get("acp"))
    return total, addresses


def _chain_height_from_raw(raw: dict) -> int | None:
    for key in ("chain_height", "height", "block_height"):
        val = raw.get(key)
        if val is None or val == "":
            continue
        try:
            return int(val)
        except (TypeError, ValueError):
            continue
    return None


async def _decorate_balance_for_user(
    session: AsyncSession,
    user_id: str,
    raw: dict,
    *,
    include_in_work: bool,
) -> AcpBalanceResponse:
    on_chain_acp = _parse_decimal_or_zero(raw.get("acp"))
    deposit_probe_failed = _probe_source_failed(raw)
    if deposit_probe_failed:
        # Never treat a failed probe empty payload as a confirmed live zero.
        on_chain_acp = Decimal(0)
    if include_in_work:
        in_work_acp, in_staked, in_ledger = await _in_work_breakdown_for_user(session, user_id)
        balance_view = (
            _custodial_balance_view
            if str(raw.get("address") or "").strip() == CUSTODIAL_HOT_ADDRESS
            else _personal_balance_view
        )
        real_acp, in_work_acp, available_acp = balance_view(
            on_chain_acp, in_staked, in_ledger
        )
    else:
        in_work_acp = in_staked = in_ledger = Decimal(0)
        real_acp = on_chain_acp
        available_acp = on_chain_acp
    in_work_staked_s = _decimal_to_api_str(in_staked) if include_in_work else None
    in_work_ledger_s = _decimal_to_api_str(in_ledger) if include_in_work else None
    vested_unlocked_acp: str | None = None
    vested_locked_acp: str | None = None
    target_address = str(raw.get("address") or "").strip()
    if target_address:
        try:
            vest = _creator_vesting_snapshot(target_address)
        except HTTPException:
            vest = None
        if vest is not None:
            vested_unlocked_acp = _decimal_to_api_str(vest[0])
            vested_locked_acp = _decimal_to_api_str(vest[1])
    on_chain_s = (
        _decimal_to_api_str(on_chain_acp)
        if include_in_work and on_chain_acp != real_acp
        else None
    )
    display_acp = real_acp
    display_units = _units_from_acp(real_acp)
    display_utxo_count = int(raw.get("utxo_count") or 0) if not deposit_probe_failed else 0
    tokenomics_buckets: list[AcpTokenomicsBucket] | None = None
    view_mode: str | None = None
    platform_credits_s: str | None = None
    balance_note = _format_balance_note(real_acp, in_work_acp, available_acp)

    operator_hot_live: Decimal | None = None
    operator_controlled_live: Decimal | None = None
    chain_supply_acp: Decimal | None = None
    supply_cap_acp: Decimal | None = None
    supply_invariant_ok: bool | None = None
    primary_kind: str | None = None
    primary_acp_val: Decimal | None = None
    withdraw_source: str | None = None
    probe_status: str | None = "live"

    is_hot_holder = bool(include_in_work and await user_is_custodial_hot_holder(session, user_id))
    privacy_acp: Decimal | None = None
    if include_in_work:
        privacy_acp, _privacy_addresses = await _privacy_receive_snapshot(
            session, user_id, target_address
        )

    if is_hot_holder:
        # Designated operator: live probes for hero when available; design total when all fail.
        seed = {target_address: raw} if target_address else None
        slices, live_ok, hot_live, live_total, live_hits, role_total = (
            _operator_controlled_balance_slices(seed_by_address=seed)
        )
        operator_hot_live = hot_live
        operator_controlled_live = live_total
        design_total = sum((s[2] for s in slices), Decimal(0))
        display_utxo_count = sum(s[3] for s in slices if s[4])
        tokenomics_buckets = [
            AcpTokenomicsBucket(
                key=key,
                label=label,
                acp=_decimal_to_api_str(acp),
                utxo_count=utxos,
            )
            for key, label, acp, utxos, _live in slices
        ]
        view_mode = "operator_hot"
        platform_credits_s = _decimal_to_api_str(in_ledger)
        # Deposit address probe only — never the operator aggregate.
        on_chain_s = (
            None
            if deposit_probe_failed
            else _decimal_to_api_str(on_chain_acp)
        )
        # Personal deposit UTXOs remain spendable with the account keystore.
        # One-time privacy receives spend with the same keystore and belong to this login.
        personal_available = Decimal(0)
        if target_address and target_address != CUSTODIAL_HOT_ADDRESS and not deposit_probe_failed and privacy_acp is not None:
            _, _, personal_available = _personal_balance_view(
                on_chain_acp + privacy_acp, in_staked, in_ledger
            )
        personal_spendable = personal_available
        # Custodial hot float is spendable via server custodial-hot keystore (hot holders only).
        if hot_live > 0:
            available_acp = hot_live
            withdraw_source = "custodial_hot"
        elif personal_spendable > 0:
            available_acp = personal_spendable
            withdraw_source = "personal_utxo"
        else:
            available_acp = Decimal(0)
            withdraw_source = "none"
        supply_state = _chain_supply_info()
        if supply_state is not None:
            chain_supply_acp = Decimal(str(supply_state["utxo_supply_acp"]))
            supply_cap_acp = Decimal(str(supply_state["max_supply_acp"]))
            supply_invariant_ok = True
            primary_kind = "chain_supply"
            primary_acp_val = chain_supply_acp
            display_acp = chain_supply_acp
            display_units = str(supply_state["utxo_supply_units"])
            probe_status = "live" if live_hits == role_total else "degraded"
            source_note = (
                f"stateful node invariant verified at height "
                f"{int(supply_state.get('height') or 0)}"
            )
        elif live_ok:
            primary_kind = "operator_total"
            primary_acp_val = live_total
            display_acp = live_total
            display_units = _units_from_acp(live_total)
            if live_hits < role_total:
                probe_status = "degraded"
            else:
                probe_status = "live"
            source_note = (
                f"live UTXO probes ({live_hits}/{role_total}; "
                "zeros preserved; design only in buckets for unavailable probes)"
            )
        else:
            primary_kind = "operator_total"
            # Ledger balances are claims on the existing supply, never additive
            # issuance. Keep them separate even while live RPC is unavailable.
            primary_acp_val = design_total
            display_acp = design_total
            display_units = _units_from_acp(design_total)
            probe_status = "unavailable"
            source_note = (
                "all live probes unavailable — showing the 210M design allocation; "
                "confirm live floats when RPC recovers"
            )
        balance_note = (
            (
                f"On-chain UTXO supply: {_decimal_to_api_str(chain_supply_acp)} ACP "
                f"of {_decimal_to_api_str(supply_cap_acp)} ACP hard cap ({source_note}). "
                f"Visible operator role wallets: {_decimal_to_api_str(live_total)} ACP. "
                if chain_supply_acp is not None and supply_cap_acp is not None
                else
                f"Operator-controlled total: "
                f"{_decimal_to_api_str(live_total) if live_ok else _decimal_to_api_str(display_acp)} ACP "
                f"({source_note}). "
            )
            +
            f"Withdraw from this login uses custodial hot float "
            f"({_decimal_to_api_str(hot_live)} ACP hot"
            f"{f'; + {_decimal_to_api_str(personal_available)} ACP personal UTXO' if personal_available > 0 else ''}"
            f"{f'; + {_decimal_to_api_str(privacy_acp)} ACP privacy receive' if privacy_acp else ''}"
            f"; {_decimal_to_api_str(available_acp)} ACP available now). "
            f"PQC KeystoreV3 (Ed25519+Dilithium2); amounts are transparent on-chain."
        )
        if target_address != CUSTODIAL_HOT_ADDRESS and hot_live > 0:
            balance_note += (
                " Deposit address is personal — hot float spends use the server custodial-hot keystore "
                "after wallet-password auth (no re-bind required)."
            )
    elif include_in_work and target_address == CUSTODIAL_HOT_ADDRESS:
        # Accidental hot binding for a normal user: never show operator pool as theirs.
        platform_credits_s = _decimal_to_api_str(in_ledger)
        display_acp = in_ledger if in_ledger > 0 else Decimal(0)
        display_units = _units_from_acp(display_acp)
        display_utxo_count = 0
        available_acp = Decimal(0)
        in_work_acp = in_staked + in_ledger
        on_chain_s = "0" if not deposit_probe_failed else None
        view_mode = None
        tokenomics_buckets = None
        withdraw_source = "none"
        if in_ledger > 0:
            primary_kind = "platform_credits"
            primary_acp_val = in_ledger
        else:
            primary_kind = "on_chain"
            primary_acp_val = Decimal(0) if not deposit_probe_failed else None
        if deposit_probe_failed:
            probe_status = "unavailable"
        balance_note = (
            "This account was incorrectly bound to the shared custodial hot wallet. "
            "Showing platform ledger credits only. Create a personal deposit address "
            "(re-login or use Personalize wallet) — do not send funds to the hot address."
        )

    # Regular users: always expose ledger credits separately from on-chain.
    # Hero prefers platform credits when on-chain is 0 and ledger > 0.
    if include_in_work and target_address != CUSTODIAL_HOT_ADDRESS and not is_hot_holder:
        visible_chain = on_chain_acp + (privacy_acp or Decimal(0))
        _, _, available_acp = _personal_balance_view(visible_chain, in_staked, in_ledger)
        if privacy_acp is None:
            available_acp = Decimal(0)
            probe_status = "degraded"
        platform_credits_s = _decimal_to_api_str(in_ledger)
        on_chain_s = None if deposit_probe_failed else _decimal_to_api_str(on_chain_acp)
        if deposit_probe_failed:
            probe_status = "unavailable" if str(raw.get("source") or "") in {
                "timeout",
                "error",
                "unavailable",
            } else "degraded"
        if visible_chain <= 0 and in_ledger > 0:
            display_acp = in_ledger
            display_units = _units_from_acp(in_ledger)
            primary_kind = "platform_credits"
            primary_acp_val = in_ledger
            balance_note = (
                f"On-chain: {'unavailable' if deposit_probe_failed else _decimal_to_api_str(on_chain_acp)} ACP. "
                f"Platform credits: {_decimal_to_api_str(in_ledger)} ACP (ledger). "
                f"Withdrawable on-chain: {_decimal_to_api_str(available_acp)} ACP."
            )
        else:
            display_acp = visible_chain
            display_units = _units_from_acp(display_acp)
            primary_kind = "on_chain"
            primary_acp_val = (
                None if deposit_probe_failed and on_chain_acp <= 0 and in_ledger <= 0 else display_acp
            )
            balance_note = (
                f"On-chain: {'unavailable' if deposit_probe_failed else _decimal_to_api_str(on_chain_acp)} ACP. "
                f"Platform credits: {_decimal_to_api_str(in_ledger)} ACP. "
                f"Available to withdraw: {_decimal_to_api_str(available_acp)} ACP."
            )
        if available_acp > 0:
            withdraw_source = "personal_utxo"
        else:
            withdraw_source = "none"

    if primary_kind is None:
        # Non-include_in_work path (foreign address probe).
        primary_kind = "on_chain"
        primary_acp_val = None if deposit_probe_failed else display_acp
        withdraw_source = "personal_utxo" if available_acp > 0 else "none"
        if deposit_probe_failed:
            probe_status = "unavailable"

    if probe_status is None:
        probe_status = "live"

    balance_status = "live"
    if probe_status in {"degraded", "unavailable"}:
        balance_status = "degraded"
    elif include_in_work and on_chain_acp <= 0 and int(raw.get("utxo_count") or 0) == 0:
        if deposit_probe_failed:
            balance_status = "degraded"

    on_chain_at_deposit_s = (
        None if deposit_probe_failed else (on_chain_s if on_chain_s is not None else _decimal_to_api_str(on_chain_acp))
    )
    platform_ledger_s = platform_credits_s
    staked_s = in_work_staked_s
    reserved_s = _decimal_to_api_str(in_work_acp) if include_in_work else None
    withdrawable_s = _decimal_to_api_str(available_acp)
    primary_s = _decimal_to_api_str(primary_acp_val) if primary_acp_val is not None else None

    return AcpBalanceResponse(
        address=str(raw.get("address") or ""),
        units=display_units,
        acp=_decimal_to_api_str(display_acp),
        utxo_count=display_utxo_count,
        on_chain_acp=on_chain_at_deposit_s if on_chain_at_deposit_s is not None else (
            None if deposit_probe_failed else _decimal_to_api_str(on_chain_acp)
        ),
        ledger_credits_acp=platform_credits_s,
        headline_acp=_decimal_to_api_str(display_acp) if primary_acp_val is not None else None,
        in_work_acp=_decimal_to_api_str(in_work_acp),
        in_work_staked_acp=in_work_staked_s,
        in_work_ledger_acp=in_work_ledger_s,
        available_acp=withdrawable_s,
        platform_credits_acp=platform_credits_s,
        tokenomics_buckets=tokenomics_buckets,
        view_mode=view_mode if view_mode else "user",
        balance_status=balance_status,
        vested_unlocked_acp=vested_unlocked_acp,
        vested_locked_acp=vested_locked_acp,
        balance_note=balance_note,
        on_chain_at_deposit_acp=on_chain_at_deposit_s,
        privacy_receive_acp=(
            _decimal_to_api_str(privacy_acp) if include_in_work and privacy_acp is not None else None
        ),
        platform_ledger_acp=platform_ledger_s,
        staked_acp=staked_s,
        reserved_total_acp=reserved_s,
        withdrawable_now_acp=withdrawable_s,
        withdraw_source=withdraw_source,  # type: ignore[arg-type]
        operator_hot_live_acp=(
            _decimal_to_api_str(operator_hot_live) if operator_hot_live is not None else None
        ),
        operator_controlled_live_acp=(
            _decimal_to_api_str(operator_controlled_live)
            if operator_controlled_live is not None
            else None
        ),
        chain_supply_acp=(
            _decimal_to_api_str(chain_supply_acp) if chain_supply_acp is not None else None
        ),
        supply_cap_acp=(
            _decimal_to_api_str(supply_cap_acp) if supply_cap_acp is not None else None
        ),
        supply_invariant_ok=supply_invariant_ok,
        primary_acp=primary_s,
        primary_kind=primary_kind,  # type: ignore[arg-type]
        probe_status=probe_status,  # type: ignore[arg-type]
        chain_height=_chain_height_from_raw(raw),
    )


def _rpc_call(
    rpc_url: str,
    method: str,
    params: list | dict | None = None,
    *,
    timeout_s: float | None = None,
):
    from app.services.acp_rpc import acp_rpc_headers

    body = {"jsonrpc": "2.0", "id": "wallet-acp-history", "method": method, "params": params or []}
    try:
        r = httpx.post(
            rpc_url,
            json=body,
            headers=acp_rpc_headers(),
            timeout=float(timeout_s if timeout_s is not None else 30.0),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"ACP RPC request failed: {exc}")
    try:
        payload = r.json()
    except Exception:
        raise HTTPException(status_code=502, detail=f"ACP RPC returned non-JSON response: {(r.text or '')[:160]}")
    if r.status_code != 200:
        detail = payload.get("error") if isinstance(payload, dict) else None
        raise HTTPException(status_code=502, detail=f"ACP RPC status {r.status_code}: {detail or 'unknown'}")
    if payload.get("error"):
        raise HTTPException(status_code=502, detail=f"ACP RPC error: {payload['error']}")
    return payload.get("result")


def _chain_supply_info(*, required: bool = False) -> dict | None:
    """Load and independently verify the node's stateful supply counters."""
    try:
        raw = _rpc_call(
            _require_acp_rpc_url(),
            "gettxoutsetinfo",
            [],
            timeout_s=_INTERACTIVE_RPC_TIMEOUT_S,
        )
        if not isinstance(raw, dict):
            raise ValueError("missing gettxoutsetinfo result")
        maximum = int(str(raw.get("max_supply_units") or ""))
        issued = int(str(raw.get("issued_supply_units") or ""))
        unspent = int(str(raw.get("utxo_supply_units") or ""))
        initialized = bool(raw.get("initialized"))
        reported_ok = raw.get("supply_invariant_ok") is True
        valid = (
            initialized
            and reported_ok
            and maximum == _ACP_SUPPLY_CAP_UNITS
            and issued == maximum
            and 0 <= unspent <= issued
        )
        if not valid:
            raise ValueError(
                f"invalid ACP supply state (initialized={initialized}, max={maximum}, "
                f"issued={issued}, unspent={unspent}, reported_ok={reported_ok})"
            )
        return {
            **raw,
            "max_supply_units": maximum,
            "issued_supply_units": issued,
            "utxo_supply_units": unspent,
        }
    except Exception as exc:
        if required:
            raise HTTPException(
                status_code=503,
                detail=f"ACP transfers are paused: supply invariant unavailable or invalid ({exc})",
            ) from exc
        return None


def _rpc_balance_for_address(address: str) -> dict:
    target = (address or "").strip()
    if not target:
        raise HTTPException(status_code=400, detail="address is required")

    now = time.monotonic()
    cached = _chain_balance_cache.get(target)
    if cached is not None:
        expires_at, payload = cached
        if now < expires_at:
            return dict(payload)

    rpc_url = _require_acp_rpc_url()
    best_height = int(_rpc_call(rpc_url, "getblockcount", []) or 0)
    if best_height <= 0:
        payload = {"address": target, "units": "0", "acp": "0", "utxo_count": 0}
        _chain_balance_cache[target] = (now + _CHAIN_BALANCE_CACHE_TTL_S, payload)
        return dict(payload)

    unspent: dict[str, int] = {}
    spent: set[str] = set()

    for height in range(1, best_height + 1):
        block_hash = _rpc_call(rpc_url, "getblockhash", {"height": height})
        block = _rpc_call(rpc_url, "getblock", {"blockhash": block_hash, "verbose": 2}) or {}
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
                key = f"{prev_txid}:{int(prev_vout)}"
                spent.add(key)
                unspent.pop(key, None)

            for idx, vout in enumerate(tx.get("vout") or []):
                out_addr = str(vout.get("recipient_address") or "")
                if out_addr != target:
                    continue
                key = f"{txid}:{idx}"
                if key in spent:
                    continue
                unspent[key] = _json_chain_amount_to_int(vout.get("amount"))

    units = sum(unspent.values())
    payload = {
        "address": target,
        "units": str(units),
        "acp": _units_to_acp_str(units),
        "utxo_count": len(unspent),
    }
    _chain_balance_cache[target] = (time.monotonic() + _CHAIN_BALANCE_CACHE_TTL_S, payload)
    return dict(payload)


def _empty_balance_payload(address: str, *, source: str = "error") -> dict:
    return {
        "address": address,
        "units": "0",
        "acp": "0",
        "utxo_count": 0,
        "source": source,
    }


def _probe_role_wallet(address: str, *, timeout_s: int) -> tuple[Decimal, int, bool]:
    """Return (acp, utxo_count, probe_ok). probe_ok=False means timeout/unavailable."""
    target = (address or "").strip()
    if not target:
        return Decimal(0), 0, False

    now = time.monotonic()
    cached = _chain_balance_cache.get(target)
    if cached is not None:
        expires_at, payload = cached
        if now < expires_at:
            if _probe_source_failed(payload):
                return Decimal(0), 0, False
            return (
                _parse_decimal_or_zero(payload.get("acp")),
                int(payload.get("utxo_count") or 0),
                True,
            )

    # Prefer incremental UTXO index (instant) over full-tip walletd scans.
    try:
        from app.services import acp_utxo_index as utxo_idx

        indexed = utxo_idx.get_indexed_balance(target)
        if indexed is not None:
            _chain_balance_cache[target] = (
                time.monotonic() + _CHAIN_BALANCE_CACHE_TTL_S,
                dict(indexed),
            )
            return (
                _parse_decimal_or_zero(indexed.get("acp")),
                int(indexed.get("utxo_count") or 0),
                True,
            )
    except Exception:
        report_optional_failure('app.api.routers.wallet_acp:_probe_role_wallet:fallback', quiet=False)

    rpc_url = _require_acp_rpc_url()
    try:
        result = _run_walletd(
            ["balance", "--rpc", rpc_url, "--address", target],
            timeout_s=max(1, int(timeout_s)),
        )
    except HTTPException as exc:
        if exc.status_code in (502, 503, 504):
            return Decimal(0), 0, False
        raise

    if not isinstance(result, dict):
        return Decimal(0), 0, False
    if not str(result.get("address") or "").strip():
        result = {**result, "address": target}
    _chain_balance_cache[target] = (time.monotonic() + _CHAIN_BALANCE_CACHE_TTL_S, dict(result))
    return (
        _parse_decimal_or_zero(result.get("acp")),
        int(result.get("utxo_count") or 0),
        True,
    )


def _operator_controlled_balance_slices(
    *,
    seed_by_address: dict[str, dict] | None = None,
) -> tuple[list[tuple[str, str, Decimal, int, bool]], bool, Decimal, Decimal, int, int]:
    """Probe operator role wallets in parallel within a shared time budget.

    Confirmed live zeros are preserved. Design alloc is used only in bucket
    display when a probe is unavailable — never mixed into the live total.

    Returns
    -------
    slices : list of (key, label, acp, utxo_count, is_live)
    used_any_live_probe : bool
    hot_live_acp : Decimal
    live_total_acp : Decimal  (sum of successful probes only)
    live_hits : int
    role_total : int
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    seed_by_address = seed_by_address or {}
    deadline = time.monotonic() + _OPERATOR_AGGREGATE_BUDGET_S
    probed: dict[str, tuple[Decimal, int, bool]] = {}

    for address, raw in seed_by_address.items():
        if not address or not isinstance(raw, dict):
            continue
        # Failed/empty probe payloads must not seed as live zeros — re-probe instead.
        if _probe_source_failed(raw):
            continue
        probed[address] = (
            _parse_decimal_or_zero(raw.get("acp")),
            int(raw.get("utxo_count") or 0),
            True,
        )

    pending = [addr for _, _, addr, _ in OPERATOR_ROLE_WALLETS if addr not in probed]
    if pending:
        remaining = max(1.0, deadline - time.monotonic())
        per_role = max(1, min(_OPERATOR_AGGREGATE_PER_ROLE_S, int(remaining)))

        def _one(addr: str) -> tuple[str, Decimal, int, bool]:
            left = max(1, int(deadline - time.monotonic()))
            acp, utxos, ok = _probe_role_wallet(addr, timeout_s=min(per_role, left))
            return addr, acp, utxos, ok

        with ThreadPoolExecutor(max_workers=min(4, len(pending))) as pool:
            futures = [pool.submit(_one, addr) for addr in pending]
            try:
                for fut in as_completed(futures, timeout=max(1.0, deadline - time.monotonic() + 1.0)):
                    try:
                        addr, acp, utxos, ok = fut.result()
                    except Exception:
                        continue
                    probed[addr] = (acp, utxos, ok)
            except TimeoutError:
                # Shared budget exhausted — unfinished roles fall back to design alloc in buckets only.
                pass

    slices: list[tuple[str, str, Decimal, int, bool]] = []
    live_hits = 0
    hot_live = Decimal(0)
    live_total = Decimal(0)
    role_total = len(OPERATOR_ROLE_WALLETS)
    for key, label, address, design_acp in OPERATOR_ROLE_WALLETS:
        live_acp, utxos, ok = probed.get(address, (Decimal(0), 0, False))
        if ok:
            live_hits += 1
            acp = live_acp
            live_total += live_acp
            bucket_label = label
        else:
            acp = design_acp
            utxos = 0
            bucket_label = f"{label} (design; probe unavailable)"
        if address == CUSTODIAL_HOT_ADDRESS and ok:
            hot_live = live_acp
        elif address == CUSTODIAL_HOT_ADDRESS:
            hot_live = Decimal(0)
        slices.append((key, bucket_label, acp, utxos, ok))
    return slices, live_hits > 0, hot_live, live_total, live_hits, role_total


def _load_balance_result(address: str, *, interactive: bool = True) -> dict:
    """Resolve on-chain balance for an address.

    Interactive wallet requests must never fall back to a full tip UTXO scan
    (tens of thousands of RPC calls). Prefer a short walletd probe, then cache
    zeros so the UI can still show ledger/platform credits immediately.
    """
    target = (address or "").strip()
    if not target:
        raise HTTPException(status_code=400, detail="address is required")

    now = time.monotonic()
    cached = _chain_balance_cache.get(target)
    if cached is not None:
        expires_at, payload = cached
        if now < expires_at:
            return dict(payload)

    rpc_url = _require_acp_rpc_url()
    if interactive:
        # Prefer incremental UTXO index before any walletd tip-scan.
        try:
            from app.services import acp_utxo_index as utxo_idx

            indexed = utxo_idx.get_indexed_balance_sync_prefer_redis(target)
            if indexed is not None and not _probe_source_failed(indexed):
                _chain_balance_cache[target] = (
                    time.monotonic() + _CHAIN_BALANCE_CACHE_TTL_S,
                    dict(indexed),
                )
                return dict(indexed)
        except Exception:
            report_optional_failure('app.api.routers.wallet_acp:_load_balance_result:fallback', quiet=False)
        timeout_s = (
            _OPERATOR_ROLE_WALLETD_TIMEOUT_S
            if target in OPERATOR_ROLE_ADDRESSES
            else _INTERACTIVE_WALLETD_TIMEOUT_S
        )
    else:
        timeout_s = 90
    timed_out = False
    try:
        result = _run_walletd(
            ["balance", "--rpc", rpc_url, "--address", target],
            timeout_s=timeout_s,
        )
        if isinstance(result, dict):
            # Normalize so callers always see the queried address.
            if not str(result.get("address") or "").strip():
                result = {**result, "address": target}
            # Successful probe — strip any stale failure source.
            result = {k: v for k, v in result.items() if k != "source"}
            _chain_balance_cache[target] = (time.monotonic() + _CHAIN_BALANCE_CACHE_TTL_S, dict(result))
            return dict(result)
    except HTTPException as exc:
        if exc.status_code not in (502, 503, 504):
            raise
        timed_out = exc.status_code == 504
        if not interactive:
            return _rpc_balance_for_address(target)

    # Fast fail-closed for wallet UI: ledger decoration still surfaces credits.
    # Prefer durable indexed balances over empty timeout payloads.
    try:
        from app.services import acp_utxo_index as utxo_idx

        indexed = utxo_idx.get_indexed_balance_sync_prefer_redis(target)
        if indexed is not None and not _probe_source_failed(indexed):
            return dict(indexed)
    except Exception:
        report_optional_failure('app.api.routers.wallet_acp:_load_balance_result:fallback', quiet=False)
    # Do not sticky-cache empty results after a timeout — that made real hot
    # floats look like 0 / tiny until the process restarted.
    # Mark source so decorate never treats empty error payloads as live zeros.
    payload = _empty_balance_payload(target, source="timeout" if timed_out else "error")
    if not timed_out:
        _chain_balance_cache[target] = (
            time.monotonic() + _CHAIN_BALANCE_NEGATIVE_CACHE_TTL_S,
            payload,
        )
    return dict(payload)


def _to_public_order(order: dict) -> AcpSwapOrderPublic:
    return AcpSwapOrderPublic(**order)


def _swap_row_to_dict(row: AcpSwapOrder) -> dict:
    return {
        "id": str(row.id),
        "user_id": str(row.user_id),
        "status": str(row.status),
        "usdt_trc20_amount": _decimal_to_api_str(_parse_decimal_or_zero(row.usdt_trc20_amount)),
        "rate_acp_per_usdt": _decimal_to_api_str(_parse_decimal_or_zero(row.rate_acp_per_usdt)),
        "estimated_acp_amount": _decimal_to_api_str(_parse_decimal_or_zero(row.estimated_acp_amount)),
        "payout_acp_address": str(row.payout_acp_address),
        "deposit_trc20_address": str(row.deposit_trc20_address),
        "deposit_reference": str(row.deposit_reference),
        "tron_txid": row.tron_txid,
        "payout_txid": row.payout_txid,
        "note": row.note,
        "created_at": (row.created_at or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z"),
        "updated_at": (row.updated_at or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z"),
    }


async def _get_user_wallet_signer(session: AsyncSession, user_id: str, wallet_password: str) -> dict[str, str]:
    wallet = await get_wallet_for_user(session, user_id)
    if wallet is None:
        raise HTTPException(
            status_code=409,
            detail="ACP wallet is not initialized for this account. Please sign in again.",
        )
    try:
        secret = decrypt_mnemonic(
            encrypted_mnemonic=wallet.encrypted_mnemonic,
            salt_b64=wallet.salt_b64,
            nonce_b64=wallet.nonce_b64,
            password=wallet_password,
        )
        mnemonic, keystore_json = decode_wallet_secret(secret)
        if keystore_json:
            return {"keystore_json": keystore_json, "mnemonic": mnemonic}
        return {"mnemonic": mnemonic}
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid wallet password")


def _hot_mnemonic_path() -> Path:
    p = os.getenv("ACP_HOT_MNEMONIC_FILE", "/run/secrets/acp_hot_mnemonic.txt")
    return Path(p)


def _hot_keystore_path() -> Path:
    p = os.getenv("ACP_HOT_KEYSTORE_FILE", "/run/secrets/acp_hot_keystore.json")
    return Path(p)


def _custodial_hot_keystore_candidates() -> list[Path]:
    """Paths for the custodial hot signer — never bridge-reserve ACP_HOT_* material."""
    env_file = (os.getenv("ACP_CUSTODIAL_HOT_KEYSTORE_FILE") or "").strip()
    paths: list[Path] = []
    if env_file:
        paths.append(Path(env_file))
    paths.extend(
        [
            Path("/run/secrets/custodial-hot.keystore.json"),
            Path("/run/secrets/wallets-canonical/custodial-hot.keystore.json"),
        ]
    )
    # Deduplicate while preserving order.
    seen: set[str] = set()
    out: list[Path] = []
    for p in paths:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def _load_custodial_hot_signer() -> tuple[list[str], str]:
    """
    Strict signer for CUSTODIAL_HOT_ADDRESS only.

    Must not fall back to ACP_HOT_* (bridge reserve). Returns (walletd_args, address).
    """
    env_json = (os.getenv("ACP_CUSTODIAL_HOT_KEYSTORE_JSON") or "").strip()
    if env_json:
        derived = _run_walletd(["address", "--keystore-json", env_json], timeout_s=60)
        address = str(derived.get("address") or "").strip()
        if address != CUSTODIAL_HOT_ADDRESS:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"ACP_CUSTODIAL_HOT_KEYSTORE_JSON derives {address or 'empty'}, "
                    f"expected {CUSTODIAL_HOT_ADDRESS}"
                ),
            )
        return (["--keystore-json", env_json], address)

    last_missing: str | None = None
    for path in _custodial_hot_keystore_candidates():
        if not path.exists():
            last_missing = str(path)
            continue
        keystore_json = path.read_text(encoding="utf-8").strip()
        if not keystore_json:
            continue
        derived = _run_walletd(["address", "--keystore-json", keystore_json], timeout_s=60)
        address = str(derived.get("address") or "").strip()
        if address != CUSTODIAL_HOT_ADDRESS:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Custodial hot keystore at {path} derives {address or 'empty'}, "
                    f"expected {CUSTODIAL_HOT_ADDRESS}"
                ),
            )
        return (["--keystore-json", keystore_json], address)

    raise HTTPException(
        status_code=503,
        detail=(
            "Custodial hot keystore is not configured on this host "
            f"(tried ACP_CUSTODIAL_HOT_KEYSTORE_FILE / default secrets"
            f"{f'; last missing {last_missing}' if last_missing else ''}). "
            "Place KeystoreV3 for acp1qzfdkq… at /run/secrets/custodial-hot.keystore.json."
        ),
    )


def _normalize_mnemonic_text(raw: str) -> str:
    return " ".join([w for w in str(raw or "").split() if w.strip()])


def _load_or_create_hot_mnemonic() -> str:
    env = os.getenv("ACP_HOT_MNEMONIC", "").strip()
    if env:
        return _normalize_mnemonic_text(env)
    p = _hot_mnemonic_path()
    if p.exists():
        txt = p.read_text(encoding="utf-8").strip()
        words = [w for w in txt.split() if w.strip()]
        if len(words) in (12, 15, 18, 21, 24):
            return " ".join(words)
        # Corrupt/partial file: regenerate to keep wallet usable.
        try:
            p.rename(p.with_suffix(p.suffix + ".bad"))
        except Exception:
            report_optional_failure('app.api.routers.wallet_acp:_load_or_create_hot_mnemonic:p.rename', quiet=False)
    p.parent.mkdir(parents=True, exist_ok=True)
    created = _run_walletd(["new"])
    mnemonic = _normalize_mnemonic_text(str(created["mnemonic"]))
    p.write_text(mnemonic + "\n", encoding="utf-8")
    return mnemonic


def _load_or_create_valid_hot_mnemonic() -> str:
    """
    Ensure mnemonic is not only structurally valid, but also accepted by walletd.
    If corrupted (e.g. bad checksum), rotate broken file and regenerate.
    """
    mnemonic = _load_or_create_hot_mnemonic()
    try:
        _run_walletd(["address", "--mnemonic", mnemonic])
        return mnemonic
    except HTTPException as exc:
        if "mnemonic" not in str(exc.detail).lower():
            raise
        p = _hot_mnemonic_path()
        if p.exists():
            try:
                p.rename(p.with_suffix(p.suffix + ".bad"))
            except Exception:
                report_optional_failure('app.api.routers.wallet_acp:_load_or_create_valid_hot_mnemonic:p.rename', quiet=False)
        created = _run_walletd(["new"])
        new_mnemonic = _normalize_mnemonic_text(str(created["mnemonic"]))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(new_mnemonic + "\n", encoding="utf-8")
        _run_walletd(["address", "--mnemonic", new_mnemonic])
        return new_mnemonic


def _load_existing_valid_hot_mnemonic() -> str:
    """
    Strict bridge/operator loader for mnemonic-based signers.
    Never creates or rotates signer material implicitly.
    Operator secrets must fail closed, not mutate themselves.
    """
    env = os.getenv("ACP_HOT_MNEMONIC", "").strip()
    if env:
        mnemonic = _normalize_mnemonic_text(env)
        if len(mnemonic.split()) not in (12, 15, 18, 21, 24):
            raise HTTPException(status_code=500, detail="ACP_HOT_MNEMONIC is malformed")
        _run_walletd(["address", "--mnemonic", mnemonic])
        return mnemonic

    p = _hot_mnemonic_path()
    if not p.exists():
        raise HTTPException(status_code=500, detail=f"ACP hot mnemonic file is missing: {p}")

    txt = p.read_text(encoding="utf-8").strip()
    words = [w for w in txt.split() if w.strip()]
    if len(words) not in (12, 15, 18, 21, 24):
        raise HTTPException(status_code=500, detail=f"ACP hot mnemonic file is malformed: {p}")

    mnemonic = " ".join(words)
    _run_walletd(["address", "--mnemonic", mnemonic])
    return mnemonic


def _load_existing_valid_hot_signer() -> tuple[list[str], str]:
    """
    Strict bridge/operator signer loader.
    Prefers keystore because ACP hybrid identities include PQC material that is not
    reproducible from mnemonic alone. Falls back to mnemonic only when no keystore is configured.
    Returns (walletd_signer_args, derived_address).
    """
    env_keystore = os.getenv("ACP_HOT_KEYSTORE_JSON", "").strip()
    if env_keystore:
        derived = _run_walletd(["address", "--keystore-json", env_keystore])
        address = str(derived.get("address") or "").strip()
        if not address:
            raise HTTPException(status_code=500, detail="ACP hot keystore env did not derive an address")
        return (["--keystore-json", env_keystore], address)

    keystore_file = os.getenv("ACP_HOT_KEYSTORE_FILE", "").strip()
    if keystore_file:
        p = Path(keystore_file)
        if not p.exists():
            raise HTTPException(status_code=500, detail=f"ACP hot keystore file is missing: {p}")
        keystore_json = p.read_text(encoding="utf-8").strip()
        if not keystore_json:
            raise HTTPException(status_code=500, detail=f"ACP hot keystore file is empty: {p}")
        derived = _run_walletd(["address", "--keystore-json", keystore_json])
        address = str(derived.get("address") or "").strip()
        if not address:
            raise HTTPException(status_code=500, detail=f"ACP hot keystore file did not derive an address: {p}")
        return (["--keystore-json", keystore_json], address)

    mnemonic = _load_existing_valid_hot_mnemonic()
    derived = _run_walletd(["address", "--mnemonic", mnemonic])
    address = str(derived.get("address") or "").strip()
    if not address:
        raise HTTPException(status_code=500, detail="ACP hot mnemonic did not derive an address")
    return (["--mnemonic", mnemonic], address)


def _build_chain_scan_data() -> tuple[int, dict[tuple[str, int], tuple[str, int]], dict[str, dict]]:
    """Full tip scan — expensive; only call from the background warmer."""
    rpc_url = _require_acp_rpc_url()
    best_height = int(
        _rpc_call(rpc_url, "getblockcount", [], timeout_s=_INTERACTIVE_RPC_TIMEOUT_S) or 0
    )
    if best_height <= 0:
        return (0, {}, {})

    out_index: dict[tuple[str, int], tuple[str, int]] = {}
    tx_index: dict[str, dict] = {}

    for height in range(1, best_height + 1):
        block_hash = _rpc_call(rpc_url, "getblockhash", {"height": height})
        block = _rpc_call(rpc_url, "getblock", {"blockhash": block_hash, "verbose": 2}) or {}
        block_time = int(block.get("time") or 0)
        txs = block.get("tx") or []

        for tx in txs:
            txid = str(tx.get("txid") or "")
            if not txid:
                continue

            inputs: list[dict] = []
            total_input_units = 0
            for vin in tx.get("vin") or []:
                prev_txid = vin.get("prev_txid")
                prev_vout = vin.get("vout")
                if prev_txid is None or prev_vout is None:
                    continue
                key = (str(prev_txid), int(prev_vout))
                prev_out = out_index.get(key)
                prev_address = prev_out[0] if prev_out else None
                prev_units = int(prev_out[1]) if prev_out else 0
                total_input_units += prev_units
                inputs.append(
                    {
                        "address": prev_address,
                        "units": prev_units,
                        "vout": int(prev_vout),
                    }
                )

            outputs: list[dict] = []
            total_output_units = 0
            for idx, vout in enumerate(tx.get("vout") or []):
                out_addr = str(vout.get("recipient_address") or "")
                out_amount = _json_chain_amount_to_int(vout.get("amount"))
                out_index[(txid, idx)] = (out_addr, out_amount)
                total_output_units += out_amount
                outputs.append(
                    {
                        "address": out_addr or None,
                        "units": out_amount,
                        "vout": idx,
                    }
                )

            tx_index[txid] = {
                "txid": txid,
                "block_height": height,
                "block_hash": str(block_hash),
                "block_time": _acp_timestamp(block_time) if block_time > 0 else _utc_now_iso(),
                "confirmations": (best_height - height + 1),
                "inputs": inputs,
                "outputs": outputs,
                "total_input_units": total_input_units,
                "total_output_units": total_output_units,
                "fee_units": max(total_input_units - total_output_units, 0),
            }

    return (best_height, out_index, tx_index)


def _warm_chain_scan_cache() -> None:
    try:
        data = _build_chain_scan_data()
        _chain_scan_cache["data"] = data
        _chain_scan_cache["expires_at"] = time.monotonic() + _CHAIN_SCAN_CACHE_TTL_S
        try:
            from app.services import acp_utxo_index as utxo_idx

            best_height, out_index, _tx_index = data
            utxo_idx.seed_from_out_index(out_index, height=int(best_height or 0))
        except Exception:
            report_optional_failure('app.api.routers.wallet_acp:_warm_chain_scan_cache:fallback', quiet=False)
    except Exception:
        # Keep previous cache if any; interactive callers already returned [].
        pass
    finally:
        with _chain_scan_lock:
            _chain_scan_state["inflight"] = False


def _schedule_chain_scan_warm() -> None:
    with _chain_scan_lock:
        if _chain_scan_state["inflight"]:
            return
        _chain_scan_state["inflight"] = True
    threading.Thread(target=_warm_chain_scan_cache, name="acp-chain-scan-warm", daemon=True).start()


def _scan_chain_transactions(*, interactive: bool = True) -> tuple[int, dict[tuple[str, int], tuple[str, int]], dict[str, dict]]:
    now = time.monotonic()
    cached = _chain_scan_cache.get("data")
    expires_at = float(_chain_scan_cache.get("expires_at") or 0.0)
    if cached is not None and now < expires_at:
        return cached  # type: ignore[return-value]

    # Prefer stale cache over silent empty while a warm is in flight.
    stale = cached if cached is not None else None

    if interactive:
        _schedule_chain_scan_warm()
        if stale is not None:
            return stale  # type: ignore[return-value]
        raise HTTPException(status_code=503, detail="ACP chain history index is warming")

    data = _build_chain_scan_data()
    _chain_scan_cache["data"] = data
    _chain_scan_cache["expires_at"] = time.monotonic() + _CHAIN_SCAN_CACHE_TTL_S
    return data


def _chain_transactions_for_address(
    address: str, limit: int
) -> tuple[list[AcpTransactionPublic], bool]:
    """Return (rows, warming). warming=True when serving stale/empty while index rebuilds."""
    warming = False
    try:
        best_height, _out_index, tx_index = _scan_chain_transactions(interactive=True)
    except HTTPException as exc:
        if exc.status_code == 503:
            warming = True
            best_height, tx_index = 0, {}
        else:
            raise
    else:
        expires_at = float(_chain_scan_cache.get("expires_at") or 0.0)
        with _chain_scan_lock:
            inflight = bool(_chain_scan_state.get("inflight"))
        if inflight and time.monotonic() >= expires_at:
            warming = True

    if best_height <= 0:
        return [], warming

    rows: list[AcpTransactionPublic] = []

    for tx in tx_index.values():
        sent_units = sum(int(i.get("units") or 0) for i in tx["inputs"] if i.get("address") == address)
        received_units = sum(int(o.get("units") or 0) for o in tx["outputs"] if o.get("address") == address)

        if sent_units == 0 and received_units == 0:
            continue

        net_units = received_units - sent_units
        if sent_units > 0 and received_units > 0 and net_units == 0:
            direction = "self"
        elif net_units < 0:
            direction = "out"
        else:
            direction = "in"

        rows.append(
            AcpTransactionPublic(
                txid=tx["txid"],
                block_height=int(tx["block_height"]),
                block_time=str(tx["block_time"]),
                confirmations=int(tx["confirmations"]),
                direction=direction,
                sent_units=str(sent_units),
                sent_acp=_units_to_acp_str(sent_units),
                received_units=str(received_units),
                received_acp=_units_to_acp_str(received_units),
                net_units=str(net_units),
                net_acp=_units_to_acp_str(net_units),
            )
        )

    rows.sort(key=lambda x: (x.block_height, x.txid), reverse=True)
    return rows[:limit], warming


def _mobile_acp_tx_to_public(row: MobileAcpTx) -> AcpTransactionPublic:
    sent = int(row.sent_units or 0)
    received = int(row.received_units or 0)
    net = int(row.net_units if row.net_units is not None else (received - sent))
    direction = str(row.direction or "in")
    if direction not in ("in", "out", "self"):
        direction = "in"
    return AcpTransactionPublic(
        txid=str(row.txid),
        block_height=int(row.block_height or 0),
        block_time=str(row.block_time or ""),
        confirmations=int(row.confirmations or 0),
        direction=direction,  # type: ignore[arg-type]
        sent_units=str(sent),
        sent_acp=_units_to_acp_str(sent),
        received_units=str(received),
        received_acp=_units_to_acp_str(received),
        net_units=str(net),
        net_acp=_units_to_acp_str(net),
    )


async def _indexed_transactions_for_address(
    session: AsyncSession, address: str, limit: int
) -> list[AcpTransactionPublic]:
    """Prefer DB-backed MobileAcpTx history when the indexer has rows for this address."""
    result = await session.execute(
        select(MobileAcpTx)
        .where(MobileAcpTx.address == address)
        .order_by(MobileAcpTx.block_height.desc().nullslast(), MobileAcpTx.txid.desc())
        .limit(limit)
    )
    return [_mobile_acp_tx_to_public(r) for r in result.scalars().all()]


def _chain_transaction_details(txid: str) -> AcpTransactionDetailsPublic | None:
    # Detail lookups may wait for a sync rebuild when cache is cold.
    _best_height, _out_index, tx_index = _scan_chain_transactions(interactive=False)
    tx = tx_index.get(txid)
    if tx is None:
        return None
    return AcpTransactionDetailsPublic(
        txid=str(tx["txid"]),
        block_height=int(tx["block_height"]),
        block_hash=str(tx.get("block_hash") or "") or None,
        block_time=str(tx["block_time"]),
        confirmations=int(tx["confirmations"]),
        total_input_units=str(int(tx["total_input_units"])),
        total_input_acp=_units_to_acp_str(int(tx["total_input_units"])),
        total_output_units=str(int(tx["total_output_units"])),
        total_output_acp=_units_to_acp_str(int(tx["total_output_units"])),
        fee_units=str(int(tx["fee_units"])),
        fee_acp=_units_to_acp_str(int(tx["fee_units"])),
        inputs=[
            AcpTransactionIoPublic(
                address=(item.get("address") if item.get("address") else None),
                units=str(int(item.get("units") or 0)),
                acp=_units_to_acp_str(int(item.get("units") or 0)),
                vout=(int(item["vout"]) if item.get("vout") is not None else None),
            )
            for item in tx["inputs"]
        ],
        outputs=[
            AcpTransactionIoPublic(
                address=(item.get("address") if item.get("address") else None),
                units=str(int(item.get("units") or 0)),
                acp=_units_to_acp_str(int(item.get("units") or 0)),
                vout=(int(item["vout"]) if item.get("vout") is not None else None),
            )
            for item in tx["outputs"]
        ],
    )


@router.get("/deposit_address", response_model=AcpDepositAddressResponse)
@router.post("/deposit_address", response_model=AcpDepositAddressResponse)
async def get_deposit_address(
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    try:
        wallet = await get_wallet_for_user(session, user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"ACP wallet lookup failed (DB schema/migration?): {exc}",
        ) from exc
    if wallet is None:
        raise HTTPException(
            status_code=409,
            detail="ACP wallet is not initialized for this account. Please sign in again.",
        )
    addr = (wallet.address or "").strip()
    if not addr:
        raise HTTPException(status_code=500, detail="ACP wallet row has empty address")
    deposit_note = None
    needs_personalize = False
    if addr == CUSTODIAL_HOT_ADDRESS:
        if await user_is_custodial_hot_holder(session, user_id):
            layout = acp_supply_layout()
            deposit_note = str(layout.get("note") or "")
            needs_personalize = False
        else:
            needs_personalize = True
            deposit_note = (
                "Shared custodial hot wallet — not a personal deposit address. "
                "Use Personalize wallet (account password) or sign in again to mint your own ACP address."
            )
    return AcpDepositAddressResponse(
        address=addr,
        mode="standard",
        redacted=privacy_svc.redact_address(addr),
        privacy_profile=privacy_svc.PRIVACY_PROFILE,
        reuse_policy="reusable_primary",
        note=deposit_note,
        needs_personalize=needs_personalize,
    )


async def _bind_view_wire(session: AsyncSession, wallet, wallet_password: str | None) -> bytes:
    cached = (getattr(wallet, "view_pubkey_wire_hex", None) or "").strip()
    if cached:
        try:
            return bytes.fromhex(cached)
        except ValueError:
            report_optional_failure('app.api.routers.wallet_acp:_bind_view_wire:bytes.fromhex', quiet=False)
    if not wallet_password:
        raise HTTPException(
            status_code=400,
            detail="wallet_password required once to enable unlinkable privacy receive addresses",
        )
    try:
        secret = decrypt_mnemonic(
            wallet.encrypted_mnemonic,
            wallet.salt_b64,
            wallet.nonce_b64,
            wallet_password,
        )
        _mnemonic, keystore_json = decode_wallet_secret(secret)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="invalid wallet password") from exc
    if not keystore_json or keystore_json == "{}":
        raise HTTPException(status_code=503, detail="wallet keystore unavailable for privacy binding")
    try:
        from app.services.acp_wallet import _run_walletd

        res = _run_walletd(["address", "--keystore-json", keystore_json, "--index", "0"])
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"privacy binding requires updated walletd: {exc}",
        ) from exc
    view_hex = str(res.get("view_pubkey_wire_hex") or "").strip()
    if len(view_hex) < 64:
        raise HTTPException(
            status_code=503,
            detail="walletd did not return view_pubkey_wire_hex — redeploy ACP wallet helper",
        )
    wallet.view_pubkey_wire_hex = view_hex
    if getattr(wallet, "privacy_next_index", None) in (None, 0):
        wallet.privacy_next_index = 1
    await session.flush()
    return bytes.fromhex(view_hex)


@router.post("/personalize", response_model=AcpPersonalizeWalletResponse)
async def personalize_wallet(
    body: AcpPersonalizeWalletRequest,
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    """Mint a personal deposit address when the account is still bound to shared hot."""
    if await user_is_custodial_hot_holder(session, user_id):
        raise HTTPException(
            status_code=403,
            detail=(
                "This operator account is designated to hold custodial hot. "
                "Most of the ~210M ACP supply is on genesis treasury, not hot."
            ),
        )
    try:
        result = await personalize_hot_bound_wallet(
            session=session,
            user_id=user_id,
            password=body.wallet_password,
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="invalid wallet password") from exc
    if result is None:
        wallet = await get_wallet_for_user(session, user_id)
        if wallet is None:
            raise HTTPException(status_code=409, detail="ACP wallet is not initialized for this account.")
        raise HTTPException(
            status_code=409,
            detail="Wallet is already personalized (not bound to shared custodial hot).",
        )
    wallet, mnemonic = result
    return AcpPersonalizeWalletResponse(
        address=str(wallet.address),
        wallet_backup_mnemonic=mnemonic,
    )


@router.get("/privacy/status", response_model=AcpPrivacyStatusPublic)
async def privacy_status(
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    wallet = await get_wallet_for_user(session, user_id)
    if wallet is None:
        raise HTTPException(status_code=409, detail="ACP wallet is not initialized for this account.")
    count = (
        await session.execute(
            select(func.count())
            .select_from(UserAcpPrivacyAddress)
            .where(UserAcpPrivacyAddress.user_id == user_id)
        )
    ).scalar_one()
    return AcpPrivacyStatusPublic(
        privacy_profile=privacy_svc.PRIVACY_PROFILE,
        view_key_bound=bool((wallet.view_pubkey_wire_hex or "").strip()),
        privacy_next_index=int(getattr(wallet, "privacy_next_index", 1) or 1),
        unlinkable_receive_count=int(count or 0),
        note=(
            "Each privacy receive address is a one-time subaddress. "
            "On-chain amounts remain visible to full nodes; unlinkability comes from never reusing addresses. "
            "Not a mixer."
        ),
    )


@router.post("/privacy/receive-address", response_model=AcpDepositAddressResponse, status_code=201)
async def privacy_receive_address(
    body: AcpPrivacyDepositRequest,
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    wallet = await get_wallet_for_user(session, user_id)
    if wallet is None:
        raise HTTPException(status_code=409, detail="ACP wallet is not initialized for this account.")
    view_wire = await _bind_view_wire(session, wallet, body.wallet_password)
    idx = int(getattr(wallet, "privacy_next_index", 1) or 1)
    if idx < 1:
        idx = 1
    if idx > privacy_svc.DEFAULT_SUBADDR_SCAN_WINDOW:
        raise HTTPException(
            status_code=409,
            detail=(
                "Privacy receive-index exceeds the consensus scan window "
                f"({privacy_svc.DEFAULT_SUBADDR_SCAN_WINDOW})."
            ),
        )
    address = privacy_svc.subaddress_bech32(view_wire, idx)
    row = UserAcpPrivacyAddress(
        id=str(uuid.uuid4()),
        user_id=user_id,
        address=address,
        sub_index=idx,
        label=(body.label or "").strip()[:120] or None,
        created_at=datetime.now(timezone.utc),
    )
    session.add(row)
    wallet.privacy_next_index = idx + 1
    await session.flush()
    await upsert_address_binding(session, user_id, address, BINDING_KIND_PRIVACY)
    return AcpDepositAddressResponse(
        address=address,
        mode="privacy",
        sub_index=idx,
        redacted=privacy_svc.redact_address(address),
        privacy_profile=privacy_svc.PRIVACY_PROFILE,
        reuse_policy="single_use_recommended",
    )


@router.get("/hot/balance", response_model=AcpBalanceResponse)
async def hot_balance(
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    try:
        wallet = await get_wallet_for_user(session, user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"ACP wallet lookup failed (DB schema/migration?): {exc}",
        ) from exc
    if wallet is None:
        raise HTTPException(
            status_code=409,
            detail="ACP wallet is not initialized for this account. Please sign in again.",
        )
    addr = (wallet.address or "").strip()
    if not addr:
        raise HTTPException(status_code=500, detail="ACP wallet row has empty address")
    try:
        res = _load_balance_result(addr, interactive=True)
    except HTTPException:
        # Keep wallet UI operational even when RPC is temporarily unavailable.
        res = _empty_balance_payload(addr)
    if not str(res.get("address") or "").strip():
        res["address"] = addr
    return await _decorate_balance_for_user(session, user_id, res, include_in_work=True)


@router.get("/balance", response_model=AcpBalanceResponse)
async def balance(
    address: str | None = Query(default=None),
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    wallet = await get_wallet_for_user(session, user_id)
    target = (address or "").strip()
    if not target:
        if wallet is None:
            raise HTTPException(
                status_code=409,
                detail="ACP wallet is not initialized for this account. Please sign in again.",
            )
        target = wallet.address
    if len(target) < 16:
        raise HTTPException(status_code=400, detail="address looks invalid")
    include_in_work = bool(wallet and wallet.address == target)
    try:
        res = _load_balance_result(target, interactive=True)
    except HTTPException:
        # Keep wallet UI operational when RPC/balance helper is temporarily unavailable.
        res = _empty_balance_payload(target)
    return await _decorate_balance_for_user(
        session,
        user_id,
        res,
        include_in_work=include_in_work,
    )


@router.get("/transactions", response_model=list[AcpTransactionPublic] | list[dict] | dict)
async def list_transactions(
    address: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    privacy: bool = Query(default=True, description="Redact counterparties in list responses"),
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    target = (address or "").strip()
    if not target:
        wallet = await get_wallet_for_user(session, user_id)
        if wallet is None:
            raise HTTPException(
                status_code=409,
                detail="ACP wallet is not initialized for this account. Please sign in again.",
            )
        target = wallet.address
    if len(target) < 16:
        raise HTTPException(status_code=400, detail="address looks invalid")

    from app.services.cache import cache_get_json, cache_set_json

    hist_key = f"acp:txhist:{target}:{limit}:{'p' if privacy else 'f'}"

    # Prefer DB-backed indexer history when rows exist; fall back to chain scan
    # when empty (not yet indexed) or when the live scan reports warming.
    indexed_rows = await _indexed_transactions_for_address(session, target, limit)
    warming = False
    rows: list[AcpTransactionPublic] = indexed_rows
    if not indexed_rows:
        try:
            rows, warming = _chain_transactions_for_address(target, limit)
        except HTTPException as exc:
            if exc.status_code in (502, 504):
                cached = await cache_get_json(hist_key)
                if isinstance(cached, dict) and cached.get("items") is not None:
                    return {**cached, "warming": True, "status": "degraded", "from_cache": True}
                return {"items": [], "warming": True, "status": "degraded"}
            raise
        if warming and not rows:
            # Still empty while warming — keep degraded/warming shape for clients.
            pass

    if not privacy:
        payload = {
            "items": [r.model_dump() if hasattr(r, "model_dump") else dict(r) for r in rows],
            "warming": warming,
            "status": "warming" if warming else "live",
        }
        if rows and not warming:
            await cache_set_json(hist_key, payload, ttl_seconds=86_400)
        elif warming and not rows:
            cached = await cache_get_json(hist_key)
            if isinstance(cached, dict) and cached.get("items"):
                return {**cached, "warming": True, "status": "warming", "from_cache": True}
        if warming:
            return payload
        return rows

    items = [
        {
            "txid": r.txid,
            "block_height": r.block_height,
            "block_time": r.block_time,
            "confirmations": r.confirmations,
            "direction": r.direction,
            "net_acp": r.net_acp,
            "sent_acp": "hidden",
            "received_acp": "hidden",
            "privacy": True,
            "privacy_profile": privacy_svc.PRIVACY_PROFILE,
        }
        for r in rows
    ]
    payload = {"items": items, "warming": warming, "status": "warming" if warming else "live"}
    if items and not warming:
        await cache_set_json(hist_key, payload, ttl_seconds=86_400)
    elif warming and not items:
        cached = await cache_get_json(hist_key)
        if isinstance(cached, dict) and cached.get("items"):
            return {**cached, "warming": True, "status": "warming", "from_cache": True}
    if warming:
        return payload
    return items


@router.get("/transactions/{txid}")
async def get_transaction_details(
    txid: str,
    privacy: bool = Query(default=True),
):
    """Public chain explorer lookup — tx details are on-chain readable without session auth."""
    txid_norm = (txid or "").strip()
    if len(txid_norm) < 16:
        raise HTTPException(status_code=400, detail="txid looks invalid")
    try:
        details = _chain_transaction_details(txid_norm)
    except HTTPException as exc:
        if exc.status_code in (502, 503, 504):
            raise HTTPException(status_code=503, detail="ACP transaction lookup is temporarily unavailable") from exc
        raise
    if details is None:
        raise HTTPException(status_code=404, detail="ACP transaction not found")
    if privacy:
        payload = details.model_dump() if hasattr(details, "model_dump") else dict(details)
        for io in payload.get("inputs") or []:
            if isinstance(io, dict) and io.get("address"):
                io["address"] = privacy_svc.redact_address(str(io["address"]))
        for io in payload.get("outputs") or []:
            if isinstance(io, dict) and io.get("address"):
                io["address"] = privacy_svc.redact_address(str(io["address"]))
        payload["privacy"] = True
        payload["privacy_profile"] = privacy_svc.PRIVACY_PROFILE
        return payload
    return details


_WITHDRAW_JOB_TTL_S = 900
_withdraw_jobs_lock = threading.Lock()
_withdraw_jobs: dict[str, dict] = {}


def _withdraw_job_key(job_id: str) -> str:
    return f"acp:withdraw_job:{job_id}"


def _store_withdraw_job(job_id: str, payload: dict) -> None:
    with _withdraw_jobs_lock:
        _withdraw_jobs[job_id] = dict(payload)
    try:
        cache_set_json_sync(_withdraw_job_key(job_id), payload, ttl_seconds=_WITHDRAW_JOB_TTL_S)
    except Exception:
        report_optional_failure('app.api.routers.wallet_acp:_store_withdraw_job:cache_set_json_sync', quiet=False)


def _read_withdraw_job(job_id: str) -> dict | None:
    with _withdraw_jobs_lock:
        local = _withdraw_jobs.get(job_id)
        if local is not None:
            return dict(local)
    return None


async def _load_withdraw_job(job_id: str) -> dict | None:
    local = _read_withdraw_job(job_id)
    if local is not None:
        return local
    try:
        remote = await cache_get_json(_withdraw_job_key(job_id))
    except Exception:
        remote = None
    if remote is None:
        try:
            remote = cache_get_json_sync(_withdraw_job_key(job_id))
        except Exception:
            remote = None
    if isinstance(remote, dict):
        with _withdraw_jobs_lock:
            _withdraw_jobs[job_id] = dict(remote)
        return dict(remote)
    return None


def _run_withdraw_transfer_job(
    *,
    job_id: str,
    user_id: str,
    rpc_url: str,
    transfer_signer_args: list[str],
    to_address: str,
    amount_acp: str,
    fee_acp: str | None,
    from_address: str | None = None,
    spend_addresses: list[str] | None = None,
) -> None:
    try:
        # Prefer indexed UTXOs so walletd skips O(tip) tip-scan (~30k blocks).
        utxo_args: list[str] = []
        sources = [a.strip() for a in (spend_addresses or []) if (a or "").strip()]
        if not sources and (from_address or "").strip():
            sources = [(from_address or "").strip()]
        if sources:
            try:
                from app.services import acp_utxo_index as utxo_idx

                indexed_outs: list[dict] = []
                for src in sources:
                    indexed_outs.extend(utxo_idx.list_indexed_utxos(src))
            except Exception:
                indexed_outs = []
            need_units = int(
                (_parse_decimal_or_zero(amount_acp) + _parse_decimal_or_zero(fee_acp or "0.00000001"))
                * Decimal(100_000_000)
            )
            picked_units = 0
            for row in indexed_outs:
                txid = str(row.get("txid") or "").strip()
                vout = int(row.get("vout") or 0)
                units = int(row.get("units") or 0)
                if not txid or units <= 0:
                    continue
                utxo_args.extend(["--utxo", f"{txid}:{vout}:{units}"])
                picked_units += units
                if picked_units >= need_units:
                    break
            if picked_units < need_units:
                utxo_args = []  # fall back to tip-scan if index incomplete

        res = _run_walletd(
            (
                [
                    "transfer",
                    "--rpc",
                    rpc_url,
                    *transfer_signer_args,
                    "--to",
                    to_address,
                    "--amount-acp",
                    amount_acp,
                ]
                + (["--fee-acp", fee_acp] if fee_acp is not None else [])
                + utxo_args
            ),
            timeout_s=180 if not utxo_args else 90,
        )
        _store_withdraw_job(
            job_id,
            {
                "job_id": job_id,
                "user_id": user_id,
                "status": "completed",
                "accepted": bool(res.get("accepted", True)),
                "txid": res.get("txid"),
                "reason": res.get("reason"),
                "error": None,
                "utxo_mode": "indexed" if utxo_args else "tip_scan",
            },
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        _store_withdraw_job(
            job_id,
            {
                "job_id": job_id,
                "user_id": user_id,
                "status": "failed",
                "accepted": False,
                "txid": None,
                "reason": None,
                "error": detail,
            },
        )
    except Exception as exc:
        _store_withdraw_job(
            job_id,
            {
                "job_id": job_id,
                "user_id": user_id,
                "status": "failed",
                "accepted": False,
                "txid": None,
                "reason": None,
                "error": str(exc) or "withdraw failed",
            },
        )


@router.post("/withdraw", response_model=AcpWithdrawResponse)
async def withdraw(
    body: AcpWithdrawRequest,
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    rpc_url = _require_acp_rpc_url()
    _chain_supply_info(required=True)
    wallet = await get_wallet_for_user(session, user_id)
    if wallet is None:
        raise HTTPException(
            status_code=409,
            detail="ACP wallet is not initialized for this account. Please sign in again.",
        )
    wallet_address = str(wallet.address or "").strip()
    is_hot_holder = await user_is_custodial_hot_holder(session, user_id)
    # Always authenticate with the account wallet password first.
    user_signer = await _get_user_wallet_signer(session, user_id, body.wallet_password)
    if user_signer.get("keystore_json"):
        derived = _run_walletd(
            ["address", "--keystore-json", user_signer["keystore_json"]], timeout_s=60
        )
    else:
        derived = _run_walletd(["address", "--mnemonic", user_signer["mnemonic"]], timeout_s=60)
    derived_address = str(derived.get("address") or "").strip()

    to_address = _validate_acp_address(body.to_address, "to_address")
    amount = _parse_positive_decimal(body.amount_acp, "amount_acp")
    fee: Decimal | None = None
    if body.fee_acp is not None and str(body.fee_acp).strip():
        fee = _parse_positive_decimal(body.fee_acp, "fee_acp")
    fee_for_check = fee if fee is not None else (Decimal(1) / Decimal(100_000_000))
    required_total = amount + fee_for_check
    _, in_staked, in_ledger = await _in_work_breakdown_for_user(session, user_id)
    in_work_acp = in_staked + in_ledger

    use_custodial_hot = False
    transfer_signer_args: list[str] | None = None

    if is_hot_holder:
        # Prefer indexed balance — interactive walletd tip-scan can burn the client timeout
        # before transfer even starts.
        try:
            from app.services import acp_utxo_index as utxo_idx

            indexed = utxo_idx.get_indexed_balance(CUSTODIAL_HOT_ADDRESS)
        except Exception:
            indexed = None
        if indexed is not None and not _probe_source_failed(indexed):
            hot_live = _parse_decimal_or_zero(indexed.get("acp"))
        else:
            hot_res = _load_balance_result(CUSTODIAL_HOT_ADDRESS, interactive=True)
            if _probe_source_failed(hot_res):
                hot_live = Decimal(0)
            else:
                hot_live = _parse_decimal_or_zero(hot_res.get("acp"))
        # Prefer hot float for operator spends when it covers the request.
        if hot_live >= required_total:
            try:
                transfer_signer_args, hot_addr = _load_custodial_hot_signer()
                if hot_addr != CUSTODIAL_HOT_ADDRESS:
                    raise HTTPException(status_code=500, detail="Custodial hot signer address mismatch")
                use_custodial_hot = True
            except HTTPException as ks_exc:
                if derived_address == CUSTODIAL_HOT_ADDRESS and user_signer.get("keystore_json"):
                    transfer_signer_args = ["--keystore-json", user_signer["keystore_json"]]
                    use_custodial_hot = True
                elif derived_address == CUSTODIAL_HOT_ADDRESS:
                    transfer_signer_args = ["--mnemonic", user_signer["mnemonic"]]
                    use_custodial_hot = True
                else:
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            f"Operator hot float is {_decimal_to_api_str(hot_live)} ACP but "
                            f"custodial hot keystore is unavailable ({ks_exc.detail}). "
                            "Upload KeystoreV3 for acp1qzfdkq… to /run/secrets/custodial-hot.keystore.json."
                        ),
                    ) from ks_exc

    if not use_custodial_hot:
        if wallet_address == CUSTODIAL_HOT_ADDRESS and not is_hot_holder:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Custodial hot wallet withdrawals are disabled on the user API. "
                    "Use the operator/bridge signer path for hot spends."
                ),
            )
        if not derived_address or derived_address != wallet_address:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Wallet key mismatch for this address. "
                    "This wallet was created with a legacy non-deterministic key flow and cannot sign spends for the stored address. "
                    "Please create/migrate to a new wallet."
                ),
            )
        balance_res = _load_balance_result(wallet_address)
        if _probe_source_failed(balance_res):
            on_chain_acp = Decimal(0)
        else:
            on_chain_acp = _parse_decimal_or_zero(balance_res.get("acp"))
        _, _, available_acp = _personal_balance_view(on_chain_acp, in_staked, in_ledger)
        privacy_acp, privacy_addresses = await _privacy_receive_snapshot(
            session, user_id, wallet_address
        )
        if privacy_acp is None:
            raise HTTPException(
                status_code=503,
                detail="Privacy receive balance is temporarily unavailable. Retry shortly.",
            )
        _, _, available_acp = _personal_balance_view(
            on_chain_acp + privacy_acp, in_staked, in_ledger
        )
        if required_total > available_acp:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Requested {_decimal_to_api_str(amount)} ACP + fee {_decimal_to_api_str(fee_for_check)} ACP "
                    f"exceeds available {_decimal_to_api_str(available_acp)} ACP "
                    f"(in work: {_decimal_to_api_str(in_work_acp)} ACP)."
                ),
            )
        if user_signer.get("keystore_json"):
            transfer_signer_args = ["--keystore-json", user_signer["keystore_json"]]
        else:
            transfer_signer_args = ["--mnemonic", user_signer["mnemonic"]]

    assert transfer_signer_args is not None

    # Queue chain transfer off the request path so Cloudflare/browser do not cut a long tip-scan.
    job_id = str(uuid4())
    spend_from = CUSTODIAL_HOT_ADDRESS if use_custodial_hot else wallet_address
    spend_addresses = [spend_from]
    if not use_custodial_hot:
        spend_addresses.extend(privacy_addresses)
    _store_withdraw_job(
        job_id,
        {
            "job_id": job_id,
            "user_id": str(user_id),
            "status": "pending",
            "accepted": None,
            "txid": None,
            "reason": None,
            "error": None,
            "to_address": to_address,
            "amount_acp": _decimal_to_api_str(amount),
            "from_address": spend_from,
        },
    )
    fee_s = _decimal_to_api_str(fee) if fee is not None else None
    threading.Thread(
        target=_run_withdraw_transfer_job,
        kwargs={
            "job_id": job_id,
            "user_id": str(user_id),
            "rpc_url": rpc_url,
            "transfer_signer_args": list(transfer_signer_args),
            "to_address": to_address,
            "amount_acp": _decimal_to_api_str(amount),
            "fee_acp": fee_s,
            "from_address": spend_from,
            "spend_addresses": spend_addresses,
        },
        daemon=True,
        name=f"acp-withdraw-{job_id[:8]}",
    ).start()
    return AcpWithdrawResponse(
        accepted=None,
        txid=None,
        reason="Transfer queued; poll GET /wallet/acp/withdraw/jobs/{job_id}",
        status="pending",
        job_id=job_id,
    )


@router.get("/withdraw/jobs/{job_id}", response_model=AcpWithdrawJobResponse)
async def withdraw_job_status(
    job_id: str,
    user_id: str = Depends(require_auth),
):
    cleaned = (job_id or "").strip()
    if not cleaned or len(cleaned) > 80:
        raise HTTPException(status_code=400, detail="Invalid job_id")
    job = await _load_withdraw_job(cleaned)
    if job is None:
        raise HTTPException(status_code=404, detail="Withdraw job not found")
    if str(job.get("user_id") or "") != str(user_id):
        raise HTTPException(status_code=404, detail="Withdraw job not found")
    status = str(job.get("status") or "pending")
    if status not in {"pending", "completed", "failed"}:
        status = "pending"
    return AcpWithdrawJobResponse(
        job_id=cleaned,
        status=status,  # type: ignore[arg-type]
        accepted=job.get("accepted"),
        txid=job.get("txid"),
        reason=job.get("reason"),
        error=job.get("error"),
    )



def _assert_web_usdt_swap_enabled() -> None:
    settings = get_settings()
    if not bool(getattr(settings, "ff_web_usdt_trc20_swap", False)):
        raise HTTPException(
            status_code=410,
            detail="Web USDT TRC-20 → ACP swap desk is disabled. Use the mobile Exchange office.",
        )


@router.post("/swap/quote", response_model=AcpSwapQuoteResponse)
def swap_quote(body: AcpSwapQuoteRequest):
    _assert_web_usdt_swap_enabled()
    amount = _parse_positive_decimal(body.usdt_trc20_amount, "usdt_trc20_amount")
    rate = _swap_rate()
    estimated = (amount * rate).quantize(Decimal("0.00000001"))
    return AcpSwapQuoteResponse(
        usdt_trc20_amount=_decimal_to_api_str(amount),
        rate_acp_per_usdt=_decimal_to_api_str(rate),
        estimated_acp_amount=_decimal_to_api_str(estimated),
    )


@router.post("/swap/orders", response_model=AcpSwapOrderPublic)
async def create_swap_order(
    body: AcpSwapOrderCreateRequest,
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    _assert_web_usdt_swap_enabled()
    amount = _parse_positive_decimal(body.usdt_trc20_amount, "usdt_trc20_amount")
    rate = _swap_rate()
    estimated = (amount * rate).quantize(Decimal("0.00000001"))
    settings = get_settings()
    payout_address = _validate_acp_address(body.payout_acp_address, "payout_acp_address")

    idempotency_key = (x_idempotency_key or "").strip() or None
    if idempotency_key:
        existing = (
            await session.execute(
                select(AcpSwapOrder).where(
                    AcpSwapOrder.user_id == user_id,
                    AcpSwapOrder.idempotency_key == idempotency_key,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return _to_public_order(_swap_row_to_dict(existing))

    order = AcpSwapOrder(
        id=uuid4(),
        user_id=user_id,
        status="awaiting_deposit",
        usdt_trc20_amount=amount,
        rate_acp_per_usdt=rate,
        estimated_acp_amount=estimated,
        payout_acp_address=payout_address,
        deposit_trc20_address=settings.usdt_trc20_deposit_address,
        deposit_reference=f"ACP-{uuid4().hex[:8].upper()}",
        note=body.note.strip() if body.note else None,
        idempotency_key=idempotency_key,
    )
    session.add(order)
    await session.flush()
    return _to_public_order(_swap_row_to_dict(order))


@router.get("/swap/orders", response_model=list[AcpSwapOrderPublic])
async def list_swap_orders(user_id: str = Depends(require_auth), session: AsyncSession = Depends(get_db)):
    rows = (
        await session.execute(
            select(AcpSwapOrder).where(AcpSwapOrder.user_id == user_id).order_by(AcpSwapOrder.created_at.desc())
        )
    ).scalars().all()
    return [_to_public_order(_swap_row_to_dict(o)) for o in rows]


@router.get("/swap/orders/{order_id}", response_model=AcpSwapOrderPublic)
async def get_swap_order(order_id: str, user_id: str = Depends(require_auth), session: AsyncSession = Depends(get_db)):
    order = await session.get(AcpSwapOrder, order_id)
    if not order or str(order.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Swap order not found")
    return _to_public_order(_swap_row_to_dict(order))


@router.post("/swap/orders/{order_id}/confirm", response_model=AcpSwapOrderPublic)
async def confirm_swap_order(
    order_id: str,
    body: AcpSwapOrderConfirmRequest,
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    order = await session.get(AcpSwapOrder, order_id)
    if not order or str(order.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Swap order not found")
    if order.status not in ("awaiting_deposit", "pending_review"):
        raise HTTPException(status_code=409, detail="Swap order can no longer be confirmed")
    order.status = "pending_review"
    if body.tron_txid:
        order.tron_txid = body.tron_txid.strip()
    order.updated_at = datetime.now(timezone.utc)
    await session.flush()
    return _to_public_order(_swap_row_to_dict(order))


@router.post("/swap/orders/{order_id}/cancel", response_model=AcpSwapOrderPublic)
async def cancel_swap_order(order_id: str, user_id: str = Depends(require_auth), session: AsyncSession = Depends(get_db)):
    order = await session.get(AcpSwapOrder, order_id)
    if not order or str(order.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Swap order not found")
    if order.status in ("completed", "cancelled", "rejected"):
        return _to_public_order(_swap_row_to_dict(order))
    order.status = "cancelled"
    order.updated_at = datetime.now(timezone.utc)
    await session.flush()
    return _to_public_order(_swap_row_to_dict(order))


@router.post("/swap/orders/{order_id}/complete", response_model=AcpSwapCompleteResponse)
async def complete_swap_order(
    order_id: str,
    body: AcpSwapCompleteRequest,
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    order = await session.get(AcpSwapOrder, order_id)
    if not order or str(order.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Swap order not found")
    if order.status in ("completed", "cancelled", "rejected"):
        raise HTTPException(status_code=409, detail=f"Swap order is already {order.status}")
    if order.status != "pending_review":
        raise HTTPException(status_code=409, detail="Swap order must be confirmed before completion")

    rpc_url = _require_acp_rpc_url()
    signer = await _get_user_wallet_signer(session, user_id, body.wallet_password)
    transfer_res = _run_walletd(
        [
            "transfer",
            "--rpc",
            rpc_url,
            *(
                ["--keystore-json", signer["keystore_json"]]
                if signer.get("keystore_json")
                else ["--mnemonic", signer["mnemonic"]]
            ),
            "--to",
            order.payout_acp_address,
            "--amount-acp",
            _decimal_to_api_str(_parse_decimal_or_zero(order.estimated_acp_amount)),
        ],
        timeout_s=180,
    )
    transfer = AcpWithdrawResponse(**transfer_res)
    order.status = "completed"
    order.payout_txid = transfer.txid
    order.updated_at = datetime.now(timezone.utc)
    await session.flush()
    try:
        from app.services import exchange_ticket_settle as settle_svc

        await settle_svc.mark_tickets_for_completed_swap(session, swap_order_id=str(order.id))
    except Exception:
        # Ticket sync must not block swap completion.
        pass
    return AcpSwapCompleteResponse(order=_to_public_order(_swap_row_to_dict(order)), transfer=transfer)


# --- OTC metals / goods intake desk -------------------------------------------------


def _otc_row_public(row: AcpOtcIntakeOrder) -> OtcIntakeOrderPublic:
    return OtcIntakeOrderPublic(
        id=str(row.id),
        user_id=str(row.user_id),
        rail=row.rail,  # type: ignore[arg-type]
        status=row.status,  # type: ignore[arg-type]
        asset_label=row.asset_label,
        asset_detail=dict(row.asset_detail or {}),
        estimated_acp_amount=_decimal_to_api_str(_parse_decimal_or_zero(row.estimated_acp_amount)),
        payout_acp_address=str(row.payout_acp_address),
        intake_reference=str(row.intake_reference),
        handoff_instructions=otc_svc.handoff_instructions(),
        proof_ref=row.proof_ref,
        note=row.note,
        created_at=(row.created_at or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z"),
        updated_at=(row.updated_at or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z"),
    )


@router.get("/otc/catalog", response_model=OtcCatalogPublic)
def otc_catalog():
    return otc_svc.catalog()


@router.post("/otc/quote/metal", response_model=OtcQuoteResponse)
def otc_quote_metal(body: OtcMetalQuoteRequest):
    return otc_svc.quote_metal(
        metal=body.metal,
        weight_grams=body.weight_grams,
        purity_ppt=body.purity_ppt,
    )


@router.post("/otc/quote/goods", response_model=OtcQuoteResponse)
def otc_quote_goods(body: OtcGoodsQuoteRequest):
    return otc_svc.quote_goods(
        category=body.category,
        estimated_value_acp=body.estimated_value_acp,
    )


@router.post("/otc/quote/commodity", response_model=OtcQuoteResponse)
def otc_quote_commodity(body: OtcCommodityQuoteRequest):
    return otc_svc.quote_commodity(
        commodity=body.commodity,
        quantity=body.quantity,
        grade_note=body.grade_note,
    )


@router.post("/otc/quote/real-estate", response_model=OtcQuoteResponse)
def otc_quote_real_estate(body: OtcRealEstateQuoteRequest):
    return otc_svc.quote_real_estate(
        deal_type=body.deal_type,
        estimated_value_acp=body.estimated_value_acp,
        jurisdiction=body.jurisdiction,
        lease_months=body.lease_months,
    )


@router.post("/otc/quote/space", response_model=OtcQuoteResponse)
def otc_quote_space(body: OtcSpaceQuoteRequest):
    return otc_svc.quote_space(
        object_class=body.object_class,
        estimated_value_acp=body.estimated_value_acp,
        norad_or_cospar_id=body.norad_or_cospar_id,
    )


@router.post("/otc/quote/ip", response_model=OtcQuoteResponse)
def otc_quote_ip(body: OtcIpQuoteRequest):
    return otc_svc.quote_ip(
        kind=body.kind,
        estimated_value_acp=body.estimated_value_acp,
        registration_uri=body.registration_uri,
    )


@router.post("/otc/orders", response_model=OtcIntakeOrderPublic, status_code=201)
async def create_otc_order(
    body: OtcIntakeCreateRequest,
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
    x_idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    payout = _validate_acp_address(body.payout_acp_address, "payout_acp_address")
    idempotency_key = (x_idempotency_key or "").strip() or None
    if idempotency_key:
        existing = (
            await session.execute(
                select(AcpOtcIntakeOrder).where(
                    AcpOtcIntakeOrder.user_id == user_id,
                    AcpOtcIntakeOrder.idempotency_key == idempotency_key,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return _otc_row_public(existing)

    if body.rail == "metal":
        if not body.metal or not body.weight_grams:
            raise HTTPException(status_code=400, detail="metal and weight_grams required for metal rail")
        purity = int(body.purity_ppt or 999)
        detail = otc_svc.build_metal_detail(
            metal=body.metal,
            weight_grams=body.weight_grams,
            purity_ppt=purity,
        )
        quote = otc_svc.quote_metal(metal=body.metal, weight_grams=body.weight_grams, purity_ppt=purity)
    elif body.rail == "commodity":
        if not body.commodity or not body.quantity:
            raise HTTPException(status_code=400, detail="commodity and quantity required for commodity rail")
        detail = otc_svc.build_commodity_detail(
            commodity=body.commodity,
            quantity=body.quantity,
            grade_note=body.grade_note,
        )
        quote = otc_svc.quote_commodity(
            commodity=body.commodity,
            quantity=body.quantity,
            grade_note=body.grade_note,
        )
    elif body.rail == "goods":
        title = (body.goods_title or "").strip()
        if not body.goods_category or not title or not body.estimated_value_acp:
            raise HTTPException(
                status_code=400,
                detail="goods_category, goods_title, and estimated_value_acp required for goods rail",
            )
        detail = otc_svc.build_goods_detail(
            category=body.goods_category,
            title=title,
            description=body.goods_description,
            estimated_value_acp=body.estimated_value_acp,
        )
        quote = otc_svc.quote_goods(category=body.goods_category, estimated_value_acp=body.estimated_value_acp)
    elif body.rail == "real_estate":
        deal = body.re_deal_type or "sale"
        parcel = (body.re_address_or_parcel or "").strip()
        if not parcel or not body.estimated_value_acp:
            raise HTTPException(
                status_code=400,
                detail="re_address_or_parcel and estimated_value_acp required for real_estate rail",
            )
        detail = otc_svc.build_real_estate_detail(
            deal_type=deal,
            address_or_parcel=parcel,
            estimated_value_acp=body.estimated_value_acp,
            jurisdiction=body.re_jurisdiction,
            lease_months=body.re_lease_months,
            document_hash=body.document_hash,
        )
        quote = otc_svc.quote_real_estate(
            deal_type=deal,
            estimated_value_acp=body.estimated_value_acp,
            jurisdiction=body.re_jurisdiction,
            lease_months=body.re_lease_months,
        )
    elif body.rail == "space":
        cls = body.space_object_class or "satellite"
        if not body.estimated_value_acp:
            raise HTTPException(status_code=400, detail="estimated_value_acp required for space rail")
        detail = otc_svc.build_space_detail(
            object_class=cls,
            estimated_value_acp=body.estimated_value_acp,
            space_object_id=body.space_object_id,
            jurisdiction=body.space_jurisdiction,
            document_hash=body.document_hash,
        )
        quote = otc_svc.quote_space(
            object_class=cls,
            estimated_value_acp=body.estimated_value_acp,
            norad_or_cospar_id=body.space_object_id,
        )
    elif body.rail == "ip":
        kind = body.ip_kind or "patent"
        title = (body.ip_title or "").strip()
        if not title or not body.estimated_value_acp:
            raise HTTPException(
                status_code=400,
                detail="ip_title and estimated_value_acp required for ip rail",
            )
        if not body.document_hash:
            raise HTTPException(status_code=400, detail="document_hash required for ip rail")
        detail = otc_svc.build_ip_detail(
            kind=kind,
            title=title,
            estimated_value_acp=body.estimated_value_acp,
            registration_uri=body.ip_registration_uri,
            jurisdiction=body.ip_jurisdiction,
            document_hash=body.document_hash,
        )
        quote = otc_svc.quote_ip(
            kind=kind,
            estimated_value_acp=body.estimated_value_acp,
            registration_uri=body.ip_registration_uri,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported OTC rail: {body.rail}")

    now = datetime.now(timezone.utc)
    order = AcpOtcIntakeOrder(
        id=uuid4(),
        user_id=user_id,
        rail=body.rail,
        status="awaiting_handoff",
        asset_label=otc_svc.asset_label_for(rail=body.rail, detail=detail),
        asset_detail=detail,
        estimated_acp_amount=_parse_decimal_or_zero(quote.estimated_acp_amount),
        payout_acp_address=payout,
        intake_reference=f"OTC-{uuid4().hex[:8].upper()}",
        note=body.note.strip() if body.note else None,
        idempotency_key=idempotency_key,
        created_at=now,
        updated_at=now,
    )
    session.add(order)
    await session.flush()
    return _otc_row_public(order)


@router.get("/otc/orders", response_model=list[OtcIntakeOrderPublic])
async def list_otc_orders(user_id: str = Depends(require_auth), session: AsyncSession = Depends(get_db)):
    rows = (
        await session.execute(
            select(AcpOtcIntakeOrder)
            .where(AcpOtcIntakeOrder.user_id == user_id)
            .order_by(AcpOtcIntakeOrder.created_at.desc())
        )
    ).scalars().all()
    return [_otc_row_public(o) for o in rows]


@router.get("/otc/orders/{order_id}", response_model=OtcIntakeOrderPublic)
async def get_otc_order(order_id: str, user_id: str = Depends(require_auth), session: AsyncSession = Depends(get_db)):
    order = await session.get(AcpOtcIntakeOrder, order_id)
    if not order or str(order.user_id) != user_id:
        raise HTTPException(status_code=404, detail="OTC intake order not found")
    return _otc_row_public(order)


@router.post("/otc/orders/{order_id}/confirm", response_model=OtcIntakeOrderPublic)
async def confirm_otc_order(
    order_id: str,
    body: OtcIntakeConfirmRequest,
    user_id: str = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    order = await session.get(AcpOtcIntakeOrder, order_id)
    if not order or str(order.user_id) != user_id:
        raise HTTPException(status_code=404, detail="OTC intake order not found")
    if order.status not in ("awaiting_handoff", "pending_review"):
        raise HTTPException(status_code=409, detail="OTC order can no longer be confirmed")
    order.status = "pending_review"
    if body.proof_ref:
        order.proof_ref = body.proof_ref.strip()[:256]
    if body.note:
        order.note = ((order.note + "\n") if order.note else "") + body.note.strip()[:500]
    order.updated_at = datetime.now(timezone.utc)
    await session.flush()
    return _otc_row_public(order)


@router.post("/otc/orders/{order_id}/cancel", response_model=OtcIntakeOrderPublic)
async def cancel_otc_order(order_id: str, user_id: str = Depends(require_auth), session: AsyncSession = Depends(get_db)):
    order = await session.get(AcpOtcIntakeOrder, order_id)
    if not order or str(order.user_id) != user_id:
        raise HTTPException(status_code=404, detail="OTC intake order not found")
    if order.status in ("completed", "cancelled", "rejected"):
        return _otc_row_public(order)
    order.status = "cancelled"
    order.updated_at = datetime.now(timezone.utc)
    await session.flush()
    return _otc_row_public(order)

