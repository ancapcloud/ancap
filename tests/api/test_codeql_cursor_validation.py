"""Malformed cursors must not silently broaden a paginated query."""
import pytest


@pytest.mark.parametrize("url", [
    "/v1/agents", "/v1/strategies", "/v1/funds", "/v1/contracts", "/v1/reviews", "/v1/verticals"
])
def test_invalid_cursor_is_explicit_validation_failure(client, url):
    response = client.get(url + "?cursor=not-a-uuid")
    assert response.status_code == 422, response.text
    assert response.json()["detail"] == "Invalid pagination cursor"
