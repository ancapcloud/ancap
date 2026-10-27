"""Private, version-bound user estimates. No payment or ledger mutations."""
from copy import deepcopy
import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select, tuple_
from sqlalchemy.orm import defer
from app.db.models import PaymentIntent, WorkflowRunRecord, WorkflowResultAssessment
from app.schemas.common import Money
from app.schemas.workflow_value import AssessmentCreate, AssessmentHistory, AssessmentPublic, AssessmentState, AssessedResultPublic, ValueSummary

VALUE_RUN_LIMIT = 200


def workflow_result_hash(result) -> str:
    canonical = json.dumps(result, sort_keys=True, default=str, ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def assessment_public(row) -> AssessmentPublic:
    return AssessmentPublic(id=str(row.id), workflow_run_id=str(row.workflow_run_id), result_hash=row.result_hash,
        verdict=row.verdict, baseline_minutes=row.baseline_minutes, assisted_minutes=row.assisted_minutes,
        hourly_rate=row.hourly_rate, hourly_currency=row.hourly_currency, note=row.note, created_at=row.created_at)


async def owned_run(session, owner_id: str, run_id: str, *, lock=False, completed=True):
    try:
        parsed = UUID(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Workflow run not found") from exc
    query = select(WorkflowRunRecord).where(WorkflowRunRecord.id == parsed, WorkflowRunRecord.owner_user_id == UUID(owner_id))
    if lock:
        query = query.with_for_update()
    run = (await session.execute(query)).scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    if completed and (run.status != "completed" or run.result_json is None):
        raise HTTPException(status_code=409, detail="A completed result is required for assessment")
    return run


async def assessment_state(session, owner_id: str, run_id: str) -> AssessmentState:
    run = await owned_run(session, owner_id, run_id)
    digest = workflow_result_hash(run.result_json)
    row = (await session.execute(select(WorkflowResultAssessment).options(defer(WorkflowResultAssessment.result_snapshot_json)).where(
        WorkflowResultAssessment.workflow_run_id == run.id, WorkflowResultAssessment.owner_user_id == UUID(owner_id),
        WorkflowResultAssessment.result_hash == digest))).scalar_one_or_none()
    stale = False
    if row is None:
        stale = bool((await session.execute(select(WorkflowResultAssessment.id).where(
            WorkflowResultAssessment.workflow_run_id == run.id, WorkflowResultAssessment.owner_user_id == UUID(owner_id)).limit(1))).first())
    return AssessmentState(result_hash=digest, assessment=assessment_public(row) if row else None, has_stale_assessment=stale)


async def create_assessment(session, owner_id: str, run_id: str, body: AssessmentCreate) -> AssessmentPublic:
    # Serialize concurrent submissions for this run. The unique constraint is a
    # second invariant; no upsert/update endpoint can overwrite a saved verdict.
    run = await owned_run(session, owner_id, run_id, lock=True)
    if workflow_result_hash(run.result_json) != body.result_hash:
        raise HTTPException(status_code=409, detail="Result changed; reload and review the current result")
    existing = (await session.execute(select(WorkflowResultAssessment.id).where(
        WorkflowResultAssessment.workflow_run_id == run.id, WorkflowResultAssessment.result_hash == body.result_hash))).first()
    if existing:
        raise HTTPException(status_code=409, detail="Assessment for this result version is already saved and cannot be changed")
    row = WorkflowResultAssessment(workflow_run_id=run.id, owner_user_id=UUID(owner_id), result_snapshot_json=deepcopy(run.result_json), **body.model_dump())
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return assessment_public(row)


def summarize_estimates(assessments):
    saved = Decimal(0)
    timed = 0
    valued = 0
    labor = {}
    for row in assessments:
        if row.baseline_minutes is None or row.assisted_minutes is None:
            continue
        difference = Decimal(row.baseline_minutes) - Decimal(row.assisted_minutes)
        saved += difference  # Negative savings are evidence too.
        timed += 1
        if row.hourly_rate is not None and row.hourly_currency:
            unit = row.hourly_currency
            labor[unit] = labor.get(unit, Decimal(0)) + difference * Decimal(row.hourly_rate) / Decimal(60)
            valued += 1
    return (str(saved) if timed else None, timed, valued,
        [Money(currency=unit, amount=str(amount.quantize(Decimal("0.000001")))) for unit, amount in sorted(labor.items())])


async def value_summary(session, owner_id: str, days: int) -> ValueSummary:
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    owner = UUID(owner_id)
    rows = list((await session.execute(select(WorkflowRunRecord.id, WorkflowRunRecord.result_json).where(
        WorkflowRunRecord.owner_user_id == owner, WorkflowRunRecord.status == "completed",
        WorkflowRunRecord.result_json.is_not(None), WorkflowRunRecord.created_at >= since,
        WorkflowRunRecord.created_at <= now).order_by(WorkflowRunRecord.created_at.desc(), WorkflowRunRecord.id.desc()).limit(VALUE_RUN_LIMIT + 1))).all())
    truncated = len(rows) > VALUE_RUN_LIMIT
    rows = rows[:VALUE_RUN_LIMIT]
    assessments = []
    charges = {}
    if rows:
        pairs = [(run.id, workflow_result_hash(run.result_json)) for run in rows]
        assessments = list((await session.execute(select(WorkflowResultAssessment).options(defer(WorkflowResultAssessment.result_snapshot_json)).where(
            WorkflowResultAssessment.owner_user_id == owner,
            tuple_(WorkflowResultAssessment.workflow_run_id, WorkflowResultAssessment.result_hash).in_(pairs)))).scalars())
        intents = (await session.execute(select(PaymentIntent.amount_currency, func.sum(PaymentIntent.amount_value)).where(
            PaymentIntent.owner_user_id == owner, PaymentIntent.workflow_run_id.in_([r.id for r in rows]),
            PaymentIntent.intent_type == "workflow_run", PaymentIntent.status == "captured",
            PaymentIntent.capture_ledger_event_id.is_not(None), PaymentIntent.amount_value > 0).group_by(PaymentIntent.amount_currency))).all()
        for currency, amount in intents:
            charges[currency] = charges.get(currency, Decimal(0)) + Decimal(amount)
    saved, timed, valued, labor = summarize_estimates(assessments)
    counts = {v: sum(a.verdict == v for a in assessments) for v in ("accepted", "revision_requested", "rejected")}
    return ValueSummary(window_start=since, window_end=now, days=days, limit=VALUE_RUN_LIMIT, truncated=truncated,
        completed_count=len(rows), assessed_count=len(assessments), accepted_count=counts["accepted"],
        revision_requested_count=counts["revision_requested"], rejected_count=counts["rejected"],
        timed_assessment_count=timed, labor_valued_count=valued, estimated_minutes_saved=saved,
        estimated_labor_value=labor, ledger_charges=[Money(currency=c, amount=str(a)) for c, a in sorted(charges.items())])


async def assessment_history(session, owner_id: str, run_id: str) -> AssessmentHistory:
    run = await owned_run(session, owner_id, run_id, completed=False)
    rows = list((await session.execute(select(WorkflowResultAssessment).options(defer(WorkflowResultAssessment.result_snapshot_json)).where(
        WorkflowResultAssessment.workflow_run_id == run.id, WorkflowResultAssessment.owner_user_id == UUID(owner_id))
        .order_by(WorkflowResultAssessment.created_at.desc(), WorkflowResultAssessment.id.desc()).limit(51))).scalars())
    return AssessmentHistory(items=[assessment_public(row) for row in rows[:50]], has_more=len(rows) > 50)


async def assessed_result(session, owner_id: str, assessment_id: str) -> AssessedResultPublic:
    try:
        parsed = UUID(assessment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Assessment not found") from exc
    row = (await session.execute(select(WorkflowResultAssessment).join(WorkflowRunRecord,
        WorkflowRunRecord.id == WorkflowResultAssessment.workflow_run_id).where(
        WorkflowResultAssessment.id == parsed, WorkflowResultAssessment.owner_user_id == UUID(owner_id),
        WorkflowRunRecord.owner_user_id == UUID(owner_id)))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if workflow_result_hash(row.result_snapshot_json) != row.result_hash:
        raise HTTPException(status_code=409, detail="Archived result integrity check failed")
    return AssessedResultPublic(assessment_id=str(row.id), result_hash=row.result_hash, result=row.result_snapshot_json)
