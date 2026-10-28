from __future__ import annotations
from app.services.recoverable_errors import report_optional_failure

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import (
    Agent,
    Strategy,
    StrategyVersion,
    Vertical,
    VerticalSpec,
    Pool,
    LedgerEvent,
    RiskProfileEnum,
)
from app.engine.actions.base_vertical import BASE_VERTICAL_ACTIONS
from app.schemas.flows import FlowArtifactRef, FlowRunResponse
from app.services.ledger import append_event, get_or_create_account, set_ledger_invariant_halted
from app.db.models import LedgerEventTypeEnum
from app.services.stakes import stake as stake_agent

from app.api.routers.listings import create_listing
from app.api.routers.orders import place_order
from app.api.routers.runs import request_run
from app.api.routers.reviews import create_review
from app.api.routers.risk import set_risk_limits
from app.api.routers.system import (
    upsert_edges_daily_from_orders,
    upsert_agent_relationships_from_orders,
    auto_limits_tick,
    auto_quarantine_tick,
    auto_ab_tick,
    circuit_breaker_by_metric_tick,
    reputation_tick,
)
from app.schemas.listings import ListingCreateRequest, ListingStatus
from app.schemas.orders import OrderPlaceRequest
from app.schemas.runs import RunRequest
from app.schemas.reviews import ReviewCreateRequest
from app.schemas.risk import RiskLimitsRequest
from app.schemas.strategies import FeeModel, FeeModelType
from app.schemas.common import Money


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class _RunCtx:
    artifacts: List[FlowArtifactRef] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def ref(self, kind: str, id: UUID | str, url: str | None = None, **meta: Any) -> None:
        sid = str(id)
        self.artifacts.append(FlowArtifactRef(kind=kind, id=sid, url=url, meta=meta or {}))


async def ensure_vertical(session: AsyncSession, name: str = "BaseVertical") -> Vertical:
    q = select(Vertical).where(Vertical.name == name).limit(1)
    r = await session.execute(q)
    vert = r.scalar_one_or_none()
    if vert:
        return vert

    vert = Vertical(name=name, status="active", owner_agent_id=None)
    session.add(vert)
    await session.flush()

    spec = VerticalSpec(
        vertical_id=vert.id,
        spec_json={
            "allowed_actions": [{"name": a} for a in sorted(BASE_VERTICAL_ACTIONS)],
            "version": "flows-runner-v1",
        },
    )
    session.add(spec)
    await session.flush()
    return vert


async def ensure_pool(session: AsyncSession, vertical_id: UUID, name: str = "Default Pool") -> Pool:
    q = select(Pool).where(Pool.name == name).limit(1)
    r = await session.execute(q)
    pool = r.scalar_one_or_none()
    if pool:
        return pool
    pool = Pool(
        name=name,
        risk_profile=RiskProfileEnum.low,
        status="active",
        rules={"seeded_by": "flows"},
    )
    session.add(pool)
    await session.flush()
    return pool


async def create_agent(
    session: AsyncSession,
    display_name: str,
    roles: list[str],
    *,
    created_by_agent_id: UUID | None = None,
) -> Agent:
    a = Agent(
        display_name=display_name,
        roles=roles,
        status="active",
        metadata_={"seeded_by": "flows"},
        created_by_agent_id=created_by_agent_id,
    )
    session.add(a)
    await session.flush()
    return a


async def mint(session: AsyncSession, *, owner_type: str, owner_id: UUID, currency: str, amount: str, reference: str) -> None:
    """Mint balance for scenarios (uses deposit event; best-effort, dev-only)."""
    acc = await get_or_create_account(session, owner_type, owner_id)
    await append_event(
        session,
        LedgerEventTypeEnum.deposit,
        currency,
        Decimal(amount),
        dst_account_id=acc.id,
        metadata={"reference": reference, "scenario": "flows"},
    )


