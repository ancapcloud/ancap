"""Bounded, project-scoped Research Operations requests."""
from typing import Literal, Optional
from uuid import UUID
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.services.webhook_url_policy import validate_webhook_url


class PriceChangeFixture(BaseModel):
    """Fixture for price change detection testing."""
    fixture_id: str = Field(..., pattern=r"^[a-f0-9-]+$")
    source_type: Literal["price_change"]
    fixture_name: str
    description: str
    original_price: float
    new_price: float
    product_name: str
    expected_detection: bool


class MarkupNoiseFixture(BaseModel):
    """Fixture for markup noise testing."""
    fixture_id: str = Field(..., pattern=r"^[a-f0-9-]+$")
    source_type: Literal["markup_noise"]
    fixture_name: str
    description: str
    noise_type: str
    noise_location: str
    expected_parsing_error: Optional[str] = None


class UnavailableSourceFixture(BaseModel):
    """Fixture for unavailable source testing."""
    fixture_id: str = Field(..., pattern=r"^[a-f0-9-]+$")
    source_type: Literal["unavailable_source"]
    fixture_name: str
    description: str
    unavailability_reason: str
    retry_after_seconds: Optional[int] = None


class ContradictionFixture(BaseModel):
    """Fixture for contradiction resolution testing."""
    fixture_id: str = Field(..., pattern=r"^[a-f0-9-]+$")
    source_type: Literal["contradiction"]
    fixture_name: str
    description: str
    claim_a: str
    claim_b: str
    expected_resolution: Literal["human_review_required", "claim_a_wins", "claim_b_wins"]


class MaliciousEmbeddedFixture(BaseModel):
    """Fixture for malicious embedded content testing."""
    fixture_id: str = Field(..., pattern=r"^[a-f0-9-]+$")
    source_type: Literal["malicious_embedded"]
    fixture_name: str
    description: str
    instruction_type: str
    detection_method: str


class SourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=120)
    url: str = Field(max_length=2048)
    permission_basis: str = Field(min_length=10, max_length=500)

    @field_validator("url")
    @classmethod
    def public_https(cls, value):
        target = validate_webhook_url(value, resolve_dns=False)
        parsed = urlsplit(value)
        if target.scheme != "https" or target.port != 443 or parsed.fragment or parsed.query:
            raise ValueError("Use a public HTTPS page on port 443 without query or fragment")
        return target.url

    @field_validator("title", "permission_basis")
    @classmethod
    def nonblank(cls, value, info):
        value = value.strip()
        if not value or (info.field_name == "permission_basis" and len(value) < 10):
            raise ValueError("A nonblank value is required")
        return value


class ClaimCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: UUID
    source_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    statement: str = Field(min_length=1, max_length=1000)
    excerpt: str = Field(min_length=1, max_length=500)
    verdict: Literal["supported_by_source", "contradiction", "unconfirmed"]

    @field_validator("statement", "excerpt")
    @classmethod
    def nonblank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("A nonblank value is required")
        return value


class PacketCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID
    source_ids: list[UUID] = Field(min_length=1, max_length=10)
    expected_review_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def unique_sources(self):
        if len(set(self.source_ids)) != len(self.source_ids):
            raise ValueError("Duplicate source ID")
        return self
