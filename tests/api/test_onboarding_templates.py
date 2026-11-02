"""ROP-05: Onboarding templates API tests — integrated with quality_fixtures pattern.

This test file verifies that onboarding templates CRUD operations work correctly with proper auth.
"""
from uuid import uuid4

from app.config import get_settings


def setup_templates(client, monkeypatch):
    """Setup fixture user for onboarding templates tests."""
    registered = client.post("/v1/auth/users", headers={"Authorization": ""}, json={
        "email": f"onboarding_{uuid4().hex}@test.com", "password": "password123", "display_name": "Onboarding admin"})
    assert registered.status_code in (200, 201), registered.text
    headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
    user = client.get("/v1/users/me", headers=headers).json()["id"]
    monkeypatch.setattr(type(get_settings()), "platform_admin_user_ids_allowlist", property(lambda self: (user,)))
    return headers


class TestOnboardingTemplatesAuth:
    """Test onboarding templates authentication and authorization.

    These tests verify that only platform admins can access onboarding templates.
    Guest users should receive 401/403 responses.
    """

    def test_guest_cannot_list_templates(self, client):
        """Guest user cannot list templates (should return 401)."""
        response = client.get("/v1/onboarding/templates")
        assert response.status_code == 401

    def test_guest_cannot_get_template(self, client):
        """Guest user cannot get a template by ID (should return 401)."""
        response = client.get("/v1/onboarding/templates/invalid-uuid")
        assert response.status_code == 401

    def test_guest_cannot_create_template(self, client):
        """Guest user cannot create templates (should return 401)."""
        data = {
            "name": "test-template",
            "description": "Test template",
            "template_type": "quickstart",
            "config_json": {},
        }
        response = client.post("/v1/onboarding/templates", json=data)
        assert response.status_code == 401

    def test_guest_cannot_delete_template(self, client):
        """Guest user cannot delete templates (should return 401)."""
        response = client.delete("/v1/onboarding/templates/invalid-uuid")
        assert response.status_code == 401


class TestOnboardingTemplatesAdmin:
    """Integration tests for onboarding templates with admin access."""

    def test_admin_can_list_templates(self, client, monkeypatch):
        """Admin user can list templates."""
        headers = setup_templates(client, monkeypatch)
        response = client.get("/v1/onboarding/templates", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data or "total" in data

    def test_admin_can_get_template(self, client, monkeypatch):
        """Admin user can get a template by ID."""
        headers = setup_templates(client, monkeypatch)
        # Create a template first
        create_data = {
            "name": "Test Template",
            "description": "Test description",
            "template_type": "quickstart",
            "config_json": {"test": True},
        }
        created = client.post("/v1/onboarding/templates", json=create_data, headers=headers)
        assert created.status_code == 201, created.text
        template_id = created.json()["id"]
        
        # Now retrieve it
        retrieved = client.get(f"/v1/onboarding/templates/{template_id}", headers=headers)
        assert retrieved.status_code == 200, retrieved.text
        data = retrieved.json()
        assert data["name"] == "Test Template"
        assert data["template_type"] == "quickstart"

    def test_admin_can_create_template(self, client, monkeypatch):
        """Admin user can create a template."""
        headers = setup_templates(client, monkeypatch)
        create_data = {
            "name": "Quickstart Run",
            "description": "Default quickstart workflow run template",
            "template_type": "quickstart",
            "config_json": {
                "owner_agent_id_field": True,
                "auto_create_run": True,
                "redirect_to_run_page": True,
            },
        }
        response = client.post("/v1/onboarding/templates", json=create_data, headers=headers)
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["name"] == "Quickstart Run"
        assert data["template_type"] == "quickstart"

    def test_admin_can_delete_template(self, client, monkeypatch):
        """Admin user can delete a template."""
        headers = setup_templates(client, monkeypatch)
        # Create a template first
        create_data = {
            "name": "To Be Deleted",
            "description": "This will be deleted",
            "template_type": "faucet",
            "config_json": {"currency": "ACP"},
        }
        created = client.post("/v1/onboarding/templates", json=create_data, headers=headers)
        assert created.status_code == 201, created.text
        template_id = created.json()["id"]
        
        # Delete it
        deleted = client.delete(f"/v1/onboarding/templates/{template_id}", headers=headers)
        assert deleted.status_code == 204

    def test_admin_can_list_templates_by_type(self, client, monkeypatch):
        """Admin user can list templates filtered by type."""
        headers = setup_templates(client, monkeypatch)
        # Create a faucet template
        create_data = {
            "name": "ACP Faucet Claim",
            "description": "Default ACP faucet claim template",
            "template_type": "faucet",
            "config_json": {"currency": "ACP"},
        }
        client.post("/v1/onboarding/templates", json=create_data, headers=headers)
        
        # List only faucet templates
        response = client.get("/v1/onboarding/templates?template_type=faucet", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["templates"]) >= 1
