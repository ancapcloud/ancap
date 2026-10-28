"""Immutable source/result packets using the existing Studio review and outbox.

Attaching a packet never executes a model, charges funds or sends anything.
"""
from copy import deepcopy

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from app.db.models import ResearchSource, WorkflowAutomation, WorkflowRunRecord, WorkflowConnection
from app.services import research_ops
from app.services.workflow_ops_support import bounded_json, digest, now, operation_output, review_hash
from app.services.workflow_value import workflow_result_hash


def binding_hash(research):
    # Freshness observations can advance without changing the reviewed evidence.
    sources = [{key: source[key] for key in ("id", "title", "url", "permission_basis", "latest_hash", "expires_at")}
               for source in research["sources"]]
    return digest({"project_id": research["project_id"], "project_name": research["project_name"],
                   "sources": sources, "claims": research["claims"]})


async def current_research(session, user, project_id, ids):
    from app.services.workflow_ops_access import project_access
    await project_access(session, user, project_id)
    rows = (await session.execute(select(ResearchSource).where(ResearchSource.project_id == str(project_id),
        ResearchSource.id.in_(ids), ResearchSource.expires_at > now()).order_by(ResearchSource.id)
        .with_for_update())).scalars().all()
    if {str(r.id) for r in rows} != set(ids):
        raise HTTPException(409, "Research sources were removed or expired; rebuild the packet")
    if any(r.status in {"unchecked", "unavailable"} or not r.latest_hash for r in rows):
        raise HTTPException(409, "Check all selected sources before building or approving the packet")
    brief = await research_ops.brief(session, user, project_id)
    selected = set(ids)
    value = {"project_id": str(project_id), "project_name": brief["project_name"],
        "sources": [r for r in brief["sources"] if str(r["id"]) in selected],
        "claims": [r for r in brief["claims"] if str(r["source_id"]) in selected]}
    value["unresolved_count"] = sum(claim["status"] != "supported_by_source" for claim in value["claims"])
    return jsonable_encoder(value), min(r.expires_at for r in rows)


def client_research(value):
    # Recipient consent is not permission to disclose internal collection notes
    # or teammate identifiers. Those remain in the private registry.
    return {"project_id": value["project_id"], "project_name": value["project_name"],
        "sources": [{key: source[key] for key in ("id", "title", "url", "status", "latest_hash", "checked_at")}
                    for source in value["sources"]],
        "claims": [{key: claim[key] for key in ("id", "source_id", "source_hash", "statement", "excerpt", "reviewer_verdict", "status", "created_at")}
                   for claim in value["claims"]], "unresolved_count": value["unresolved_count"]}


async def result_versions(session, operation, expected=None):
    ids = [str(item["run_id"]) for item in operation.progress_json.get("items", [])]
    if not ids:
        raise HTTPException(409, "An existing completed Studio report is required")
    rows = (await session.execute(select(WorkflowRunRecord).where(WorkflowRunRecord.id.in_(ids),
        WorkflowRunRecord.owner_user_id == str(operation.owner_user_id)).order_by(WorkflowRunRecord.id)
        .with_for_update())).scalars().all()
    if len(rows) != len(ids) or any(r.status != "completed" or r.result_json is None for r in rows):
        raise HTTPException(409, "Workflow result is missing or expired")
    versions = [{"run_id": str(r.id), "result_hash": workflow_result_hash(r.result_json)} for r in rows]
    outputs = {str(i["run_id"]): i["output"] for i in operation.progress_json["items"]}
    if any(v["result_hash"] != workflow_result_hash(outputs[v["run_id"]]) for v in versions) or (expected is not None and versions != expected):
        raise HTTPException(409, "Workflow result changed; rebuild and review the packet")
    return versions


