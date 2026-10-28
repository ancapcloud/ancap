"""Hidden platform-admin console APIs — gated by require_platform_admin."""
from __future__ import annotations
from app.services.recoverable_errors import report_optional_failure

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import cast, Date, func, or_, select

from app.api.deps import DbSession, require_platform_admin
from app.db.models import (
    GrowthMetricRollup,
    MobileAddressIndexerState,
    PaymentIntent,
    User,
    UserAcpWallet,
    UserEvmWallet,
    WorkflowRunRecord,
)
from app.schemas.acp_reconcile import (
    AcpHistoryRescanRequest,
    AcpHistoryRescanResponse,
    AcpReconcileExecuteRequest,
    AcpReconcileExecuteResponse,
    AcpReconcileGapItem,
    AcpReconcileReport,
    AcpReconcileTransferResult,
)
from app.services.acp_fund_reconcile import build_reconcile_report, execute_restore_gaps
from app.services.cache import redis_ping
from app.services.ledger import is_ledger_invariant_halted
from app.jobs.mobile_acp_indexer_tick import mobile_acp_indexer_tick

router = APIRouter(prefix="/platform-admin", tags=["Platform Admin"])


class AdminUserListItem(BaseModel):
    id: str
    email: str
    display_name: str | None = None
    created_at: datetime | None = None
    has_acp_wallet: bool = False
    has_evm_wallet: bool = False
    workflow_runs: int = 0


class AdminUserListResponse(BaseModel):
    items: list[AdminUserListItem]
    total: int
    limit: int
    offset: int


class AdminUserDetail(BaseModel):
    id: str
    email: str
    display_name: str | None = None
    created_at: datetime | None = None
    stripe_customer_id: str | None = None
    acp_address: str | None = None
    evm_address: str | None = None
    workflow_runs: int = 0
    captured_payments: int = 0


class AdminOverview(BaseModel):
    users_total: int
    users_7d: int
    users_30d: int
    workflow_runs_total: int
    workflow_runs_7d: int
    captured_payments_total: int
    captured_payments_7d: int
    redis_ok: bool
    ledger_halted: bool
    generated_at: datetime


class TimeseriesPoint(BaseModel):
    date: str
    value: float


class TimeseriesResponse(BaseModel):
    metric: str
    days: int
    points: list[TimeseriesPoint]


class ForecastPoint(BaseModel):
    date: str
    value: float
    kind: str = Field(description="history | forecast")


class ForecastResponse(BaseModel):
    metric: str
    days: int
    horizon: int
    points: list[ForecastPoint]
    slope_per_day: float
    method: str = "linear_ols"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _day_start(days_ago: int) -> datetime:
    return (_utc_now() - timedelta(days=days_ago)).replace(hour=0, minute=0, second=0, microsecond=0)


@router.get("/overview", response_model=AdminOverview)
async def admin_overview(
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
):
    now = _utc_now()
    d7 = _day_start(7)
    d30 = _day_start(30)

    users_total = (await session.execute(select(func.count(User.id)))).scalar_one()
    users_7d = (
        await session.execute(select(func.count(User.id)).where(User.created_at >= d7))
    ).scalar_one()
    users_30d = (
        await session.execute(select(func.count(User.id)).where(User.created_at >= d30))
    ).scalar_one()

    runs_total = (await session.execute(select(func.count(WorkflowRunRecord.id)))).scalar_one()
    runs_7d = (
        await session.execute(
            select(func.count(WorkflowRunRecord.id)).where(WorkflowRunRecord.created_at >= d7)
        )
    ).scalar_one()

    captured_total = (
        await session.execute(
            select(func.count(PaymentIntent.id)).where(PaymentIntent.status == "captured")
        )
    ).scalar_one()
    captured_7d = (
        await session.execute(
            select(func.count(PaymentIntent.id)).where(
                PaymentIntent.status == "captured",
                PaymentIntent.created_at >= d7,
            )
        )
    ).scalar_one()

    redis_ok, _ = await redis_ping()
    ledger_halted = await is_ledger_invariant_halted(session)

    return AdminOverview(
        users_total=int(users_total or 0),
        users_7d=int(users_7d or 0),
        users_30d=int(users_30d or 0),
        workflow_runs_total=int(runs_total or 0),
        workflow_runs_7d=int(runs_7d or 0),
        captured_payments_total=int(captured_total or 0),
        captured_payments_7d=int(captured_7d or 0),
        redis_ok=bool(redis_ok),
        ledger_halted=bool(ledger_halted),
        generated_at=now,
    )


