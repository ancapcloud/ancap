"""A bounded research pilot. No LLM, payment or delivery authority."""
from datetime import timedelta

import httpx
from fastapi import HTTPException
from sqlalchemy import delete, func, select

from app.db.models import WorkflowProject, ResearchSource, ResearchSnapshot, ResearchClaim
from app.services import research_fetch
from app.services.workflow_ops_access import project_access
from app.services.workflow_ops_support import digest, now


async def purge_expired(session):
    expired = select(ResearchSource.id).where(ResearchSource.expires_at <= now()).order_by(ResearchSource.id).limit(100).with_for_update(skip_locked=True)
    await session.execute(delete(ResearchSource).where(ResearchSource.id.in_(expired)))


async def project(session, user, project_id, write=False):
    # Serialize permission checks, limits and mutations with project deletion/member edits.
    if write:
        await session.execute(select(WorkflowProject.id).where(WorkflowProject.id == str(project_id)).with_for_update())
    return await project_access(session, user, str(project_id), write=write)


async def source(session, user, project_id, source_id, write=False):
    p = await project(session, user, project_id, write)
    query = select(ResearchSource).where(ResearchSource.id == str(source_id),
        ResearchSource.project_id == str(project_id), ResearchSource.expires_at > now())
    if write:
        query = query.with_for_update()
    row = (await session.execute(query)).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Source not found")
    return p, row


def public_source(row):
    return {k: getattr(row, k) for k in ("id", "project_id", "title", "url", "permission_basis", "status", "latest_hash", "checked_at", "expires_at")}


async def add_source(session, user, project_id, body):
    p = await project(session, user, project_id, True)
    # Purge this project's expired content before evaluating its bounded quota.
    await session.execute(delete(ResearchSource).where(ResearchSource.project_id == p.id, ResearchSource.expires_at <= now()))
    rows = (await session.execute(select(ResearchSource).where(ResearchSource.project_id == p.id))).scalars().all()
    if len(rows) >= 10:
        raise HTTPException(409, "Pilot limit: ten sources per project")
    if any(r.url == body.url for r in rows):
        raise HTTPException(409, "Source already registered")
    row = ResearchSource(project_id=p.id, **body.model_dump(), status="unchecked", expires_at=now()+timedelta(days=p.retention_days))
    session.add(row)
    await session.flush()
    return public_source(row)


async def check_source(session, user, project_id, source_id):
    _, row = await source(session, user, project_id, source_id, True)
    if row.checked_at and (now() - row.checked_at).total_seconds() < 60:
        raise HTTPException(429, "Wait sixty seconds before checking this source again")
    snapshots = (await session.execute(select(ResearchSnapshot).where(ResearchSnapshot.source_id == row.id)
        .order_by(ResearchSnapshot.created_at.desc(), ResearchSnapshot.id.desc()))).scalars().all()
    if len(snapshots) >= 20:
        raise HTTPException(409, "Pilot version limit reached; export and review before replacing this source")
    try:
        raw_hash, text_hash, text_content = await research_fetch.fetch_page(row.url)
    except (ValueError, OSError, TimeoutError, httpx.HTTPError):
        if row.expires_at <= now():
            raise HTTPException(404, "Source expired during collection") from None
        row.status, row.checked_at = "unavailable", now()
        await session.flush()
        return {"source": public_source(row), "change": "unavailable", "snapshot": None}
    if row.expires_at <= now():
        raise HTTPException(404, "Source expired during collection")
    previous = snapshots[0] if snapshots else None
    change = "baseline" if previous is None else "unchanged" if previous.raw_hash == raw_hash else "technical" if previous.text_hash == text_hash else "content_change_requires_review"
    if change != "unchanged":
        version = ResearchSnapshot(source_id=row.id, raw_hash=raw_hash, text_hash=text_hash,
            text_content=text_content, change_kind=change, created_at=now())
        session.add(version)
    row.status, row.latest_hash, row.checked_at = change, text_hash, now()
    await session.flush()
    return {"source": public_source(row), "change": change,
        "snapshot": {"hash": text_hash, "text": text_content},
        "changes": research_fetch.text_changes(previous.text_content, text_content) if previous else {"items": [], "truncated": False},
        "previous_excerpt": previous.text_content[:1000] if previous else None,
        "excerpts_are_truncated": bool(previous and len(previous.text_content) > 1000)}


