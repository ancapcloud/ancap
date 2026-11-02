"""ROP-05: Onboarding templates service for reuse."""
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OnboardingTemplate


async def create_template(
    session: AsyncSession,
    *,
    name: str,
    description: str | None = None,
    template_type: str,
    config_json: dict,
    created_by_user_id: UUID | None = None,
) -> OnboardingTemplate:
    """Create a new onboarding template."""
    template = OnboardingTemplate(
        name=name,
        description=description,
        template_type=template_type,
        config_json=config_json,
        created_by_user_id=created_by_user_id,
    )
    session.add(template)
    await session.flush()
    return template


async def get_template(session: AsyncSession, *, template_id: UUID) -> OnboardingTemplate | None:
    """Get template by ID."""
    result = await session.execute(select(OnboardingTemplate).where(OnboardingTemplate.id == template_id))
    return result.scalar_one_or_none()


async def list_templates(
    session: AsyncSession,
    *,
    template_type: str | None = None,
    created_by_user_id: UUID | None = None,
    limit: int = 100,
) -> list[OnboardingTemplate]:
    """List templates with optional filters."""
    query = select(OnboardingTemplate)
    if template_type:
        query = query.where(OnboardingTemplate.template_type == template_type)
    if created_by_user_id:
        query = query.where(OnboardingTemplate.created_by_user_id == created_by_user_id)
    
    result = await session.execute(query.order_by(OnboardingTemplate.created_at.desc()).limit(limit))
    return result.scalars().all()


async def delete_template(session: AsyncSession, *, template_id: UUID) -> bool:
    """Delete a template."""
    template = await get_template(session, template_id=template_id)
    if not template:
        return False
    await session.delete(template)
    await session.commit()
    return True


async def save_default_templates(session: AsyncSession) -> None:
    """Save default onboarding templates for reuse."""
    from app.db.models import OnboardingTemplate
    
    default_templates = [
        {
            "name": "Quickstart Run",
            "description": "Default quickstart workflow run template",
            "template_type": "quickstart",
            "config_json": {
                "owner_agent_id_field": True,
                "auto_create_run": True,
                "redirect_to_run_page": True,
            },
        },
        {
            "name": "ACP Faucet Claim",
            "description": "Default ACP faucet claim template",
            "template_type": "faucet",
            "config_json": {
                "currency": "ACP",
                "default_amount": 10,
                "agent_id_field": True,
            },
        },
        {
            "name": "Starter Pack Assignment",
            "description": "Default starter pack assignment template",
            "template_type": "starter-pack",
            "config_json": {
                "default_code": "default",
                "agent_id_field": True,
            },
        },
    ]
    
    for tmpl_data in default_templates:
        # Check if template with same name and type already exists
        existing = await get_template_by_name_and_type(session, name=tmpl_data["name"], template_type=tmpl_data["template_type"])
        if existing:
            continue  # Skip if already exists
        
        template = OnboardingTemplate(
            name=tmpl_data["name"],
            description=tmpl_data["description"],
            template_type=tmpl_data["template_type"],
            config_json=tmpl_data["config_json"],
            created_by_user_id=None,  # Admin-created
        )
        session.add(template)
    
    await session.flush()


async def get_template_by_name_and_type(session: AsyncSession, *, name: str, template_type: str) -> OnboardingTemplate | None:
    """Get template by name and type."""
    from app.db.models import OnboardingTemplate
    result = await session.execute(
        select(OnboardingTemplate)
        .where(OnboardingTemplate.name == name)
        .where(OnboardingTemplate.template_type == template_type)
    )
    return result.scalar_one_or_none()