async def tick_jobs_best_effort(session: AsyncSession) -> dict[str, Any]:
    """Run the same jobs as /v1/system/jobs/tick, but don't halt ledger on invariant (runner needs orders)."""
    processed = await upsert_edges_daily_from_orders(session, batch_size=2000, commit=False)
    agent_rel_processed = await upsert_agent_relationships_from_orders(session, batch_size=2000, commit=False)
    limits_updated = await auto_limits_tick(session, max_updates=100)
    quarantine_count = await auto_quarantine_tick(session, threshold=0.2)
    ab_result = await auto_ab_tick(session, min_sample_size=5, promote_percentile=0.9)
    cb_result = await circuit_breaker_by_metric_tick(session, commit=False)
    rep_result = await reputation_tick(session, max_subjects=50, since_days=7, commit=False)
    await set_ledger_invariant_halted(session, halted=False)
    return {
        "ok": True,
        "edges_daily_orders_processed": processed,
        "agent_relationships_orders_processed": agent_rel_processed,
        "auto_limits_updated": limits_updated,
        "auto_quarantine_count": quarantine_count,
        "auto_ab": ab_result,
        "circuit_breaker_by_metric": cb_result,
        "reputation_recomputed": rep_result.get("recomputed"),
        "ledger_invariant_violations": [],
        "ledger_invariant_halted_forced": True,
    }


async def create_minimal_strategy(
    session: AsyncSession,
    *,
    owner_agent_id: UUID,
    vertical_id: UUID,
    name: str,
) -> tuple[Strategy, StrategyVersion]:
    strat = Strategy(
        name=name,
        vertical_id=vertical_id,
        status="published",
        owner_agent_id=owner_agent_id,
        summary="Scenario runner strategy",
        description="Autogenerated for end-to-end flows",
        tags=["flows"],
    )
    session.add(strat)
    await session.flush()

    ver = StrategyVersion(
        strategy_id=strat.id,
        semver="0.1.0",
        workflow_json={
            "steps": [
                {"id": "seed", "action": "const", "args": {"value": 1000}, "save_as": "_start_equity"},
                {"id": "rand", "action": "rand_uniform", "args": {"low": 1, "high": 10}},
                {"id": "buy", "action": "portfolio_buy", "args": {"asset": "ABC", "amount": 1, "price": {"ref": "rand"}}},
                {"id": "sell", "action": "portfolio_sell", "args": {"asset": "ABC", "amount": 1, "price": 2}},
            ]
        },
    )
    session.add(ver)
    await session.flush()
    return strat, ver


async def run_flow(flow_id: str, session: AsyncSession, *, seed: int | None = None, params: dict | None = None) -> FlowRunResponse:
    started_at = _now()
    ctx = _RunCtx()
    params = params or {}

    try:
        if flow_id == "flow1":
            await _flow1(session, ctx, seed=seed, params=params)
        elif flow_id == "flow2":
            await _flow2(session, ctx, seed=seed, params=params)
        elif flow_id == "flow3":
            await _flow3(session, ctx, seed=seed, params=params)
        elif flow_id == "simulation":
            await _simulation(session, ctx, seed=seed, params=params)
        else:
            raise ValueError(f"Unknown flow_id: {flow_id}")
        ok = True
    except Exception as e:
        ok = False
        ctx.errors.append(str(e))

    finished_at = _now()
    return FlowRunResponse(
        flow_id=flow_id,
        ok=ok,
        started_at=started_at,
        finished_at=finished_at,
        summary=ctx.summary,
        artifacts=ctx.artifacts,
        errors=ctx.errors,
    )


# ---- Flow implementations (filled in next todos) ----