async def add_claim(session, user, project_id, body):
    _, row = await source(session, user, project_id, body.source_id, True)
    count = await session.scalar(select(func.count()).select_from(ResearchClaim).where(ResearchClaim.source_id == row.id))
    if count >= 50:
        raise HTTPException(409, "Pilot limit: fifty claims per source")
    version = (await session.execute(select(ResearchSnapshot).where(ResearchSnapshot.source_id == row.id,
        ResearchSnapshot.text_hash == body.source_hash).limit(1))).scalar_one_or_none()
    if row.latest_hash != body.source_hash or row.status == "unavailable" or version is None:
        raise HTTPException(409, "Source changed or is unavailable; reload and review")
    if body.excerpt not in version.text_content:
        raise HTTPException(422, "Excerpt must occur in the selected source text")
    claim = ResearchClaim(**body.model_dump(exclude={"source_id"}), source_id=row.id,
        reviewer_user_id=user, created_at=now())
    session.add(claim)
    await session.flush()
    return {"id": claim.id, "verification_basis": "human_source_link_not_independent_fact_check"}


async def brief(session, user, project_id):
    p = await project(session, user, project_id)
    sources = (await session.execute(select(ResearchSource).where(ResearchSource.project_id == p.id,
        ResearchSource.expires_at > now()).order_by(ResearchSource.id))).scalars().all()
    claims = (await session.execute(select(ResearchClaim).where(ResearchClaim.source_id.in_([r.id for r in sources]))
        .order_by(ResearchClaim.created_at, ResearchClaim.id))).scalars().all() if sources else []
    lookup = {s.id: s for s in sources}
    items = []
    for c in claims:
        s = lookup[c.source_id]
        items.append({"id": c.id, "source_id": s.id, "source_hash": c.source_hash,
            "statement": c.statement, "excerpt": c.excerpt, "reviewer_verdict": c.verdict,
            "status": "source_unavailable" if s.status == "unavailable" else "requires_update" if s.latest_hash != c.source_hash else c.verdict,
            "reviewer_user_id": c.reviewer_user_id, "created_at": c.created_at})
    payload = {"project_id": p.id, "project_name": p.name, "sources": [public_source(s) for s in sources], "claims": items}
    return {**payload, "version_hash": digest(payload), "state": "draft_requires_review",
        "independent_fact_check": False, "delivery_enabled": False,
        "unresolved_count": sum(c["status"] != "supported_by_source" for c in items),
        "limits": {"sources": 10, "versions_per_source": 20, "claims_per_source": 50},
        "collection": "manual_public_utf8_html_no_scheduler_no_llm"}


async def snapshots(session, user, project_id, source_id):
    await source(session, user, project_id, source_id)
    rows = (await session.execute(select(ResearchSnapshot).where(ResearchSnapshot.source_id == str(source_id))
        .order_by(ResearchSnapshot.created_at.desc(), ResearchSnapshot.id.desc()).limit(20))).scalars().all()
    return [{"id": r.id, "hash": r.text_hash, "raw_hash": r.raw_hash, "text": r.text_content,
        "change": r.change_kind, "created_at": r.created_at} for r in rows]


async def upload_quality_fixtures(session, project_id: str, fixtures: dict):
    """Upload quality test fixtures for ROP-03 bounded collection."""
    from app.db.models import QualityFixture
    
    fixture_records = []
    for fixture_type, items in fixtures.items():
        for item in items:
            record = QualityFixture(
                project_id=project_id,
                fixture_type=fixture_type,
                language=item.get("language"),
                document_type=item.get("document_type"),
                source_url=item.get("source_url"),
                fixture_data=item,
                expected_hash=item.get("expected_hash"),
                status="pending"
            )
            session.add(record)
            fixture_records.append({
                "fixture_id": record.id,
                "project_id": project_id,
                "fixture_type": fixture_type,
                "status": "pending"
            })
    await session.flush()
    return {"status": "uploaded", "fixture_count": len(fixture_records), "records": fixture_records}


async def get_quality_fixture(session, project_id: str, fixture_id: str):
    """Get a quality test fixture by ID."""
    from app.db.models import QualityFixture
    row = (await session.execute(select(QualityFixture).where(
        QualityFixture.id == fixture_id, QualityFixture.project_id == project_id
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Fixture not found")
    return {
        "fixture_id": str(row.id),
        "project_id": row.project_id,
        "fixture_type": row.fixture_type,
        "language": row.language,
        "document_type": row.document_type,
        "source_url": row.source_url,
        "status": row.status,
        "created_at": row.created_at.isoformat()
    }


async def remove_quality_fixture(session, project_id: str, fixture_id: str):
    """Remove a quality test fixture."""
    from app.db.models import QualityFixture
    row = (await session.execute(select(QualityFixture).where(
        QualityFixture.id == fixture_id, QualityFixture.project_id == project_id
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Fixture not found")
    await session.delete(row)
    await session.flush()
    return {"status": "deleted", "fixture_id": fixture_id}


async def remove_source(session, user, project_id, source_id):
    _, row = await source(session, user, project_id, source_id, True)
    await session.delete(row)
    await session.flush()
    return {"deleted": True, "snapshots_and_claims": "deleted"}
