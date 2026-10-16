"""People + AI project economy service (Wave 1 catalog + platform seeds)."""

from __future__ import annotations

import secrets
import re
import uuid
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.db.models import (
    EconomyApplication,
    EconomyApplicationStatusEnum,
    EconomyProject,
    EconomyProjectKindEnum,
    EconomyProjectStatusEnum,
    EconomyTask,
    EconomyTaskAssigneeTypeEnum,
    User,
)
from app.schemas.project_economy import (
    EconomyApplicationCreate,
    EconomyProjectCreate,
    EconomyProjectUpdate,
    EconomyTaskCreate,
)
from app.services.auth import hash_password

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,79}$")

# Public author of the five AI demo catalog entries (email is lookup-only, never in API).
SEED_OWNER_EMAIL = "dragon.cat.trx@gmail.com"
SEED_OWNER_DISPLAY_NAME = "3n3rgy"

# First five catalog entries: AI-authored demo projects from Wave 0.
PLATFORM_SEED_PROJECTS: tuple[dict, ...] = (
    {
        "id": "11111111-1111-4111-8111-111111111101",
        "seed_key": "aeterna",
        "slug": "aeterna-longevity-brief",
        "title": "AETERNA — longevity research brief",
        "summary": "Turn a broad interest in longevity research into a clear brief for a qualified professional.",
        "result_promise": "A research outline, evidence checklist and professional-review questions.",
        "earning_model": "Illustrative digital brief only — no medical service or patient work.",
        "kind": EconomyProjectKindEnum.demo.value,
        "background_href": "/aeterna",
        "task_title": "Draft longevity research questions",
        "acceptance_criteria": "Sources dated, limitations listed, no individual health assessment claimed.",
    },
    {
        "id": "11111111-1111-4111-8111-111111111102",
        "seed_key": "galaxy",
        "slug": "galaxy-edge-infra-concept",
        "title": "Galaxy — encrypted edge infrastructure concept",
        "summary": "Sketch an encrypted edge-computing concept for a hypothetical space project.",
        "result_promise": "An architecture brief and checks for a potential infrastructure partner.",
        "earning_model": "Concept brief only — no orbital deployment or supplier agreement.",
        "kind": EconomyProjectKindEnum.concept.value,
        "background_href": "/galaxy",
        "task_title": "Map trust boundaries and open questions",
        "acceptance_criteria": "Each trust boundary identifiable; hosting and key custody questions listed.",
    },
    {
        "id": "11111111-1111-4111-8111-111111111103",
        "seed_key": "lunar",
        "slug": "lunar-catalog-card",
        "title": "Lunar — science catalog card sample",
        "summary": "Design a science-themed catalog using fictional lunar parcel records.",
        "result_promise": "A sample catalog specification with a clearly labeled fictional entry.",
        "earning_model": "Educational catalog sample — no land title or mining rights.",
        "kind": EconomyProjectKindEnum.demo.value,
        "background_href": "/lunar",
        "task_title": "Propose catalog record schema",
        "acceptance_criteria": "Fictional entry labeled; ownership claims explicitly excluded.",
    },
    {
        "id": "11111111-1111-4111-8111-111111111104",
        "seed_key": "stardust",
        "slug": "stardust-weather-brief",
        "title": "Stardust — weather observation brief",
        "summary": "Define a weather-research dashboard with sample observations and human review.",
        "result_promise": "A dashboard brief, input schema and sample review note.",
        "earning_model": "Dashboard example — not a live forecast or emergency alert.",
        "kind": EconomyProjectKindEnum.demo.value,
        "background_href": "/stardust",
        "task_title": "Structure observation review fields",
        "acceptance_criteria": "Missing source/timestamp flagged; human verification status required.",
    },
    {
        "id": "11111111-1111-4111-8111-111111111105",
        "seed_key": "starlink",
        "slug": "starlink-install-intake",
        "title": "Starlink — installation intake for independent technician",
        "summary": "Prepare a sample satellite-internet installation request for an independent technician.",
        "result_promise": "A site-intake brief and questions before a service quote.",
        "earning_model": "Intake sample only — does not book installation or claim Starlink partnership.",
        "kind": EconomyProjectKindEnum.concept.value,
        "background_href": "/starlink-install",
        "task_title": "Collect site intake checklist",
        "acceptance_criteria": "Location, mount, power, cable route and access permission fields present.",
    },
)