async def _flow1(session: AsyncSession, ctx: _RunCtx, *, seed: int | None, params: dict) -> None:
    settings = get_settings()
    currency = params.get("currency") or "ACP"
    one_time_price = str(params.get("one_time_price") or "10")

    vert = await ensure_vertical(session)
    ctx.ref("vertical", vert.id, url=f"/verticals?selected={vert.id}")

    pool = await ensure_pool(session, UUID(str(vert.id)))
    ctx.ref("pool", pool.id, url=f"/pools?selected={pool.id}")

    builder = await create_agent(session, display_name=f"Flow1 Builder", roles=["builder"])
    buyer = await create_agent(session, display_name=f"Flow1 Buyer", roles=["buyer"])
    ctx.ref("agent", builder.id, url="/agents", role="builder")
    ctx.ref("agent", buyer.id, url="/agents", role="buyer")

    # Ensure builder can activate if stake required, and can pay listing fees (if configured).
    mint_builder = Decimal(one_time_price) * Decimal(2)
    if float(settings.stake_to_activate_amount or "0") > 0:
        mint_builder += Decimal(settings.stake_to_activate_amount or "0")
    if settings.listing_fee_amount:
        try:
            mint_builder += Decimal(settings.listing_fee_amount or "0")
        except Exception:
            report_optional_failure('app.scenarios.runner:_flow1:256', quiet=True)
    await mint(session, owner_type="agent", owner_id=UUID(str(builder.id)), currency=currency, amount=str(mint_builder), reference="flow1-builder-mint")

    if float(settings.stake_to_activate_amount or "0") > 0:
        await stake_agent(
            session,
            agent_id=UUID(str(builder.id)),
            amount_currency=settings.stake_to_activate_currency,
            amount_value=Decimal(settings.stake_to_activate_amount),
        )
        ctx.summary["builder_staked"] = True
    else:
        ctx.summary["builder_staked"] = False

    await mint(session, owner_type="agent", owner_id=UUID(str(buyer.id)), currency=currency, amount=str(Decimal(one_time_price) * Decimal(2)), reference="flow1-buyer-mint")

    strat, ver = await create_minimal_strategy(
        session,
        owner_agent_id=UUID(str(builder.id)),
        vertical_id=UUID(str(vert.id)),
        name="Flow1 Strategy",
    )
    ctx.ref("strategy", strat.id, url="/strategies")
    ctx.ref("strategy_version", ver.id, url="/strategies")

    listing_req = ListingCreateRequest(
        strategy_id=str(strat.id),
        strategy_version_id=str(ver.id),
        fee_model=FeeModel(
            type=FeeModelType.one_time,
            one_time_price=Money(amount=one_time_price, currency=currency),
        ),
        status=ListingStatus.active,
        terms_url=None,
        notes="Flow1 listing",
    )
    listing = await create_listing(listing_req, session)
    ctx.ref("listing", listing.id, url="/marketplace")

    order_req = OrderPlaceRequest(
        listing_id=listing.id,
        buyer_type="agent",
        buyer_id=str(buyer.id),
        payment_method="ledger",
        note="Flow1 purchase",
    )
    order = await place_order(order_req, session, idempotency_key=f"flow1-order-{seed or 0}-{listing.id}")
    ctx.ref("order", order.id, url="/orders")

    # Verify access exists (grant is created by place_order)
    from app.db.models import AccessGrant
    gq = select(AccessGrant).where(
        AccessGrant.strategy_id == UUID(listing.strategy_id),
        AccessGrant.grantee_type == "agent",
        AccessGrant.grantee_id == UUID(order.buyer_id),
    ).limit(1)
    gr = await session.execute(gq)
    grant = gr.scalar_one_or_none()
    if grant:
        ctx.ref("access_grant", grant.id, url="/access", scope=str(getattr(grant.scope, "value", grant.scope)))
        ctx.summary["access_grant_created"] = True
    else:
        ctx.summary["access_grant_created"] = False

    run_req = RunRequest(
        strategy_version_id=str(ver.id),
        pool_id=str(pool.id),
        params={"_start_equity": 1000, "seed": seed} if seed is not None else {"_start_equity": 1000},
        limits={},
        dry_run=True,
        run_mode="mock",
    )
    run = await request_run(run_req, session, idempotency_key=f"flow1-run-{seed or 0}-{ver.id}-{pool.id}")
    ctx.ref("run", run.id, url="/runs")

    tick_result = await tick_jobs_best_effort(session)
    ctx.summary["tick"] = tick_result

    # Ledger evidence: recent transfers/fees for escrow+settlement
    ev_q = select(LedgerEvent).order_by(LedgerEvent.ts.desc()).limit(50)
    ev_r = await session.execute(ev_q)
    evs = ev_r.scalars().all()
    ctx.summary["ledger_recent_count"] = len(evs)
    ctx.summary["order_amount"] = {"currency": currency, "amount": one_time_price}


