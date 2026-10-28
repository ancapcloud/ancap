"""Studio ownership, project roles and private run serialization.

Kept independent of orchestration and research services to avoid import cycles.
"""
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from app.db.models import WorkflowProject, WorkflowOperationRun, WorkflowAutomation
from app.services.workflow_ops_support import now, review_hash


async def owned(session, model, owner, row_id, lock=False):
    try:
        row_id = str(UUID(str(row_id)))
    except ValueError:
        raise HTTPException(404, "Not found") from None
    query = select(model).where(model.id == row_id, model.owner_user_id == str(owner))
    if lock:
        query = query.with_for_update()
    row = (await session.execute(query)).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Not found")
    return row


def public_run(row):
    return {"id": str(row.id), "owner_user_id": str(row.owner_user_id), "automation_id": str(row.automation_id) if row.automation_id else None, "kind": row.kind, "state": row.state, "progress": row.progress_json, "review_hash": review_hash(row), "cost_acp": str(row.cost_acp), "max_cost_acp": str(row.max_cost_acp), "created_at": row.created_at, "expires_at": row.expires_at}


async def project_access(session, user_id, project_id, write=False):
    try:
        project_id = str(UUID(str(project_id)))
    except ValueError:
        raise HTTPException(404, "Not found") from None
    row = (await session.execute(select(WorkflowProject).where(WorkflowProject.id == project_id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Not found")
    role = "owner" if str(row.owner_user_id) == str(user_id) else (row.members_json or {}).get(str(user_id))
    if role not in ({"owner", "editor"} if write else {"owner", "editor", "viewer"}):
        raise HTTPException(404, "Not found")
    return row


async def run_access(session, user_id, run_id, write=False):
    try:
        run_id = str(UUID(str(run_id)))
    except ValueError:
        raise HTTPException(404, "Not found") from None
    query = select(WorkflowOperationRun).where(WorkflowOperationRun.id == run_id)
    if write:
        query = query.with_for_update()
    row = (await session.execute(query)).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Not found")
    packets = row.progress_json.get("research_packets", [])
    if packets:
        if row.expires_at and row.expires_at <= now():
            raise HTTPException(404, "Not found")
        await project_access(session, user_id, packets[-1]["packet"]["research"]["project_id"], write=write)
    if str(row.owner_user_id) != str(user_id):
        automation = await session.get(WorkflowAutomation, row.automation_id) if row.automation_id else None
        if automation is None:
            raise HTTPException(404, "Not found")
        await project_access(session, user_id, automation.project_id, write=write)
    return row
