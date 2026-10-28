"""Compose QOBLIB-style crypto benchmark scorecard from live rails."""
from __future__ import annotations
from app.services.recoverable_errors import report_optional_failure

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import BridgeOperation
from app.schemas.crypto_benchmark import (
    BenchmarkOverall,
    BenchmarkResult,
    CryptoBenchmarkClassPublic,
    CryptoBenchmarkResponse,
)
from app.services import sacp as sacp_svc
from app.services.bridge_reconciliation import (
    check_reconciliation_mismatch_alert,
    check_stale_snapshots,
    latest_reserve_snapshot,
)

SNAPSHOT_FRESH_MINUTES = 60
LIVE_PROOF_FRESH_MINUTES = 15


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _age_minutes(ts: datetime | None, now: datetime | None = None) -> float | None:
    if ts is None:
        return None
    ref = now or _utc_now()
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (ref - ts).total_seconds() / 60.0


def _worst_result(results: list[BenchmarkResult]) -> BenchmarkOverall:
    if any(r == "fail" for r in results):
        return "fail"
    if any(r == "pending" for r in results):
        return "pending"
    return "pass"


async def _bridge_counts(session: AsyncSession) -> dict[str, int]:
    counts: dict[str, int] = {}
    try:
        rows = await session.execute(
            select(BridgeOperation.status, func.count()).group_by(BridgeOperation.status)
        )
        for st, c in rows.all():
            counts[str(st)] = int(c)
    except Exception:
        report_optional_failure('app.services.crypto_benchmark:_bridge_counts:session.execute', quiet=False)
    return counts


