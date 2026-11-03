from uuid import uuid4
from tests.api.test_workflow_cost_evidence_api import setup_costs


def test_quality_routes_await_database_and_keep_operator_data_private(client, monkeypatch, db_cursor):
    headers, _, _ = setup_costs(client, monkeypatch)
    fixture_id = str(uuid4())
    db_cursor.execute("INSERT INTO quality_fixtures (id,fixture_type,language,sample_id,expected_result,is_available) VALUES (%s,%s,%s,%s,%s,%s)",
                      (fixture_id, 'price_change', 'en', uuid4().hex, 'Synthetic expected result', True))
    db_cursor.connection.commit()
    url = '/v1/quality-fixtures/'
    assert client.get(url, headers={'Authorization':''}).status_code == 401
    assert client.get(url).status_code == 403
    response = client.get(url+'?limit=1', headers=headers)
    assert response.status_code == 200, response.text
    assert response.headers['cache-control'] == 'private, no-store'
    assert response.json()['total'] >= 1
    assert len(response.json()['fixtures']) == 1
    item = client.get(url+fixture_id, headers=headers)
    assert item.status_code == 200, item.text
    assert item.json()['expected_result'] == 'Synthetic expected result'
    assert client.get(url+str(uuid4()), headers=headers).status_code == 404
    assert client.get(url+'not-a-uuid', headers=headers).status_code == 422
    assert client.get(url+'?limit=100000', headers=headers).status_code == 422
    assert client.get(url+'?offset=-1', headers=headers).status_code == 422


def test_cost_evidence_canonical_get_is_unique(client, monkeypatch, db_cursor):
    """COST-03: only GET /admin/cost-evidence/{id} may serve the record."""
    headers, _, body = setup_costs(client, monkeypatch)
    body.update(
        provider_id="synthetic-provider",
        document_type="invoice",
        external_payment_event=True,
        delivery_event=True,
    )
    saved = client.post("/v1/workflow-store/admin/cost-evidence", json=body, headers=headers)
    assert saved.status_code == 201, saved.text
    evidence_id = saved.json()["id"]

    db_cursor.execute(
        "SELECT document_sha256, review_note FROM workflow_cost_evidence WHERE id=%s",
        (evidence_id,),
    )
    before = db_cursor.fetchone()

    canonical = client.get(
        f"/v1/workflow-store/admin/cost-evidence/{evidence_id}", headers=headers
    )
    assert canonical.status_code == 200, canonical.text
    payload = canonical.json()
    assert payload["verification_basis"] == "operator_attested"
    assert payload["provider_id"] == "synthetic-provider"
    assert payload["external_payment_event"] is True
    assert payload["delivery_event"] is True
    assert payload["source"] == body["source"]
    assert payload["document_sha256"] == body["document_sha256"]
    assert payload["review_note"] == body["review_note"]
    assert len(payload["allocations"]) == 1
    assert canonical.headers["cache-control"] == "private, no-store"

    # Non-canonical alias must not remain registered beside the admin path.
    assert (
        client.get(f"/v1/workflow-store/cost-evidence/{evidence_id}", headers=headers).status_code
        == 404
    )
    assert client.get(
        f"/v1/workflow-store/admin/cost-evidence/{evidence_id}",
        headers={"Authorization": ""},
    ).status_code == 401
    assert client.get(f"/v1/workflow-store/admin/cost-evidence/{evidence_id}").status_code == 403

    db_cursor.execute(
        "SELECT document_sha256, review_note FROM workflow_cost_evidence WHERE id=%s",
        (evidence_id,),
    )
    after = db_cursor.fetchone()
    assert after == before
