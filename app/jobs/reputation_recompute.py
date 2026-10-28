"""
Reputation 2.0 recompute worker: trust_score and reputation_snapshots from events + edges.

Run as: CLI (python -m app.jobs.reputation_recompute), background worker, or on-demand POST /v1/reputation/recompute.
Uses async SQLAlchemy; pass session from get_db or async_session_maker().
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    RelationshipEdgeDaily,
    TrustScore,
    ReputationSnapshot,
    ReputationEvent,
    EdgeTypeEnum,
)
from app.config import get_settings

ALGO_TRUST_VERSION = "trust2-v1"
ALGO_REP_VERSION = "rep2-v1"


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _exp_decay(age_days: float, half_life_days: float) -> float:
    if half_life_days <= 0:
        return 1.0
    return math.pow(0.5, age_days / half_life_days)


@dataclass(frozen=True)
class WindowSpec:
    name: str
    days: int
    half_life_days: float


def _windows_from_settings() -> list[WindowSpec]:
    s = get_settings()
    return [
        WindowSpec("30d", 30, float(s.reputation_half_life_30d)),
        WindowSpec("90d", 90, float(s.reputation_half_life_90d)),
    ]


async def recompute_for_subject(
    session: AsyncSession,
    subject_type: str,
    subject_id: UUID,
    now: datetime | None = None,
    commit: bool = True,
) -> None:
    """Compute trust_score and reputation_snapshot for each window; upsert into DB. Set commit=False if caller commits."""
    now = now or datetime.utcnow()
    today = now.date()
    settings = get_settings()
    windows = _windows_from_settings()

    trust_by_window: dict[str, float] = {}
    trust_components_by_window: dict[str, dict[str, Any]] = {}
    trust_inputs_hash_by_window: dict[str, str] = {}

    for w in windows:
        start_day = today - timedelta(days=w.days)

        # Edges: subject as seller (dst)
        q_edges = (
            select(
                RelationshipEdgeDaily.src_id,
                RelationshipEdgeDaily.dst_id,
                func.coalesce(func.sum(RelationshipEdgeDaily.count), 0).label("cnt"),
                func.coalesce(func.sum(RelationshipEdgeDaily.amount_sum), 0).label("amt"),
            )
            .where(
                RelationshipEdgeDaily.edge_type == EdgeTypeEnum.order.value,
                RelationshipEdgeDaily.day >= start_day,
                RelationshipEdgeDaily.day <= today,
                RelationshipEdgeDaily.dst_type == subject_type,
                RelationshipEdgeDaily.dst_id == subject_id,
            )
            .group_by(RelationshipEdgeDaily.src_id, RelationshipEdgeDaily.dst_id)
        )
        r = await session.execute(q_edges)
        rows = r.all()

        total_buyers = len(rows)
        total_orders = 0
        total_amt = 0.0
        buyer_amts: dict[str, float] = {}
        for buyer_id, _seller_id, cnt, amt in rows:
            total_orders += int(cnt or 0)
            amt_f = float(amt or 0)
            buyer_amts[str(buyer_id)] = buyer_amts.get(str(buyer_id), 0) + amt_f
            total_amt += amt_f

        buyer_diversity = 0.0
        if total_orders > 0:
            buyer_diversity = _clamp(total_buyers / max(total_orders, 1), 0.0, 1.0)

        # Reciprocity: subject also bought from these buyers?
        reciprocity_amt = 0.0
        if buyer_amts:
            try:
                buyer_uuids = [UUID(b) for b in buyer_amts]
            except (ValueError, TypeError):
                buyer_uuids = []
            if buyer_uuids:
                q_back = (
                    select(
                        RelationshipEdgeDaily.dst_id,
                        func.coalesce(func.sum(RelationshipEdgeDaily.amount_sum), 0).label("back_amt"),
                    )
                    .where(
                        RelationshipEdgeDaily.edge_type == EdgeTypeEnum.order.value,
                        RelationshipEdgeDaily.day >= start_day,
                        RelationshipEdgeDaily.day <= today,
                        RelationshipEdgeDaily.src_type == subject_type,
                        RelationshipEdgeDaily.src_id == subject_id,
                        RelationshipEdgeDaily.dst_id.in_(buyer_uuids),
                    )
                    .group_by(RelationshipEdgeDaily.dst_id)
                )
                back_r = await session.execute(q_back)
                back_map = {str(buyer_id): float(back_amt or 0) for buyer_id, back_amt in back_r.all()}
                for buyer_id, fwd_amt in buyer_amts.items():
                    reciprocity_amt += min(fwd_amt, back_map.get(buyer_id, 0.0))

        reciprocity = 0.0
        if total_amt > 0:
            reciprocity = _clamp(reciprocity_amt / total_amt, 0.0, 1.0)

        cycle_flag = 0.0  # MVP: add cycle detection later

        if total_orders == 0 and total_buyers == 0:
            trust = 1.0
            components = {"buyer_diversity": 1.0, "reciprocity": 0.0, "cycle_flag": 0.0, "sybil_risk": 0.0}
        else:
            sybil_risk = _clamp(
                0.5 * reciprocity + 0.4 * (1.0 - buyer_diversity) + 0.7 * cycle_flag,
                0.0,
                1.0,
            )
            trust = _clamp(1.0 - sybil_risk, 0.0, 1.0)
            components = {
                "buyer_diversity": buyer_diversity,
                "reciprocity": reciprocity,
                "cycle_flag": cycle_flag,
                "sybil_risk": sybil_risk,
                "total_orders": total_orders,
                "total_buyers": total_buyers,
                "total_amount": total_amt,
            }

        inputs_hash = _sha256_hex(f"{subject_type}:{subject_id}:{w.name}:{sorted(components.items())}")
        trust_by_window[w.name] = trust
        trust_components_by_window[w.name] = components
        trust_inputs_hash_by_window[w.name] = inputs_hash

        stmt = insert(TrustScore).values(
            subject_type=subject_type,
            subject_id=subject_id,
            window=w.name,
            algo_version=ALGO_TRUST_VERSION,
            trust_score=trust,
            components=components,
            inputs_hash=inputs_hash,
            computed_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["subject_type", "subject_id", "window", "algo_version"],
            set_={
                "trust_score": stmt.excluded.trust_score,
                "components": stmt.excluded.components,
                "inputs_hash": stmt.excluded.inputs_hash,
                "computed_at": stmt.excluded.computed_at,
            },
        )
        await session.execute(stmt)

    # Reputation snapshots: quality from events * trust
    for w in windows:
        start_ts = now - timedelta(days=w.days)

        q_events = (
            select(ReputationEvent.value, ReputationEvent.event_type, ReputationEvent.created_at)
            .where(
                ReputationEvent.subject_type == subject_type,
                ReputationEvent.subject_id == subject_id,
                ReputationEvent.created_at >= start_ts,
                ReputationEvent.created_at <= now,
            )
        )
        r = await session.execute(q_events)
        events = r.all()

        quality_sum = 0.0
        weight_sum = 0.0
        buckets: dict[str, float] = {
            "execution_quality": 0.0,
            "market_quality": 0.0,
            "audit_quality": 0.0,
            "moderation": 0.0,
        }
        bucket_w: dict[str, float] = {k: 0.0 for k in buckets}

        for value, ev_type, created_at in events:
            age_days = (now - created_at).total_seconds() / 86400.0
            w_decay = _exp_decay(age_days, w.half_life_days)
            v = float(value) if value is not None else 0.0
            ev_str = str(ev_type) if ev_type else ""
            if ev_str.startswith("run_") or ev_str.startswith("evaluation_"):
                b = "execution_quality"
            elif ev_str.startswith("order_") or ev_str.startswith("access_"):
                b = "market_quality"
            elif ev_str.startswith("audit_"):
                b = "audit_quality"
            elif ev_str.startswith("moderation_"):
                b = "moderation"
            else:
                b = "market_quality"
            quality_sum += v * w_decay
            weight_sum += w_decay
            buckets[b] += v * w_decay
            bucket_w[b] += w_decay

        # Stable score: clamp(avg(decay-weighted values), 0, 1) * trust; optional: sigmoid(weighted_sum)
        quality = quality_sum / weight_sum if weight_sum > 0 else 0.0
        trust = trust_by_window[w.name]
        quality01 = _clamp(quality, 0.0, 1.0)
        final01 = _clamp(quality01 * trust, 0.0, 1.0)
        final_score = 100.0 * final01

        # Anti-flip-flop guardrail: clamp score movement per recompute window.
        prev_q = (
            select(ReputationSnapshot.score)
            .where(
                ReputationSnapshot.subject_type == subject_type,
                ReputationSnapshot.subject_id == subject_id,
                ReputationSnapshot.window == w.name,
                ReputationSnapshot.algo_version == ALGO_REP_VERSION,
            )
            .limit(1)
        )
        prev_r = await session.execute(prev_q)
        prev_score = prev_r.scalar_one_or_none()
        if prev_score is not None:
            max_delta = float(settings.reputation_max_score_delta_per_recompute)
            lower = float(prev_score) - max_delta
            upper = float(prev_score) + max_delta
            clamped = _clamp(final_score, lower, upper)
            if clamped != final_score:
                comp_out_guard = {
                    "previous_score": float(prev_score),
                    "max_delta": max_delta,
                    "raw_score": float(final_score),
                    "clamped_score": float(clamped),
                }
            else:
                comp_out_guard = None
            final_score = clamped
        else:
            comp_out_guard = None

        comp_out: dict[str, Any] = {
            "quality": quality01,
            "trust": trust,
            "final01": final01,
            "trust_components": trust_components_by_window[w.name],
            "buckets": {
                k: (_clamp(buckets[k] / bucket_w[k], -1.0, 1.0) if bucket_w[k] > 0 else 0.0)
                for k in buckets
            },
            "event_count": len(events),
        }
        if comp_out_guard:
            comp_out["flipflop_guard"] = comp_out_guard
        inputs_hash = _sha256_hex(
            f"{subject_type}:{subject_id}:{w.name}:{ALGO_REP_VERSION}:{trust_inputs_hash_by_window[w.name]}:{len(events)}"
        )

        stmt = insert(ReputationSnapshot).values(
            subject_type=subject_type,
            subject_id=subject_id,
            window=w.name,
            algo_version=ALGO_REP_VERSION,
            score=final_score,
            components=comp_out,
            inputs_hash=inputs_hash,
            computed_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["subject_type", "subject_id", "window", "algo_version"],
            set_={
                "score": stmt.excluded.score,
                "components": stmt.excluded.components,
                "inputs_hash": stmt.excluded.inputs_hash,
                "computed_at": stmt.excluded.computed_at,
            },
        )
        await session.execute(stmt)

    if commit:
        await session.commit()


async def recompute_all_subjects(
    session: AsyncSession,
    subject_type: str,
    subject_ids: list[UUID],
    batch_size: int = 100,
) -> None:
    """Recompute trust + snapshots for many subjects. Prefer separate transactions per batch."""
    for i in range(0, len(subject_ids), batch_size):
        batch = subject_ids[i : i + batch_size]
        for sid in batch:
            await recompute_for_subject(session, subject_type, sid if isinstance(sid, UUID) else UUID(str(sid)), None)
        await session.commit()