@router.get("/users", response_model=AdminUserListResponse)
async def admin_list_users(
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
    q: str | None = Query(None, max_length=200),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    base = select(User)
    count_q = select(func.count(User.id))
    if q and q.strip():
        needle = f"%{q.strip().lower()}%"
        filt = or_(func.lower(User.email).like(needle), func.lower(User.display_name).like(needle))
        # also allow exact id match
        try:
            UUID(q.strip())
            filt = or_(filt, User.id == q.strip())
        except ValueError:
            report_optional_failure('app.api.routers.platform_admin:admin_list_users:UUID', quiet=False)
        base = base.where(filt)
        count_q = count_q.where(filt)

    total = (await session.execute(count_q)).scalar_one()
    rows = (
        await session.execute(base.order_by(User.created_at.desc()).limit(limit).offset(offset))
    ).scalars().all()

    user_ids = [u.id for u in rows]
    acp_ids: set[str] = set()
    evm_ids: set[str] = set()
    run_counts: dict[str, int] = {}
    if user_ids:
        acp_rows = (
            await session.execute(select(UserAcpWallet.user_id).where(UserAcpWallet.user_id.in_(user_ids)))
        ).all()
        acp_ids = {str(r[0]) for r in acp_rows}
        evm_rows = (
            await session.execute(select(UserEvmWallet.user_id).where(UserEvmWallet.user_id.in_(user_ids)))
        ).all()
        evm_ids = {str(r[0]) for r in evm_rows}
        run_rows = (
            await session.execute(
                select(WorkflowRunRecord.owner_user_id, func.count(WorkflowRunRecord.id))
                .where(WorkflowRunRecord.owner_user_id.in_(user_ids))
                .group_by(WorkflowRunRecord.owner_user_id)
            )
        ).all()
        run_counts = {str(uid): int(c) for uid, c in run_rows}

    items = [
        AdminUserListItem(
            id=str(u.id),
            email=u.email,
            display_name=u.display_name,
            created_at=u.created_at,
            has_acp_wallet=str(u.id) in acp_ids,
            has_evm_wallet=str(u.id) in evm_ids,
            workflow_runs=run_counts.get(str(u.id), 0),
        )
        for u in rows
    ]
    return AdminUserListResponse(items=items, total=int(total or 0), limit=limit, offset=offset)


@router.get("/users/{user_id}", response_model=AdminUserDetail)
async def admin_user_detail(
    user_id: str,
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
):
    try:
        UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user id") from exc

    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    acp = await session.get(UserAcpWallet, user_id)
    evm = await session.get(UserEvmWallet, user_id)
    runs = (
        await session.execute(
            select(func.count(WorkflowRunRecord.id)).where(WorkflowRunRecord.owner_user_id == user_id)
        )
    ).scalar_one()
    payments = (
        await session.execute(
            select(func.count(PaymentIntent.id)).where(
                PaymentIntent.owner_user_id == user_id,
                PaymentIntent.status == "captured",
            )
        )
    ).scalar_one()

    return AdminUserDetail(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at,
        stripe_customer_id=user.stripe_customer_id,
        acp_address=acp.address if acp else None,
        evm_address=evm.wallet_address if evm else None,
        workflow_runs=int(runs or 0),
        captured_payments=int(payments or 0),
    )


async def _build_daily_series(session: DbSession, metric: str, days: int) -> list[TimeseriesPoint]:
    since = _day_start(days)
    end = _utc_now().date()
    start = since.date()
    buckets: dict[str, float] = {}
    d = start
    while d <= end:
        buckets[d.isoformat()] = 0.0
        d += timedelta(days=1)

    if metric == "signups":
        rows = (
            await session.execute(
                select(cast(User.created_at, Date), func.count(User.id))
                .where(User.created_at >= since)
                .group_by(cast(User.created_at, Date))
            )
        ).all()
        for day, count in rows:
            if day is not None:
                buckets[day.isoformat()] = float(count)
    elif metric == "workflow_runs":
        rows = (
            await session.execute(
                select(cast(WorkflowRunRecord.created_at, Date), func.count(WorkflowRunRecord.id))
                .where(WorkflowRunRecord.created_at >= since)
                .group_by(cast(WorkflowRunRecord.created_at, Date))
            )
        ).all()
        for day, count in rows:
            if day is not None:
                buckets[day.isoformat()] = float(count)
    elif metric == "captured_payments":
        rows = (
            await session.execute(
                select(cast(PaymentIntent.created_at, Date), func.count(PaymentIntent.id))
                .where(PaymentIntent.status == "captured", PaymentIntent.created_at >= since)
                .group_by(cast(PaymentIntent.created_at, Date))
            )
        ).all()
        for day, count in rows:
            if day is not None:
                buckets[day.isoformat()] = float(count)
    elif metric == "growth_rollup":
        # Sum all rollup values per day (generic growth signal).
        rows = (
            await session.execute(
                select(GrowthMetricRollup.metric_date, func.sum(GrowthMetricRollup.metric_value))
                .where(GrowthMetricRollup.metric_date >= start)
                .group_by(GrowthMetricRollup.metric_date)
            )
        ).all()
        for day, value in rows:
            if day is not None:
                buckets[day.isoformat()] = float(value or 0)
    else:
        raise HTTPException(
            status_code=400,
            detail="metric must be one of: signups, workflow_runs, captured_payments, growth_rollup",
        )

    return [TimeseriesPoint(date=k, value=buckets[k]) for k in sorted(buckets.keys())]


@router.get("/timeseries", response_model=TimeseriesResponse)
async def admin_timeseries(
    session: DbSession,
    metric: str = Query("signups"),
    days: int = Query(30, ge=7, le=90),
    _admin: str = Depends(require_platform_admin),
):
    points = await _build_daily_series(session, metric, days)
    return TimeseriesResponse(metric=metric, days=days, points=points)


def _linear_forecast(history: list[TimeseriesPoint], horizon: int) -> tuple[list[ForecastPoint], float]:
    n = len(history)
    if n == 0:
        return [], 0.0
    xs = list(range(n))
    ys = [p.value for p in history]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    denom = sum((x - mean_x) ** 2 for x in xs) or 1.0
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denom
    intercept = mean_y - slope * mean_x

    out: list[ForecastPoint] = [
        ForecastPoint(date=p.date, value=p.value, kind="history") for p in history
    ]
    last = date.fromisoformat(history[-1].date)
    for i in range(1, horizon + 1):
        x = n - 1 + i
        pred = max(0.0, intercept + slope * x)
        out.append(
            ForecastPoint(
                date=(last + timedelta(days=i)).isoformat(),
                value=round(pred, 4),
                kind="forecast",
            )
        )
    return out, slope


@router.get("/forecast", response_model=ForecastResponse)
async def admin_forecast(
    session: DbSession,
    metric: str = Query("signups"),
    days: int = Query(30, ge=7, le=90),
    horizon: int = Query(7, ge=1, le=30),
    _admin: str = Depends(require_platform_admin),
):
    history = await _build_daily_series(session, metric, days)
    points, slope = _linear_forecast(history, horizon)
    return ForecastResponse(
        metric=metric,
        days=days,
        horizon=horizon,
        points=points,
        slope_per_day=round(slope, 6),
        method="linear_ols",
    )


@router.get("/acp-reconcile", response_model=AcpReconcileReport)
async def admin_acp_reconcile_report(
    session: DbSession,
    limit: int = Query(500, ge=1, le=2000),
    only_gaps: bool = Query(True),
    _admin: str = Depends(require_platform_admin),
):
    raw = await build_reconcile_report(session, limit=limit, only_gaps=only_gaps)
    return AcpReconcileReport(
        dry_run=True,
        scanned=int(raw["scanned"]),
        gap_count=int(raw["gap_count"]),
        items=[AcpReconcileGapItem(**item) for item in raw["items"]],
        note=raw.get("note"),
    )


@router.post("/acp-reconcile/execute", response_model=AcpReconcileExecuteResponse)
async def admin_acp_reconcile_execute(
    body: AcpReconcileExecuteRequest,
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
):
    try:
        raw = await execute_restore_gaps(
            session,
            user_ids=body.user_ids or None,
            confirm=bool(body.confirm),
            max_transfers=int(body.max_transfers),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    transfers = []
    for t in raw.get("transfers") or []:
        transfers.append(
            AcpReconcileTransferResult(
                user_id=str(t.get("user_id")),
                address=str(t.get("address")),
                amount_acp=str(t.get("amount_acp")),
                ok=bool(t.get("ok")),
                txid=(str(t["txid"]) if t.get("txid") else None),
                error=(str(t["error"]) if t.get("error") else None),
            )
        )
    return AcpReconcileExecuteResponse(
        dry_run=False,
        attempted=int(raw.get("attempted") or 0),
        skipped=int(raw.get("skipped") or 0),
        transfers=transfers,
    )


@router.post("/acp-history/rescan", response_model=AcpHistoryRescanResponse)
async def admin_acp_history_rescan(
    body: AcpHistoryRescanRequest,
    session: DbSession,
    _admin: str = Depends(require_platform_admin),
):
    """Force an indexer tick; optionally clear the global watermark for a full rescan."""
    target = (body.address or "").strip() or None
    if target and len(target) < 16:
        raise HTTPException(status_code=400, detail="address looks invalid")

    state_row = await session.execute(
        select(MobileAddressIndexerState).where(MobileAddressIndexerState.id == 1)
    )
    state = state_row.scalar_one_or_none()
    if state is None:
        state = MobileAddressIndexerState(id=1, last_scanned_height=0, indexed_addresses=[])
        session.add(state)
        await session.flush()

    previous_height = int(state.last_scanned_height or 0)
    watermark_reset = False
    note_parts: list[str] = []

    if body.reset_watermark:
        # Cautious: resets the global indexer watermark for ALL watched addresses.
        state.last_scanned_height = 0
        watermark_reset = True
        note_parts.append(
            "last_scanned_height cleared to 0; tick rescans from genesis for all watched addresses"
        )
        await session.flush()

    extra = [target] if target else None
    tick = await mobile_acp_indexer_tick(session, extra_addresses=extra)
    if tick.get("error"):
        note_parts.append(f"indexer: {tick['error']}")

    return AcpHistoryRescanResponse(
        ok=not bool(tick.get("error")),
        address=target,
        watermark_reset=watermark_reset,
        previous_last_scanned_height=previous_height,
        last_scanned_height=int(tick.get("last_scanned_height") or state.last_scanned_height or 0),
        addresses_watched=int(tick.get("addresses_watched") or len(state.indexed_addresses or [])),
        indexed=int(tick.get("indexed") or 0),
        best_height=(int(tick["best_height"]) if tick.get("best_height") is not None else None),
        error=(str(tick["error"]) if tick.get("error") else None),
        note="; ".join(note_parts) if note_parts else None,
    )