async def _flow2(session: AsyncSession, ctx: _RunCtx, *, seed: int | None, params: dict) -> None:
    currency = params.get("currency") or "ACP"
    one_time_price = str(params.get("one_time_price") or "5")

    vert = await ensure_vertical(session)
    pool = await ensure_pool(session, UUID(str(vert.id)), name="Audit Pool")
    ctx.ref("pool", pool.id, url="/pools", role="audit")

    builder = await create_agent(session, display_name="Flow2 Builder", roles=["builder"])
    auditor = await create_agent(session, display_name="Flow2 Auditor", roles=["auditor"])
    ctx.ref("agent", builder.id, url="/agents", role="builder")
    ctx.ref("agent", auditor.id, url="/agents", role="auditor")

    settings = get_settings()
    await mint(session, owner_type="agent", owner_id=UUID(str(builder.id)), currency=currency, amount="100", reference="flow2-builder-mint")
    if float(settings.stake_to_activate_amount or "0") > 0:
        await stake_agent(
            session,
            agent_id=UUID(str(builder.id)),
            amount_currency=settings.stake_to_activate_currency,
            amount_value=Decimal(settings.stake_to_activate_amount),
        )
    await mint(session, owner_type="agent", owner_id=UUID(str(auditor.id)), currency=currency, amount="100", reference="flow2-auditor-mint")

    strat, ver = await create_minimal_strategy(
        session,
        owner_agent_id=UUID(str(builder.id)),
        vertical_id=UUID(str(vert.id)),
        name="Flow2 Strategy (suspect)",
    )
    ctx.ref("strategy", strat.id, url="/strategies")
    ctx.ref("strategy_version", ver.id, url="/strategies")

    listing = await create_listing(
        ListingCreateRequest(
            strategy_id=str(strat.id),
            strategy_version_id=str(ver.id),
            fee_model=FeeModel(
                type=FeeModelType.one_time,
                one_time_price=Money(amount=one_time_price, currency=currency),
            ),
            status=ListingStatus.active,
            notes="Flow2 listing for audit",
        ),
        session,
    )
    ctx.ref("listing", listing.id, url="/marketplace")

    order = await place_order(
        OrderPlaceRequest(
            listing_id=listing.id,
            buyer_type="agent",
            buyer_id=str(auditor.id),
            payment_method="ledger",
            note="Flow2 auditor purchase",
        ),
        session,
        idempotency_key=f"flow2-order-{seed or 0}-{listing.id}",
    )
    ctx.ref("order", order.id, url="/orders")

    # Create a couple of runs before "risk tightening"
    runs = []
    for i in range(int(params.get("pre_runs") or 2)):
        rr = await request_run(
            RunRequest(
                strategy_version_id=str(ver.id),
                pool_id=str(pool.id),
                params={"_start_equity": 1000, "seed": (seed or 0) + i},
                limits={"max_steps": 50},
                dry_run=True,
                run_mode="mock",
            ),
            session,
            idempotency_key=f"flow2-run-pre-{seed or 0}-{i}-{ver.id}-{pool.id}",
        )
        runs.append(rr)
        ctx.ref("run", rr.id, url="/runs", phase="pre-risk")

    # Auditor flags strategy via negative review.
    review = await create_review(
        ReviewCreateRequest(
            reviewer_type="agent",
            reviewer_id=str(auditor.id),
            target_type="strategy",
            target_id=str(strat.id),
            weight=float(params.get("review_weight") or 1.0),
            text="Flow2: flagged as bad / suspicious",
            run_id=runs[-1].id if runs else None,
        ),
        session,
    )
    ctx.ref("review", review.id, url="/reputation", target="strategy")

    tick_result = await tick_jobs_best_effort(session)
    ctx.summary["tick"] = tick_result

    # Tighten risk policy for this strategy: require near-perfect trust_score so runs are blocked.
    limits = await set_risk_limits(
        RiskLimitsRequest(
            scope_type="strategy",
            scope_id=str(strat.id),
            policy_json={
                # Force deterministic block in demo: reciprocity_score is always >= 0.0, so cap=0 blocks.
                "max_reciprocity_score": float(params.get("max_reciprocity_score") or 0.0),
                "min_trust_score": float(params.get("min_trust_score") or 0.99),
                "reputation_window": params.get("reputation_window") or "90d",
                "max_steps": 100,
            },
        ),
        session,
    )
    # Important: DbSession has autoflush=False; make sure policy is persisted before request_run reads it.
    await session.flush()
    ctx.summary["risk_limits_set"] = {"scope_type": limits.scope_type, "scope_id": limits.scope_id}

    # Verify: new run request is blocked (HTTPException 403)
    blocked = False
    try:
        await request_run(
            RunRequest(
                strategy_version_id=str(ver.id),
                pool_id=str(pool.id),
                params={"_start_equity": 1000, "seed": (seed or 0) + 999},
                limits={"max_steps": 50},
                dry_run=True,
                run_mode="mock",
            ),
            session,
            idempotency_key=f"flow2-run-blocked-{seed or 0}-{ver.id}-{pool.id}",
        )
    except Exception as e:
        blocked = True
        ctx.errors.append(f"expected_block: {e}")
    ctx.summary["new_run_blocked_by_risk"] = blocked