_PROJECT_LOAD_OPTIONS = (
    selectinload(EconomyProject.tasks),
    selectinload(EconomyProject.owner),
)


def mutations_enabled() -> bool:
    return bool(get_settings().ff_project_economy)


def require_mutations() -> None:
    if not mutations_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project economy mutations are disabled (FF_PROJECT_ECONOMY=false)",
        )


async def ensure_seed_owner(session: AsyncSession) -> User:
    """Find or create the public seed author. Email is never returned by the API."""
    user = (
        await session.execute(select(User).where(User.email == SEED_OWNER_EMAIL))
    ).scalar_one_or_none()
    if user is None:
        user = User(
            id=str(uuid.uuid4()),
            email=SEED_OWNER_EMAIL,
            # Unusable login: random secret is discarded after hashing.
            password_hash=hash_password(secrets.token_urlsafe(48)),
            display_name=SEED_OWNER_DISPLAY_NAME,
        )
        session.add(user)
        await session.flush()
        return user

    if not (user.display_name or "").strip():
        user.display_name = SEED_OWNER_DISPLAY_NAME
        await session.flush()
    return user


async def ensure_platform_seeds(session: AsyncSession) -> None:
    """Idempotently insert the five AI demo projects owned by 3n3rgy."""
    owner = await ensure_seed_owner(session)
    owner_id = str(owner.id)
    existing = (
        await session.execute(
            select(EconomyProject).where(EconomyProject.is_platform_seed.is_(True))
        )
    ).scalars().all()
    by_key = {row.seed_key: row for row in existing if row.seed_key}
    dirty = False

    for seed in PLATFORM_SEED_PROJECTS:
        project = by_key.get(seed["seed_key"])
        if project is None:
            project = EconomyProject(
                id=seed["id"],
                owner_user_id=owner_id,
                slug=seed["slug"],
                title=seed["title"],
                summary=seed["summary"],
                result_promise=seed["result_promise"],
                earning_model=seed["earning_model"],
                status=EconomyProjectStatusEnum.published.value,
                kind=seed["kind"],
                seed_key=seed["seed_key"],
                is_platform_seed=True,
                background_href=seed["background_href"],
                metadata_json={
                    "ai_authored": True,
                    "platform_order": PLATFORM_SEED_PROJECTS.index(seed) + 1,
                    "disclosure": "AI-created demo project — not a completed customer order.",
                },
            )
            session.add(project)
            session.add(
                EconomyTask(
                    id=str(uuid.uuid4()),
                    project_id=seed["id"],
                    title=seed["task_title"],
                    acceptance_criteria=seed["acceptance_criteria"],
                    stage_order=1,
                    price_acp=None,
                    assignee_type=EconomyTaskAssigneeTypeEnum.human.value,
                )
            )
            dirty = True
        elif project.owner_user_id != owner_id:
            project.owner_user_id = owner_id
            dirty = True

    if dirty:
        await session.commit()


def _owner_display_name(project: EconomyProject) -> str | None:
    if project.is_platform_seed:
        return SEED_OWNER_DISPLAY_NAME
    owner = getattr(project, "owner", None)
    if owner is None:
        return None
    name = (owner.display_name or "").strip()
    return name or None


def project_to_public(project: EconomyProject) -> dict:
    return {
        "id": project.id,
        "owner_user_id": project.owner_user_id,
        "owner_display_name": _owner_display_name(project),
        "slug": project.slug,
        "title": project.title,
        "summary": project.summary,
        "result_promise": project.result_promise,
        "earning_model": project.earning_model,
        "status": project.status,
        "kind": project.kind,
        "seed_key": project.seed_key,
        "is_platform_seed": bool(project.is_platform_seed),
        "background_href": project.background_href,
        "metadata_json": project.metadata_json or {},
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "tasks": [
            {
                "id": task.id,
                "project_id": task.project_id,
                "title": task.title,
                "acceptance_criteria": task.acceptance_criteria,
                "stage_order": task.stage_order,
                "price_acp": task.price_acp,
                "assignee_type": task.assignee_type,
                "created_at": task.created_at,
            }
            for task in sorted(project.tasks or [], key=lambda item: (item.stage_order, str(item.id)))
        ],
    }


