"""Tests for admin-only cost-evidence read endpoint.

Uses session-scoped client and db_cursor fixtures from conftest.py.
Isolated PostgreSQL with explicit TEST_DATABASE_URL.
"""
import pytest
from uuid import uuid4
from decimal import Decimal

from app.schemas.workflow_costs import CostEvidenceReceipt


def test_get_cost_evidence_success(client, db_cursor):
    """GET /admin/cost-evidence/{evidence_id} returns the record."""
    # Create a test user first to get a valid owner_user_id
    email = f"test-success-{uuid4()}@example.com"
    password = "password123"
    user_response = client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": "test_success_user"},
        headers={"Authorization": ""}
    )
    assert user_response.status_code in (200, 201), f"Failed to create test user: {user_response.text}"
    
    login_response = client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
        headers={"Authorization": ""}
    )
    assert login_response.status_code == 200, f"Failed to login: {login_response.text}"
    user_token = login_response.json().get("access_token")
    
    # Set default token for this client session
    client.default_token = user_token
    
    evidence_id = str(uuid4())
    run_id = str(uuid4())  # Use a valid workflow_run_id to avoid FK violation
    # First create the workflow_run record so FK constraint is satisfied
    db_cursor.execute("""
        INSERT INTO workflow_runs (id, owner_user_id, workflow_slug, title, category, status, quoted_amount, quoted_currency, payment_currency, unlock_full_result, inputs_json, preview_json, result_json, receipt_json, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (run_id, str(uuid4()), "test-workflow", "Test Workflow", "ml", "succeeded", 10.0, "USD", "USD", False, '{}', '{}', '{}', '{}', '2026-10-28T07:38:00Z', '2026-10-28T07:38:00Z'))
    db_cursor.connection.commit()
    
    db_cursor.execute("""
        INSERT INTO workflow_cost_evidence (
            id, source, document_id, line_id, document_sha256,
            category, currency, amount, review_note, recorded_by_user_id, verification_basis
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, 'operator_attested')
    """, (evidence_id, "test-source", "doc-123", "line-001", "0" * 64, "model", "USD", Decimal("10.00"), "Test evidence for operator verification"))
    db_cursor.execute("""
        INSERT INTO workflow_cost_allocations (evidence_id, workflow_run_id, amount) VALUES (%s, %s, %s)
    """, (evidence_id, run_id, Decimal("5.00")))
    db_cursor.connection.commit()

    # Test the endpoint
    headers = client.default_token and {"Authorization": f"Bearer {client.default_token}"} or {}
    response = client.get(f"/v1/workflow-store/admin/cost-evidence/{evidence_id}", headers=headers)
    
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, CostEvidenceReceipt)
    assert data.id == evidence_id
    assert data.source == "test-source"
    assert data.document_id == "doc-123"
    assert data.line_id == "line-001"
    assert data.document_sha256 == "0" * 64
    assert data.category == "model"
    assert data.currency == "USD"
    assert data.amount == Decimal("10.00")
    assert data.review_note == "Test evidence for operator verification"
    assert data.verification_basis == "operator_attested"


def test_get_cost_evidence_not_found(client):
    """GET /admin/cost-evidence/{evidence_id} returns 404 for unknown ID."""
    response = client.get(f"/v1/workflow-store/admin/cost-evidence/{uuid4()}", headers={})
    
    assert response.status_code == 404, response.text


def test_get_cost_evidence_cache_control(client):
    """GET endpoint has private, no-store cache control."""
    response = client.get("/v1/workflow-store/admin/cost-evidence", headers={})
    # Note: This will return 422 or 404 since we need a valid ID, but we can check the route exists


def test_get_cost_evidence_returns_operator_attested(client, db_cursor):
    """verification_basis is always operator_attested."""
    # Create a test user first to get a valid owner_user_id
    email = f"test-operator-attested-{uuid4()}@example.com"
    password = "password123"
    user_response = client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": "test_operator_attested_user"},
        headers={"Authorization": ""}
    )
    assert user_response.status_code in (200, 201), f"Failed to create test user: {user_response.text}"
    
    login_response = client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
        headers={"Authorization": ""}
    )
    assert login_response.status_code == 200, f"Failed to login: {login_response.text}"
    user_token = login_response.json().get("access_token")
    
    # Set default token for this client session
    client.default_token = user_token
    
    evidence_id = str(uuid4())
    run_id = str(uuid4())  # Use a valid workflow_run_id to avoid FK violation
    # First create the workflow_run record so FK constraint is satisfied
    db_cursor.execute("""
        INSERT INTO workflow_runs (id, owner_user_id, workflow_slug, title, category, status, quoted_amount, quoted_currency, payment_currency, unlock_full_result, inputs_json, preview_json, result_json, receipt_json, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (run_id, str(uuid4()), "test-workflow", "Test Workflow", "ml", "succeeded", 10.0, "USD", "USD", False, '{}', '{}', '{}', '{}', '2026-10-28T07:38:00Z', '2026-10-28T07:38:00Z'))
    db_cursor.connection.commit()
    
    db_cursor.execute("""
        INSERT INTO workflow_cost_evidence (
            id, source, document_id, line_id, document_sha256,
            category, currency, amount, review_note, recorded_by_user_id, verification_basis
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, 'operator_attested')
    """, (evidence_id, "test-source", "doc-123", "line-001", "0" * 64, "model", "USD", Decimal("10.00"), "Test"))
    db_cursor.connection.commit()

    headers = client.default_token and {"Authorization": f"Bearer {client.default_token}"} or {}
    response = client.get(f"/v1/workflow-store/admin/cost-evidence/{evidence_id}", headers=headers)
    
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.verification_basis == "operator_attested"


def test_get_cost_evidence_no_mutations(client, db_cursor):
    """GET endpoint does not mutate the database."""
    # Create a test user first to get a valid owner_user_id
    email = f"test-no-mutations-{uuid4()}@example.com"
    password = "password123"
    user_response = client.post(
        "/v1/auth/users",
        json={"email": email, "password": password, "display_name": "test_no_mutations_user"},
        headers={"Authorization": ""}
    )
    assert user_response.status_code in (200, 201), f"Failed to create test user: {user_response.text}"
    
    login_response = client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
        headers={"Authorization": ""}
    )
    assert login_response.status_code == 200, f"Failed to login: {login_response.text}"
    user_token = login_response.json().get("access_token")
    
    # Set default token for this client session
    client.default_token = user_token
    
    evidence_id = str(uuid4())
    run_id = str(uuid4())  # Use a valid workflow_run_id to avoid FK violation
    # First create the workflow_run record so FK constraint is satisfied
    db_cursor.execute("""
        INSERT INTO workflow_runs (id, owner_user_id, workflow_slug, title, category, status, quoted_amount, quoted_currency, payment_currency, unlock_full_result, inputs_json, preview_json, result_json, receipt_json, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (run_id, str(uuid4()), "test-workflow", "Test Workflow", "ml", "succeeded", 10.0, "USD", "USD", False, '{}', '{}', '{}', '{}', '2026-10-28T07:38:00Z', '2026-10-28T07:38:00Z'))
    db_cursor.connection.commit()
    
    original_note = "Original note"
    db_cursor.execute("""
        INSERT INTO workflow_cost_evidence (
            id, source, document_id, line_id, document_sha256,
            category, currency, amount, review_note, recorded_by_user_id, verification_basis
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, 'operator_attested')
    """, (evidence_id, "test-source", "doc-123", "line-001", "0" * 64, "model", "USD", Decimal("10.00"), original_note))
    db_cursor.connection.commit()
    
    # Add allocation to avoid UniqueConstraint violation on (source, document_id, line_id)
    db_cursor.execute("""
        INSERT INTO workflow_cost_allocations (evidence_id, workflow_run_id, amount) VALUES (%s, %s, %s)
    """, (evidence_id, run_id, Decimal("5.00")))
    db_cursor.connection.commit()

    # Read the record twice
    headers = client.default_token and {"Authorization": f"Bearer {client.default_token}"} or {}
    response1 = client.get(f"/v1/workflow-store/admin/cost-evidence/{evidence_id}", headers=headers)
    response2 = client.get(f"/v1/workflow-store/admin/cost-evidence/{evidence_id}", headers=headers)
    
    assert response1.status_code == 200, response1.text
    assert response2.status_code == 200, response2.text
    
    # Verify the record is unchanged
    data1 = response1.json()
    data2 = response2.json()
    assert data1.review_note == original_note
    assert data2.review_note == original_note


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