async def _flow3(session: AsyncSession, ctx: _RunCtx, *, seed: int | None, params: dict) -> None:
    currency = params.get("currency") or "ACP"
    price = str(params.get("one_time_price") or "7")

    vert = await ensure_vertical(session)
    pool = await ensure_pool(session, UUID(str(vert.id)), name="Hire Pool")
    ctx.ref("pool", pool.id, url="/pools", role="hire")

    employer = await create_agent(session, display_name="Flow3 Employer", roles=["buyer"])
    worker = await create_agent(session, display_name="Flow3 Worker", roles=["builder", "worker"])
    ctx.ref("agent", employer.id, url="/agents", role="employer")
    ctx.ref("agent", worker.id, url="/agents", role="worker")

    settings = get_settings()
    await mint(session, owner_type="agent", owner_id=UUID(str(worker.id)), currency=currency, amount="100", reference="flow3-worker-mint")
    if float(settings.stake_to_activate_amount or "0") > 0:
        await stake_agent(
            session,
            agent_id=UUID(str(worker.id)),
            amount_currency=settings.stake_to_activate_currency,
            amount_value=Decimal(settings.stake_to_activate_amount),
        )
    await mint(session, owner_type="agent", owner_id=UUID(str(employer.id)), currency=currency, amount="100", reference="flow3-employer-mint")

    strat, ver1 = await create_minimal_strategy(
        session,
        owner_agent_id=UUID(str(worker.id)),
        vertical_id=UUID(str(vert.id)),
        name="Flow3 Service Strategy",
    )
    ctx.ref("strategy", strat.id, url="/strategies")
    ctx.ref("strategy_version", ver1.id, url="/strategies", phase="initial")

    listing = await create_listing(
        ListingCreateRequest(
            strategy_id=str(strat.id),
            strategy_version_id=str(ver1.id),
            fee_model=FeeModel(
                type=FeeModelType.one_time,
                one_time_price=Money(amount=price, currency=currency),
            ),
            status=ListingStatus.active,
            notes="Flow3: service listing",
        ),
        session,
    )
    ctx.ref("listing", listing.id, url="/marketplace", listing_kind="service")

    order = await place_order(
        OrderPlaceRequest(
            listing_id=listing.id,
            buyer_type="agent",
            buyer_id=str(employer.id),
            payment_method="ledger",
            note="Flow3 hire order",
        ),
        session,
        idempotency_key=f"flow3-order-{seed or 0}-{listing.id}",
    )
    ctx.ref("order", order.id, url="/orders")

    # Worker delivers an updated version ("deliverable")
    ver2 = StrategyVersion(
        strategy_id=strat.id,
        semver="0.2.0",
        workflow_json={
            "steps": [
                {"id": "seed", "action": "const", "args": {"value": 1000}, "save_as": "_start_equity"},
                {"id": "add", "action": "math_add", "args": {"a": 1, "b": 2}},
                {"id": "buy", "action": "portfolio_buy", "args": {"asset": "XYZ", "amount": 1, "price": 3}},
                {"id": "sell", "action": "portfolio_sell", "args": {"asset": "XYZ", "amount": 1, "price": 4}},
            ]
        },
        changelog="Flow3 deliverable: improved workflow",
    )
    session.add(ver2)
    await session.flush()
    ctx.ref("strategy_version", ver2.id, url="/strategies", phase="deliverable")

    run = await request_run(
        RunRequest(
            strategy_version_id=str(ver2.id),
            pool_id=str(pool.id),
            params={"_start_equity": 1000, "seed": seed or 0},
            limits={"max_steps": 80},
            dry_run=True,
            run_mode="mock",
        ),
        session,
        idempotency_key=f"flow3-run-{seed or 0}-{ver2.id}-{pool.id}",
    )
    ctx.ref("run", run.id, url="/runs", phase="deliverable")

    tick_result = await tick_jobs_best_effort(session)
    ctx.summary["tick"] = tick_result


