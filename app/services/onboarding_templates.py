"""ROP-05: Onboarding templates service."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import OnboardingTemplate

# Default templates for ROP-05
DEFAULT_TEMPLATES = [
    {
        "name": "Crypto Client Onboarding",
        "description": "Template for crypto-focused clients with news and social sources",
        "template_type": "crypto",
        "source_categories": ["news", "social", "official"],
        "packet_template": {
            "sections": ["market_summary", "price_alerts", "social_sentiment"],
            "frequency_hours": 6,
            "max_sources": 10
        },
        "config_json": {
            "model_params": {"temperature": 0.7, "max_tokens": 500},
            "prompts": {
                "market_summary": "Summarize crypto market movements...",
                "price_alerts": "Alert on significant price changes..."
            }
        },
        "validation_config": {
            "min_sources": 3,
            "max_age_hours": 24,
            "confidence_threshold": 0.7
        }
    },
    {
        "name": "Social Media Monitoring",
        "description": "Template for social media sentiment analysis",
        "template_type": "social",
        "source_categories": ["twitter", "telegram", "reddit"],
        "packet_template": {
            "sections": ["trending_topics", "sentiment_analysis", "viral_content"],
            "frequency_hours": 3,
            "max_sources": 20
        },
        "config_json": {
            "model_params": {"temperature": 0.8, "max_tokens": 400},
            "prompts": {
                "sentiment_analysis": "Analyze sentiment of social posts..."
            }
        },
        "validation_config": {
            "min_sources": 5,
            "max_age_hours": 12,
            "confidence_threshold": 0.6
        }
    },
    {
        "name": "News Aggregation",
        "description": "Template for news aggregation and verification",
        "template_type": "news",
        "source_categories": ["official", "news", "press"],
        "packet_template": {
            "sections": ["breaking_news", "verified_stories", "editorial_summary"],
            "frequency_hours": 1,
            "max_sources": 15
        },
        "config_json": {
            "model_params": {"temperature": 0.3, "max_tokens": 600},
            "prompts": {
                "breaking_news": "Identify and summarize breaking news..."
            }
        },
        "validation_config": {
            "min_sources": 2,
            "max_age_hours": 48,
            "confidence_threshold": 0.8
        }
    }
]


async def get_template_by_id(db: AsyncSession, template_id: str) -> Optional[OnboardingTemplate]:
    """Get onboarding template by ID."""
    return await db.get(OnboardingTemplate, template_id)


async def list_templates(db: AsyncSession, owner_user_id: Optional[str] = None, is_active: bool = True, limit: int = 100) -> List[OnboardingTemplate]:
    """List onboarding templates with optional filtering."""
    query = db.query(OnboardingTemplate)
    
    if owner_user_id:
        query = query.filter(OnboardingTemplate.created_by_user_id == owner_user_id)
    if is_active:
        query = query.filter(OnboardingTemplate.is_active == True)
    
    results = await query.order_by(OnboardingTemplate.created_at.desc()).limit(limit).all()
    return results


async def create_template(db: AsyncSession, name: str, description: Optional[str] = None, 
                          template_type: str = "general", config_json: Optional[dict] = None,
                          source_categories: Optional[list] = None, packet_template: Optional[dict] = None,
                          validation_config: Optional[dict] = None) -> OnboardingTemplate:
    """Create a new onboarding template."""
    template = OnboardingTemplate(
        name=name,
        description=description,
        template_type=template_type,
        config_json=config_json,
        source_categories=source_categories,
        packet_template=packet_template,
        validation_config=validation_config,
        created_by_user_id=None  # Admin creates templates
    )
    db.add(template)
    await db.commit()
    return template


async def update_template(db: AsyncSession, template_id: str, **kwargs) -> Optional[OnboardingTemplate]:
    """Update an existing onboarding template."""
    template = await get_template_by_id(db, template_id)
    if not template:
        return None
    
    for key, value in kwargs.items():
        if hasattr(template, key):
            setattr(template, key, value)
    
    await db.commit()
    return template


async def delete_template(db: AsyncSession, template_id: str) -> bool:
    """Delete an onboarding template."""
    template = await get_template_by_id(db, template_id)
    if not template:
        return False
    
    await db.delete(template)
    await db.commit()
    return True


async def import_default_templates(db: AsyncSession) -> List[OnboardingTemplate]:
    """Import default templates for ROP-05."""
    existing_names = {str(t.name) for t in await list_templates(db, is_active=True)}
    
    for template_data in DEFAULT_TEMPLATES:
        if template_data["name"] not in existing_names:
            template = OnboardingTemplate(
                name=template_data["name"],
                description=template_data["description"],
                template_type=template_data["template_type"],
                config_json=template_data.get("config_json"),
                source_categories=template_data.get("source_categories"),
                packet_template=template_data.get("packet_template"),
                validation_config=template_data.get("validation_config")
            )
            db.add(template)
    
    await db.commit()
    return await list_templates(db, is_active=True)
