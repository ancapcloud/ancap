"""Tests for packet templates API (ROP-06)."""

import pytest
from uuid import uuid4
from decimal import Decimal

from app.db.session import init_db, LocalSession
from app.db.models import PacketTemplate
from app.main import app


@pytest.fixture(scope="module")
async def db_session(event_loop):
    """Create test database session."""
    from app.config import get_test_settings
    
    settings = get_test_settings()
    async with LocalSession(settings.database_url) as session:
        await init_db(session)
        yield session
        # Cleanup not needed for module-scoped tests


@pytest.mark.anyio
async def test_create_packet_template(db_session):
    """Test creating a packet template."""
    from app.services.packet_templates import PacketTemplatesService
    
    service = PacketTemplatesService()
    template = await service.create_template(
        db=db_session,
        owner_user_id=None,
        name="Test Template",
        slug="test-template",
        description="A test packet template",
        source_categories=["crypto", "news"],
        max_sources_per_packet=10,
        max_snapshots_per_source=20,
        max_claims_per_source=50,
        check_cooldown_seconds=60,
        retention_days=30,
        packet_structure={},
        languages="en",
        status="draft",
    )
    
    assert template is not None
    assert template.name == "Test Template"
    assert template.slug == "test-template"
    assert template.status == "draft"


@pytest.mark.anyio
async def test_get_packet_template(db_session):
    """Test getting a packet template by ID."""
    from app.services.packet_templates import PacketTemplatesService
    
    service = PacketTemplatesService()
    
    # Create first
    template1 = await service.create_template(
        db=db_session,
        owner_user_id=None,
        name="Get Test",
        slug="get-test",
        status="draft",
    )
    
    # Get it back
    retrieved = await service.get_template(db=db_session, template_id=template1.id)
    assert retrieved is not None
    assert retrieved.name == "Get Test"


@pytest.mark.anyio
async def test_list_packet_templates(db_session):
    """Test listing packet templates."""
    from app.services.packet_templates import PacketTemplatesService
    
    service = PacketTemplatesService()
    
    # Create some templates
    for i in range(3):
        await service.create_template(
            db=db_session,
            owner_user_id=None,
            name=f"List Test {i}",
            slug=f"list-test-{i}",
            status="draft",
        )
    
    # List them
    templates, total = await service.list_templates(db=db_session)
    assert len(templates) == 3
    assert total == 3


@pytest.mark.anyio
async def test_delete_packet_template(db_session):
    """Test deleting a packet template."""
    from app.services.packet_templates import PacketTemplatesService
    
    service = PacketTemplatesService()
    
    # Create and delete
    template = await service.create_template(
        db=db_session,
        owner_user_id=None,
        name="Delete Test",
        slug="delete-test",
        status="draft",
    )
    
    result = await service.delete_template(db=db_session, template_id=template.id)
    assert result is True
    
    # Verify deleted
    retrieved = await service.get_template(db=db_session, template_id=template.id)
    assert retrieved is None


@pytest.mark.anyio
async def test_packet_template_auth_401(client):
    """Test that unauthenticated requests to packet templates return 401."""
    response = client.post("/v1/packet-templates/", json={
        "name": "Auth Test",
        "slug": "auth-test",
    })
    assert response.status_code == 401


@pytest.mark.anyio
async def test_packet_template_404(client):
    """Test that non-existent template returns 404."""
    fake_id = uuid4()
    response = client.get(f"/v1/packet-templates/{fake_id}")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_packet_template_update(client, db_session):
    """Test updating a packet template."""
    from app.services.packet_templates import PacketTemplatesService
    
    service = PacketTemplatesService()
    
    # Create template
    template = await service.create_template(
        db=db_session,
        owner_user_id=None,
        name="Update Test",
        slug="update-test",
        status="draft",
    )
    
    # Update via router (simulated)
    response = client.patch(f"/v1/packet-templates/{template.id}", json={
        "name": "Updated Name",
        "status": "active",
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["status"] == "active"
