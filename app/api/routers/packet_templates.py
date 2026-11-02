"""API router for packet templates (ROP-06)."""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.packet_templates import PacketTemplatesService
from app.schemas.packet_templates import (
    PacketTemplateCreate,
    PacketTemplateUpdate,
    PacketTemplateResponse,
    PacketTemplateListResponse,
)

router = APIRouter(prefix="/packet-templates", tags=["packet-templates"])

service = PacketTemplatesService()


@router.post(
    "/",
    response_model=PacketTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new packet template",
    description="Create a reusable packet template for structured report creation.",
)
async def create_packet_template(
    request: PacketTemplateCreate,
    db: Session = Depends(get_db),
):
    """Create a new packet template."""
    try:
        template = await service.create_template(
            db=db,
            owner_user_id=request.owner_user_id if hasattr(request, 'owner_user_id') else None,
            name=request.name,
            slug=request.slug,
            description=request.description,
            source_categories=request.source_categories,
            max_sources_per_packet=request.max_sources_per_packet,
            max_snapshots_per_source=request.max_snapshots_per_source,
            max_claims_per_source=request.max_claims_per_source,
            check_cooldown_seconds=request.check_cooldown_seconds,
            retention_days=request.retention_days,
            packet_structure=request.packet_structure,
            languages=request.languages,
            status=request.status,
        )
        return template
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create packet template: {str(e)}",
        )


@router.get(
    "/{template_id}",
    response_model=PacketTemplateResponse,
    summary="Get a packet template by ID",
    description="Retrieve a specific packet template.",
)
async def get_packet_template(
    template_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a packet template by ID."""
    template = await service.get_template(db=db, template_id=template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Packet template with id {template_id} not found",
        )
    return template


@router.get(
    "/",
    response_model=PacketTemplateListResponse,
    summary="List packet templates",
    description="Retrieve all or filtered packet templates.",
)
async def list_packet_templates(
    owner_user_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List packet templates with optional filtering."""
    templates, total = await service.list_templates(
        db=db,
        owner_user_id=owner_user_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return PacketTemplateListResponse(templates=templates, total=total)


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a packet template",
    description="Delete a specific packet template.",
)
async def delete_packet_template(
    template_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a packet template."""
    success = await service.delete_template(db=db, template_id=template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Packet template with id {template_id} not found",
        )
    return None
