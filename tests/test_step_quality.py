"""Unit tests for step quality scorer (ROADMAP §5)."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.step_quality import compute_step_quality, get_step_quality


def test_compute_step_quality_succeeded_fast():
    assert compute_step_quality("s1", "const", "succeeded", 0, None) == 1.0  # 0.6*1 + 0.4*1


def test_compute_step_quality_succeeded_slow():
    # duration 10s -> latency 0
    assert compute_step_quality("s1", "action", "succeeded", 10_000, {}) == 0.6  # 0.6*1 + 0.4*0


def test_compute_step_quality_failed():
    # duration 100ms -> latency 0.99, outcome 0
    assert compute_step_quality("s1", "action", "failed", 100, None) == 0.396  # 0.6*0 + 0.4*0.99


def test_compute_step_quality_skipped():
    # skipped: outcome 0.5, duration None -> latency 1.0
    assert compute_step_quality("s1", "action", "skipped", None, {}) == 0.7  # 0.6*0.5 + 0.4*1


def test_compute_step_quality_negative_duration_clamped():
    # negative duration_ms should be treated as 0 (clamped to 0)
    assert compute_step_quality("s1", "action", "succeeded", -50, None) == 1.0  # 0.6*1 + 0.4*1


@pytest.mark.asyncio
async def test_get_step_quality_empty_url_uses_builtin():
    """When scorer_url is empty, get_step_quality returns built-in heuristic."""
    result = await get_step_quality("s1", "const", "succeeded", 0, None, scorer_url="", timeout_seconds=5)
    assert result == 1.0


@pytest.mark.asyncio
async def test_get_step_quality_http_returns_score():
    """When scorer_url is set and HTTP returns 200 + {score}, that score is used."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"score": 0.88}
    mock_post = AsyncMock(return_value=mock_response)
    with patch("app.services.step_quality.httpx") as m_httpx:
        m_client = AsyncMock()
        m_client.post = mock_post
        m_client.__aenter__.return_value = m_client
        m_client.__aexit__.return_value = None
        m_httpx.AsyncClient.return_value = m_client
        result = await get_step_quality(
            "s1", "a", "succeeded", 100, None, scorer_url="http://scorer/score", timeout_seconds=5
        )
    assert result == 0.88
    mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_get_step_quality_http_fallback_on_error():
    """When HTTP fails or returns invalid, fallback to built-in."""
    with patch("app.services.step_quality.httpx") as m_httpx:
        m_client = AsyncMock()
        m_client.post = AsyncMock(side_effect=Exception("timeout"))
        m_client.__aenter__.return_value = m_client
        m_client.__aexit__.return_value = None
        m_httpx.AsyncClient.return_value = m_client
        result = await get_step_quality(
            "s1", "a", "succeeded", 0, None, scorer_url="http://scorer/score", timeout_seconds=1
        )
    assert result == 1.0  # built-in for succeeded + fast