async def list_projects(
    session: AsyncSession,
    *,
    viewer_user_id: UUID | None,
    include_mine: bool,
    limit: int,
    offset: int,
) -> tuple[list[EconomyProject], int]:
    await ensure_platform_seeds(session)
    enabled = mutations_enabled()

    if enabled:
        if include_mine and viewer_user_id is not None:
            where_clause = or_(
                EconomyProject.status == EconomyProjectStatusEnum.published.value,
                EconomyProject.owner_user_id == str(viewer_user_id),
            )
        else:
            where_clause = EconomyProject.status == EconomyProjectStatusEnum.published.value
    else:
        # Preview: only platform seed demos, no community UGC disclosure.
        where_clause = and_(
            EconomyProject.is_platform_seed.is_(True),
            EconomyProject.status == EconomyProjectStatusEnum.published.value,
        )

    total = int(
        (
            await session.execute(select(func.count()).select_from(EconomyProject).where(where_clause))
        ).scalar_one()
    )
    rows = (
        await session.execute(
            select(EconomyProject)
            .options(*_PROJECT_LOAD_OPTIONS)
            .where(where_clause)
            .order_by(
                EconomyProject.is_platform_seed.desc(),
                EconomyProject.created_at.asc(),
                EconomyProject.slug.asc(),
            )
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()
    return list(rows), total


async def get_project_by_slug(
    session: AsyncSession,
    slug: str,
    *,
    viewer_user_id: UUID | None,
) -> EconomyProject:
    await ensure_platform_seeds(session)
    project = (
        await session.execute(
            select(EconomyProject)
            .options(*_PROJECT_LOAD_OPTIONS)
            .where(EconomyProject.slug == slug)
        )
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    is_owner = viewer_user_id is not None and project.owner_user_id == str(viewer_user_id)
    if project.status != EconomyProjectStatusEnum.published.value and not is_owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not mutations_enabled() and not project.is_platform_seed and not is_owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def create_project(session: AsyncSession, owner_user_id: UUID, body: EconomyProjectCreate) -> EconomyProject:
    require_mutations()
    if not _SLUG_RE.match(body.slug):
        raise HTTPException(status_code=400, detail="Invalid slug")
    exists = (
        await session.execute(select(EconomyProject.id).where(EconomyProject.slug == body.slug))
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Slug already in use")

    project = EconomyProject(
        id=str(uuid.uuid4()),
        owner_user_id=str(owner_user_id),
        slug=body.slug,
        title=body.title.strip(),
        summary=body.summary.strip(),
        result_promise=body.result_promise.strip(),
        earning_model=(body.earning_model or "").strip() or None,
        status=EconomyProjectStatusEnum.draft.value,
        kind=body.kind,
        seed_key=None,
        is_platform_seed=False,
        background_href=body.background_href,
        metadata_json={},
    )
    session.add(project)
    for index, task in enumerate(body.tasks):
        session.add(_task_from_create(project.id, task, default_order=index + 1))
    await session.commit()
    return await get_project_by_slug(session, project.slug, viewer_user_id=owner_user_id)


async def update_project(
    session: AsyncSession,
    project_id: UUID,
    owner_user_id: UUID,
    body: EconomyProjectUpdate,
) -> EconomyProject:
    require_mutations()
    project = await _require_owned_project(session, project_id, owner_user_id)
    if project.is_platform_seed:
        raise HTTPException(status_code=403, detail="Platform seed projects are read-only")
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(project, key, value)
    await session.commit()
    return await get_project_by_slug(session, project.slug, viewer_user_id=owner_user_id)


async def publish_project(session: AsyncSession, project_id: UUID, owner_user_id: UUID) -> EconomyProject:
    require_mutations()
    project = await _require_owned_project(session, project_id, owner_user_id)
    if project.is_platform_seed:
        raise HTTPException(status_code=403, detail="Platform seed projects are read-only")
    if not (await session.execute(select(EconomyTask.id).where(EconomyTask.project_id == str(project_id)).limit(1))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Add at least one task before publishing")
    project.status = EconomyProjectStatusEnum.published.value
    await session.commit()
    return await get_project_by_slug(session, project.slug, viewer_user_id=owner_user_id)


async def add_task(
    session: AsyncSession,
    project_id: UUID,
    owner_user_id: UUID,
    body: EconomyTaskCreate,
) -> EconomyTask:
    require_mutations()
    project = await _require_owned_project(session, project_id, owner_user_id)
    if project.is_platform_seed:
        raise HTTPException(status_code=403, detail="Platform seed projects are read-only")
    task = _task_from_create(str(project_id), body, default_order=body.stage_order)
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def apply_to_task(
    session: AsyncSession,
    task_id: UUID,
    applicant_user_id: UUID,
    body: EconomyApplicationCreate,
) -> EconomyApplication:
    require_mutations()
    task = (
        await session.execute(
            select(EconomyTask).options(selectinload(EconomyTask.project)).where(EconomyTask.id == str(task_id))
        )
    ).scalar_one_or_none()
    if task is None or task.project is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.project.status != EconomyProjectStatusEnum.published.value:
        raise HTTPException(status_code=400, detail="Project is not published")
    if task.project.is_platform_seed:
        raise HTTPException(
            status_code=403,
            detail="Platform demo projects accept no applications until community catalog opens",
        )
    if task.project.owner_user_id == str(applicant_user_id):
        raise HTTPException(status_code=400, detail="Owners cannot apply to their own tasks")

    existing = (
        await session.execute(
            select(EconomyApplication).where(
                EconomyApplication.task_id == str(task_id),
                EconomyApplication.applicant_user_id == str(applicant_user_id),
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Application already submitted")

    application = EconomyApplication(
        id=str(uuid.uuid4()),
        task_id=str(task_id),
        applicant_user_id=str(applicant_user_id),
        status=EconomyApplicationStatusEnum.pending.value,
        note=(body.note or "").strip() or None,
    )
    session.add(application)
    await session.commit()
    await session.refresh(application)
    return application


async def list_task_applications(
    session: AsyncSession,
    task_id: UUID,
    viewer_user_id: UUID,
) -> list[EconomyApplication]:
    require_mutations()
    task = (
        await session.execute(
            select(EconomyTask).options(selectinload(EconomyTask.project)).where(EconomyTask.id == str(task_id))
        )
    ).scalar_one_or_none()
    if task is None or task.project is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.project.owner_user_id != str(viewer_user_id):
        raise HTTPException(status_code=403, detail="Only the project owner can list applications")
    rows = (
        await session.execute(
            select(EconomyApplication)
            .where(EconomyApplication.task_id == str(task_id))
            .order_by(EconomyApplication.created_at.asc())
        )
    ).scalars().all()
    return list(rows)


async def _require_owned_project(session: AsyncSession, project_id: UUID, owner_user_id: UUID) -> EconomyProject:
    project = (
        await session.execute(select(EconomyProject).where(EconomyProject.id == str(project_id)))
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_user_id != str(owner_user_id):
        raise HTTPException(status_code=403, detail="Not the project owner")
    return project


def _task_from_create(project_id: str, body: EconomyTaskCreate, *, default_order: int) -> EconomyTask:
    price = body.price_acp
    if price is not None and price < 0:
        raise HTTPException(status_code=400, detail="price_acp must be non-negative")
    return EconomyTask(
        id=str(uuid.uuid4()),
        project_id=project_id,
        title=body.title.strip(),
        acceptance_criteria=body.acceptance_criteria.strip(),
        stage_order=body.stage_order if body.stage_order else default_order,
        price_acp=Decimal(str(price)) if price is not None else None,
        assignee_type=body.assignee_type,
    )
