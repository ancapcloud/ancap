"""Admin API for ROP-05 packet templates (distinct from onboarding templates)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.deps import DbSession, require_platform_admin
from app.schemas.packet_templates import (
    PacketTemplateCreate,
    PacketTemplateListResponse,
    PacketTemplateResponse,
)
from app.services import packet_templates as templates_service

router = APIRouter(
    prefix="/packet-templates",
    tags=["packet-templates"],
    dependencies=[Depends(require_platform_admin)],
)


def _public(row) -> PacketTemplateResponse:
    return PacketTemplateResponse.model_validate(row)


@router.post(
    "",
    response_model=PacketTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_packet_template(
    body: PacketTemplateCreate,
    session: DbSession,
    response: Response,
):
    response.headers["Cache-Control"] = "private, no-store"
    row = await templates_service.create_template(
        session,
        name=body.name,
        slug=body.slug,
        description=body.description,
        source_categories=body.source_categories,
        max_sources_per_packet=body.max_sources_per_packet,
        max_snapshots_per_source=body.max_snapshots_per_source,
        max_claims_per_source=body.max_claims_per_source,
        check_cooldown_seconds=body.check_cooldown_seconds,
        retention_days=body.retention_days,
        packet_structure=body.packet_structure,
        languages=body.languages,
        status=body.status,
    )
    return _public(row)


@router.get("", response_model=PacketTemplateListResponse)
async def list_packet_templates(
    session: DbSession,
    response: Response,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    response.headers["Cache-Control"] = "private, no-store"
    rows, total = await templates_service.list_templates(
        session, status=status_filter, limit=limit, offset=offset
    )
    return PacketTemplateListResponse(templates=[_public(r) for r in rows], total=total)


@router.get("/{template_id}", response_model=PacketTemplateResponse)
async def get_packet_template(
    template_id: UUID,
    session: DbSession,
    response: Response,
):
    response.headers["Cache-Control"] = "private, no-store"
    row = await templates_service.get_template(session, template_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return _public(row)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_packet_template(
    template_id: UUID,
    session: DbSession,
    response: Response,
):
    response.headers["Cache-Control"] = "private, no-store"
    deleted = await templates_service.delete_template(session, template_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
