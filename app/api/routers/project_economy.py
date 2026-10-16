"""People + AI project economy API (Wave 1)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, get_current_user_id, require_auth
from app.schemas.project_economy import (
    EconomyApplicationCreate,
    EconomyApplicationPublic,
    EconomyProjectCreate,
    EconomyProjectListResponse,
    EconomyProjectPublic,
    EconomyProjectUpdate,
    EconomyTaskCreate,
    EconomyTaskPublic,
)
from app.services import project_economy as svc

router = APIRouter(prefix="/economy", tags=["People AI Project Economy"])


@router.get("/projects", response_model=EconomyProjectListResponse)
async def list_economy_projects(
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
    mine: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    viewer = UUID(user_id) if user_id else None
    rows, total = await svc.list_projects(
        session,
        viewer_user_id=viewer,
        include_mine=mine,
        limit=limit,
        offset=offset,
    )
    enabled = svc.mutations_enabled()
    return EconomyProjectListResponse(
        items=[EconomyProjectPublic(**svc.project_to_public(row)) for row in rows],
        total=total,
        mutations_enabled=enabled,
        preview_only=not enabled,
    )


@router.get("/projects/{slug}", response_model=EconomyProjectPublic)
async def get_economy_project(
    slug: str,
    session: DbSession,
    user_id: str | None = Depends(get_current_user_id),
):
    viewer = UUID(user_id) if user_id else None
    project = await svc.get_project_by_slug(session, slug, viewer_user_id=viewer)
    return EconomyProjectPublic(**svc.project_to_public(project))


@router.post("/projects", response_model=EconomyProjectPublic, status_code=201)
async def create_economy_project(
    body: EconomyProjectCreate,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    project = await svc.create_project(session, UUID(user_id), body)
    return EconomyProjectPublic(**svc.project_to_public(project))


@router.patch("/projects/{project_id}", response_model=EconomyProjectPublic)
async def update_economy_project(
    project_id: UUID,
    body: EconomyProjectUpdate,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    project = await svc.update_project(session, project_id, UUID(user_id), body)
    return EconomyProjectPublic(**svc.project_to_public(project))


@router.post("/projects/{project_id}/publish", response_model=EconomyProjectPublic)
async def publish_economy_project(
    project_id: UUID,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    project = await svc.publish_project(session, project_id, UUID(user_id))
    return EconomyProjectPublic(**svc.project_to_public(project))


@router.post("/projects/{project_id}/tasks", response_model=EconomyTaskPublic, status_code=201)
async def add_economy_task(
    project_id: UUID,
    body: EconomyTaskCreate,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    task = await svc.add_task(session, project_id, UUID(user_id), body)
    return EconomyTaskPublic.model_validate(task)


@router.post("/tasks/{task_id}/applications", response_model=EconomyApplicationPublic, status_code=201)
async def apply_to_economy_task(
    task_id: UUID,
    body: EconomyApplicationCreate,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    application = await svc.apply_to_task(session, task_id, UUID(user_id), body)
    return EconomyApplicationPublic.model_validate(application)


@router.get("/tasks/{task_id}/applications", response_model=list[EconomyApplicationPublic])
async def list_economy_task_applications(
    task_id: UUID,
    session: DbSession,
    user_id: str = Depends(require_auth),
):
    rows = await svc.list_task_applications(session, task_id, UUID(user_id))
    return [EconomyApplicationPublic.model_validate(row) for row in rows]