async def attach_packet(session, user, project_id, body):
    from app.services.workflow_ops_access import project_access, run_access, public_run
    await project_access(session, user, str(project_id), write=True)
    operation = await run_access(session, user, str(body.operation_id), write=True)
    automation = await session.get(WorkflowAutomation, operation.automation_id) if operation.automation_id else None
    if automation is None or str(automation.project_id) != str(project_id):
        raise HTTPException(404, "Report not found in this project")
    if operation.state != "awaiting_review" or review_hash(operation) != body.expected_review_hash:
        raise HTTPException(409, "Report changed or is not awaiting review; reload")
    if len(operation.snapshot_json["definition"].get("connection_ids", [])) > 1:
        raise HTTPException(409, "The research pilot permits one delivery destination")
    await validate_channel(session, operation)
    history = list(operation.progress_json.get("research_packets", []))
    versions = await result_versions(session, operation)
    ids = sorted(str(source) for source in body.source_ids)
    research, expiry = await current_research(session, user, str(project_id), ids)
    output = {"items": [item["output"] for item in operation.progress_json["items"]]}
    packet = bounded_json({"format": "ancap-research-client-packet/v1", "operation_id": str(operation.id),
        "research": client_research(research), "workflow_versions": versions, "result": output,
        "review_scope": "exact_packet_human_review_not_independent_fact_check"}, 100000)
    if history and history[-1]["hash"] == digest(packet) and history[-1]["binding_hash"] == binding_hash(research):
        return public_run(operation)
    if len(history) >= 3:
        raise HTTPException(409, "Three packet versions reached; create a new report instead of rewriting history")
    saved = {"version": len(history)+1, "hash": digest(packet), "binding_hash": binding_hash(research),
        "source_ids": ids, "packet": packet, "created_at": now().isoformat()}
    operation.progress_json = {**operation.progress_json, "research_packets": [*history, saved]}
    operation.expires_at = min(operation.expires_at, expiry) if operation.expires_at else expiry
    await session.flush()
    return public_run(operation)


async def validate_packet(session, operation, user):
    from app.services.workflow_ops_access import project_access
    saved = operation.progress_json["research_packets"][-1]
    packet = saved["packet"]
    if operation.expires_at and operation.expires_at <= now():
        raise HTTPException(409, "Research packet expired")
    if digest(packet) != saved["hash"]:
        raise HTTPException(409, "Research packet integrity check failed")
    project_id = packet["research"]["project_id"]
    await project_access(session, user, project_id, write=True)
    await project_access(session, str(operation.owner_user_id), project_id)
    await result_versions(session, operation, packet["workflow_versions"])
    current, _ = await current_research(session, user, project_id, saved["source_ids"])
    if binding_hash(current) != saved["binding_hash"]:
        raise HTTPException(409, "Research evidence changed; build a new packet and review it")
    return saved


async def approve_packet(session, operation, user, edited_output):
    saved = await validate_packet(session, operation, user)
    packet = deepcopy(saved["packet"])
    if edited_output is not None:
        packet["result"] = bounded_json(edited_output, 100000)
    bounded_json(packet, 100000)
    return {"output": packet, "approval": {"draft_hash": saved["hash"], "packet_hash": digest(packet),
        "reviewer_user_id": user, "approved_at": now().isoformat(), "scope": packet["review_scope"]}}


async def validate_delivery(session, operation):
    approval = operation.progress_json.get("research_approval")
    if not approval:
        raise HTTPException(409, "A reviewed research packet is required")
    saved = await validate_packet(session, operation, approval["reviewer_user_id"])
    if approval["draft_hash"] != saved["hash"] or digest(operation_output(operation)) != approval["packet_hash"]:
        raise HTTPException(409, "Approved packet changed; delivery blocked")
    await validate_channel(session, operation)


async def validate_channel(session, operation):
    # The existing text adapters shorten payloads; only the full JSON webhook is
    # eligible for the pilot. No destination is also valid for private review.
    ids = operation.snapshot_json["definition"].get("connection_ids", [])
    if len(ids) > 1:
        raise HTTPException(409, "One webhook destination is supported")
    if ids:
        connection = (await session.execute(select(WorkflowConnection).where(WorkflowConnection.id == ids[0],
            WorkflowConnection.owner_user_id == str(operation.owner_user_id)))).scalar_one_or_none()
        if connection is None or connection.kind != "webhook" or not connection.allow_delivery:
            raise HTTPException(409, "A consented full-payload webhook is required for research delivery")
