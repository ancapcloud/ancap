"""Pydantic schemas for Research Operations quality fixtures (ROP-03)."""

from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import UUID
import secrets

from pydantic import BaseModel, Field


class EvaluationFixture(BaseModel):
    """De-identified evaluation fixture for quality testing."""
    fixture_id: str = Field(default_factory=lambda: f"fix-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)[:8]}")
    source_type: Literal["price_change", "product_change", "markup_noise", "unavailable_source", "contradiction", "malicious_embedded"]
    fixture_name: str
    description: str
    expected_error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    test_case: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PriceChangeFixture(EvaluationFixture):
    """Fixture for price/product change detection."""
    original_price: float
    new_price: float
    product_name: str
    expected_detection: bool = True


class MarkupNoiseFixture(EvaluationFixture):
    """Fixture with markup noise in source HTML."""
    noise_type: Literal["script_injection", "css_override", "meta_tag_conflict", "unicode_zero_width"]
    noise_location: str
    expected_parsing_error: Optional[str] = None


class UnavailableSourceFixture(EvaluationFixture):
    """Fixture simulating unavailable source."""
    unavailability_reason: Literal["dns_failure", "ssl_error", "timeout", "403_forbidden", "410_gone"]
    retry_after_seconds: Optional[int] = None


class ContradictionFixture(EvaluationFixture):
    """Fixture with contradictory information in source."""
    claim_a: str
    claim_b: str
    expected_resolution: Literal["claim_a_wins", "claim_b_wins", "human_review_required"]


class MaliciousEmbeddedFixture(EvaluationFixture):
    """Fixture with embedded malicious instructions."""
    instruction_type: Literal["prompt_injection", "data_exfiltration", "credential_harvesting"]
    detection_method: str
