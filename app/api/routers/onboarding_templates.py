"""ROP-05: Onboarding templates admin router."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DbSession, require_platform_admin
from app.services.onboarding_templates import (
    create_template as _create_template,
    get_template_by_id as _get_template,
    list_templates as _list_templates,
    delete_template as _delete_template,
)
from app.schemas.onboarding import TemplateCreateRequest, TemplatePublic

router = APIRouter(
    prefix="/onboarding/templates",
    tags=["Onboarding Templates (ROP-05)"],
    dependencies=[Depends(require_platform_admin)],
)


async def create_onboarding_template(body: TemplateCreateRequest, session: DbSession):
    """Create a new onboarding template."""
    try:
        template = await _create_template(
            session,
            name=body.name,
            description=body.description,
            template_type=body.template_type,
            config_json=body.config_json,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TemplatePublic(
        id=str(template.id),
        name=template.name,
        description=template.description,
        template_type=template.template_type,
        config_json=template.config_json,
        created_by_user_id=str(template.created_by_user_id) if template.created_by_user_id else None,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


async def get_onboarding_template(template_id: UUID, session: DbSession):
    """Get template by ID (admin only)."""
    try:
        template = await _get_template(session, template_id=template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return TemplatePublic(
            id=str(template.id),
            name=template.name,
            description=template.description,
            template_type=template.template_type,
            config_json=template.config_json,
            created_by_user_id=str(template.created_by_user_id) if template.created_by_user_id else None,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def list_onboarding_templates(session: DbSession, template_type: str | None = None, limit: int = 100):
    """List onboarding templates (admin only)."""
    try:
        templates = await _list_templates(session, is_active=True, limit=limit)
        return [
            TemplatePublic(
                id=str(t.id),
                name=t.name,
                description=t.description,
                template_type=t.template_type,
                config_json=t.config_json,
                created_by_user_id=str(t.created_by_user_id) if t.created_by_user_id else None,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in templates
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def delete_onboarding_template(template_id: UUID, session: DbSession):
    """Delete a template (admin only)."""
    try:
        success = await _delete_template(session, template_id=template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=TemplatePublic, status_code=201)
async def create_endpoint(body: TemplateCreateRequest, session: DbSession):
    return await create_onboarding_template(body, session)


@router.get("/{template_id}", response_model=TemplatePublic)
async def get_endpoint(template_id: UUID, session: DbSession):
    return await get_onboarding_template(template_id, session)


@router.get("", response_model=list[TemplatePublic])
async def list_endpoint(session: DbSession, template_type: str | None = None, limit: int = 100):
    templates = await list_onboarding_templates(session, template_type=template_type, limit=limit)
    return templates


@router.delete("/{template_id}", status_code=204)
async def delete_endpoint(template_id: UUID, session: DbSession):
    await delete_onboarding_template(template_id, session)