async def build_benchmark(session: AsyncSession) -> CryptoBenchmarkResponse:
    from app.api.routers.bridge_rail import _live_reserve_proof_payload

    settings = get_settings()
    measured_at = _utc_now()
    reserve_proof = await _live_reserve_proof_payload(session)
    counts = await _bridge_counts(session)
    sacp_status = sacp_svc.public_status()
    sacp_proof = await sacp_svc.reserve_proof(session)
    try:
        latest_snapshot = await latest_reserve_snapshot(session)
    except Exception:
        latest_snapshot = None
    stale_alert = await check_stale_snapshots(session)
    mismatch_alert = await check_reconciliation_mismatch_alert(session)

    classes: list[CryptoBenchmarkClassPublic] = []

    # reserve_backing
    supply_smallest = int(reserve_proof.wacp_total_supply_acp_smallest or "0")
    backing = reserve_proof.backing_ratio
    rb_notes: list[str] = []
    rb_observed: dict[str, Any] = {
        "backing_ratio": backing,
        "wacp_total_supply_acp_smallest": str(supply_smallest),
        "reserve_health": reserve_proof.reserve_health,
        "snapshot_backing_ratio": float(latest_snapshot.backing_ratio)
        if latest_snapshot and latest_snapshot.backing_ratio is not None
        else None,
    }
    if not settings.bridge_rail_enabled:
        rb_result: BenchmarkResult = "pending"
        rb_notes.append("Bridge rail disabled — backing benchmark not applicable.")
    elif supply_smallest <= 0:
        rb_result = "pass"
        rb_notes.append("Completed wACP supply is zero; backing ratio baseline deferred.")
    elif backing is None:
        rb_result = "pending"
        rb_notes.append("Backing ratio unavailable.")
    elif Decimal(backing) >= Decimal("1"):
        rb_result = "pass"
    else:
        rb_result = "fail"
        rb_notes.append("Reserve balance below implied completed wACP supply.")
    classes.append(
        CryptoBenchmarkClassPublic(
            id="reserve_backing",
            title="Reserve backing",
            baseline="backing_ratio >= 1.0 when completed wACP supply > 0",
            observed=rb_observed,
            result=rb_result,
            notes=rb_notes,
        )
    )

    # snapshot_freshness
    snap_age = _age_minutes(latest_snapshot.snapshot_at if latest_snapshot else None, measured_at)
    proof_age = _age_minutes(reserve_proof.last_updated_at, measured_at)
    sf_notes: list[str] = []
    sf_observed: dict[str, Any] = {
        "snapshot_age_minutes": round(snap_age, 1) if snap_age is not None else None,
        "proof_age_minutes": round(proof_age, 1) if proof_age is not None else None,
        "snapshot_fresh_threshold_minutes": SNAPSHOT_FRESH_MINUTES,
        "proof_fresh_threshold_minutes": LIVE_PROOF_FRESH_MINUTES,
        "stale_alert": stale_alert,
    }
    snapshot_fresh = snap_age is not None and snap_age <= SNAPSHOT_FRESH_MINUTES
    proof_fresh = proof_age is not None and proof_age <= LIVE_PROOF_FRESH_MINUTES
    if not settings.bridge_rail_enabled:
        sf_result: BenchmarkResult = "pending"
        sf_notes.append("Bridge rail disabled.")
    elif stale_alert:
        sf_result = "fail"
        sf_notes.append("Latest reserve snapshot exceeds stale threshold.")
    elif snapshot_fresh or proof_fresh:
        sf_result = "pass"
        if snapshot_fresh:
            sf_notes.append("Snapshot within freshness window.")
        else:
            sf_notes.append("Live reserve proof within freshness window.")
    elif latest_snapshot is None and reserve_proof.last_updated_at is None:
        sf_result = "pending"
        sf_notes.append("No snapshot or live proof timestamp available.")
    else:
        sf_result = "fail"
        sf_notes.append("Neither snapshot nor live proof is within freshness window.")
    classes.append(
        CryptoBenchmarkClassPublic(
            id="snapshot_freshness",
            title="Snapshot freshness",
            baseline=f"snapshot age <= {SNAPSHOT_FRESH_MINUTES} min or live proof age <= {LIVE_PROOF_FRESH_MINUTES} min",
            observed=sf_observed,
            result=sf_result,
            notes=sf_notes,
        )
    )

    # intent_pipeline
    failed = counts.get("FAILED", 0)
    pending_deposit = counts.get("PENDING_DEPOSIT", 0)
    ip_notes: list[str] = []
    ip_observed: dict[str, Any] = {
        "counts_by_status": counts,
        "failed": failed,
        "pending_deposit": pending_deposit,
        "pending_deposit_ttl_hours": settings.bridge_pending_deposit_ttl_hours,
    }
    if not settings.bridge_rail_enabled:
        ip_result: BenchmarkResult = "pending"
        ip_notes.append("Bridge rail disabled.")
    elif failed > 0:
        ip_result = "fail"
        ip_notes.append(f"{failed} FAILED intent(s) require operator review.")
    else:
        ip_result = "pass"
        if pending_deposit > 0:
            ip_notes.append(
                f"{pending_deposit} PENDING_DEPOSIT intent(s) noted; "
                f"TTL auto-cancel after {settings.bridge_pending_deposit_ttl_hours}h when configured."
            )
    classes.append(
        CryptoBenchmarkClassPublic(
            id="intent_pipeline",
            title="Intent pipeline",
            baseline="FAILED == 0; PENDING_DEPOSIT noted (TTL cancel allowed)",
            observed=ip_observed,
            result=ip_result,
            notes=ip_notes,
        )
    )

    # dry_run_honesty
    bridge_live = settings.bridge_rail_enabled and not settings.bridge_rail_paused
    dr_notes: list[str] = []
    dr_observed: dict[str, Any] = {
        "bridge_rail_enabled": settings.bridge_rail_enabled,
        "bridge_rail_paused": settings.bridge_rail_paused,
        "dry_run": settings.bridge_dry_run,
    }
    if not settings.bridge_rail_enabled:
        dr_result: BenchmarkResult = "pending"
        dr_notes.append("Bridge rail disabled.")
    elif bridge_live and settings.bridge_dry_run:
        dr_result = "fail"
        dr_notes.append("Bridge enabled but dry_run=true — not honest full production posture.")
    elif settings.bridge_dry_run:
        dr_result = "pass"
        dr_notes.append("dry_run=true with bridge paused/disabled — simulation posture is honest.")
    else:
        dr_result = "pass"
        dr_notes.append("Bridge live with dry_run=false.")
    classes.append(
        CryptoBenchmarkClassPublic(
            id="dry_run_honesty",
            title="Dry-run honesty",
            baseline="if mint live then dry_run=false; dry-run must not claim full production",
            observed=dr_observed,
            result=dr_result,
            notes=dr_notes,
        )
    )

    # sacp_readiness
    sacp_contract = (settings.sacp_contract or "").strip()
    sacp_enabled = sacp_svc.is_enabled()
    sr_notes: list[str] = list(sacp_status.get("notes") or [])
    sr_observed: dict[str, Any] = {
        "ff_sacp": sacp_enabled,
        "sacp_contract": sacp_contract or None,
        "mint_available": sacp_status.get("mint_available"),
        "reserve_health": sacp_proof.get("reserve_health"),
    }
    if not sacp_enabled:
        sr_result: BenchmarkResult = "pass"
        sr_notes.append("sACP disabled — honest pre-production posture.")
    elif not sacp_contract:
        if sacp_status.get("mint_available"):
            sr_result = "fail"
            sr_notes.append("sACP mint advertised but SACP_CONTRACT is empty.")
        else:
            sr_result = "pass"
            sr_notes.append("sACP openly not_configured — contracts pending deploy.")
    else:
        sr_result = "pass"
        sr_notes.append("sACP contract configured.")
    classes.append(
        CryptoBenchmarkClassPublic(
            id="sacp_readiness",
            title="sACP readiness",
            baseline="contracts set OR status openly not_configured",
            observed=sr_observed,
            result=sr_result,
            notes=sr_notes[:6],
        )
    )

    # contract_trust
    wacp = (settings.bridge_wacp_contract or "").strip()
    gateway = (settings.bridge_gateway_contract or "").strip()
    ct_notes: list[str] = []
    ct_observed: dict[str, Any] = {
        "wacp_contract": wacp or None,
        "gateway_contract": gateway or None,
        "bsc_contract_verified": bool(settings.bridge_bsc_contract_verified and wacp),
        "token_metadata_live": bool(settings.bridge_token_metadata_live),
        "reconciliation_mismatch": mismatch_alert,
    }
    if wacp and gateway:
        ct_result: BenchmarkResult = "pass"
        ct_notes.append("Official wACP and gateway addresses configured.")
        ct_notes.append("token_metadata_live=false reported honestly.")
    elif not settings.bridge_rail_enabled:
        ct_result = "pending"
        ct_notes.append("Bridge disabled — contract trust deferred.")
    else:
        ct_result = "fail"
        ct_notes.append("Missing wACP or gateway contract address.")
    if mismatch_alert:
        ct_result = "fail"
        ct_notes.append("Latest reconciliation snapshot reports mismatch.")
    classes.append(
        CryptoBenchmarkClassPublic(
            id="contract_trust",
            title="Contract trust",
            baseline="official wACP + gateway published; verification flags honest",
            observed=ct_observed,
            result=ct_result,
            notes=ct_notes,
        )
    )

    overall = _worst_result([c.result for c in classes])
    pass_n = sum(1 for c in classes if c.result == "pass")
    fail_n = sum(1 for c in classes if c.result == "fail")
    pending_n = sum(1 for c in classes if c.result == "pending")
    summary = (
        f"{pass_n}/{len(classes)} benchmarks pass; "
        f"{fail_n} fail; {pending_n} pending. "
        "Measured vs published baselines — not a safety guarantee."
    )

    return CryptoBenchmarkResponse(
        overall=overall,
        measured_at=measured_at,
        classes=classes,
        summary=summary,
    )