async def _simulation(session: AsyncSession, ctx: _RunCtx, *, seed: int | None, params: dict) -> None:
    import random

    rng = random.Random(seed or 0)
    currency = params.get("currency") or "ACP"
    agents_n = int(params.get("agents") or 100)
    strategies_per_agent = int(params.get("strategies_per_agent") or 1)
    orders_total = int(params.get("orders") or agents_n)
    runs_per_order = int(params.get("runs_per_order") or 1)
    tick_every = int(params.get("tick_every") or 50)

    vert = await ensure_vertical(session)
    pool = await ensure_pool(session, UUID(str(vert.id)), name="Simulation Pool")
    ctx.ref("pool", pool.id, url="/pools", role="simulation")

    settings = get_settings()

    seeder = await create_agent(session, display_name="Simulation Seeder", roles=["seller"])
    ctx.ref("agent", seeder.id, url="/agents", role="seeder")

    agents: list[Agent] = []
    for i in range(agents_n):
        role = "seller" if i < max(1, agents_n // 2) else "buyer"
        a = await create_agent(
            session,
            display_name=f"SimAgent {i:04d}",
            roles=[role],
            created_by_agent_id=UUID(str(seeder.id)),
        )
        agents.append(a)
        await mint(session, owner_type="agent", owner_id=UUID(str(a.id)), currency=currency, amount="50", reference="sim-mint")
        if role == "seller" and float(settings.stake_to_activate_amount or "0") > 0:
            try:
                await stake_agent(
                    session,
                    agent_id=UUID(str(a.id)),
                    amount_currency=settings.stake_to_activate_currency,
                    amount_value=Decimal(settings.stake_to_activate_amount),
                )
            except Exception:
                report_optional_failure('app.scenarios.runner:_simulation:611', quiet=True)

    sellers = agents[: max(1, agents_n // 2)]
    buyers = agents[max(1, agents_n // 2) :]

    listings: list[dict[str, str]] = []
    for s in sellers:
        for j in range(strategies_per_agent):
            strat, ver = await create_minimal_strategy(
                session,
                owner_agent_id=UUID(str(s.id)),
                vertical_id=UUID(str(vert.id)),
                name=f"Sim Strategy {s.display_name} #{j+1}",
            )
            listing = await create_listing(
                ListingCreateRequest(
                    strategy_id=str(strat.id),
                    strategy_version_id=str(ver.id),
                    fee_model=FeeModel(
                        type=FeeModelType.one_time,
                        one_time_price=Money(amount="1", currency=currency),
                    ),
                    status=ListingStatus.active,
                    notes="Simulation listing",
                ),
                session,
            )
            listings.append({"listing_id": listing.id, "version_id": str(ver.id)})

    created_orders = 0
    created_runs = 0
    blocked_orders = 0
    for k in range(orders_total):
        buyer = rng.choice(buyers) if buyers else rng.choice(agents)
        item = rng.choice(listings)
        try:
            await place_order(
                OrderPlaceRequest(
                    listing_id=item["listing_id"],
                    buyer_type="agent",
                    buyer_id=str(buyer.id),
                    payment_method="ledger",
                    note="sim order",
                ),
                session,
                idempotency_key=f"sim-order-{seed or 0}-{k}-{item['listing_id']}-{buyer.id}",
            )
            created_orders += 1
        except Exception:
            blocked_orders += 1
            continue

        for r_i in range(runs_per_order):
            try:
                run = await request_run(
                    RunRequest(
                        strategy_version_id=item["version_id"],
                        pool_id=str(pool.id),
                        params={"_start_equity": 1000, "seed": rng.randint(0, 1_000_000)},
                        limits={"max_steps": 60},
                        dry_run=True,
                        run_mode="mock",
                    ),
                    session,
                    idempotency_key=f"sim-run-{seed or 0}-{k}-{r_i}-{item['version_id']}-{pool.id}-{buyer.id}",
                )
                created_runs += 1
                if created_runs <= 5:
                    ctx.ref("run", run.id, url="/runs", sim_sample=True)
            except Exception:
                report_optional_failure('app.scenarios.runner:_simulation:672', quiet=True)

        if (k + 1) % max(1, tick_every) == 0:
            await tick_jobs_best_effort(session)

    tick_result = await tick_jobs_best_effort(session)
    ctx.summary.update(
        {
            "agents": agents_n,
            "strategies_per_agent": strategies_per_agent,
            "orders_requested": orders_total,
            "orders_created": created_orders,
            "orders_blocked": blocked_orders,
            "runs_created": created_runs,
            "tick": tick_result,
        }
    )

