"""API key schemas."""
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ApiKeyCreateRequest(BaseModel):
    """Request to create an API key for an agent."""
    agent_id: str = Field(..., description="Agent ID that will own the key")
    scope: Optional[str] = Field(None, max_length=64, description="Optional scope (e.g. read, write)")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration time")


class ApiKeyCreateResponse(BaseModel):
    """Response when creating a key: raw key is returned once; store it securely."""
    id: str
    agent_id: str
    key_prefix: str = Field(..., description="First chars of the key for identification; use in X-API-Key for auth")
    key: str = Field(..., description="Full API key; shown only once, store securely")
    scope: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class ApiKeyPublic(BaseModel):
    """Public key info (no secret)."""
    id: str
    agent_id: str
    org_id: Optional[str] = None
    key_prefix: str
    scope: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class AccountApiKeyPublic(BaseModel):
    active: bool
    key_prefix: str | None = None
    created_at: datetime | None = None
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None
    requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0


class AccountApiKeyCreated(AccountApiKeyPublic):
    key: str


# --- Org-scoped API key schemas ---

class OrgApiKeyCreateRequest(BaseModel):
    """Create an API key owned by the organization (no agent required)."""
    name: str = Field(..., max_length=80, description="Descriptive name for this key")
    scope: Optional[str] = Field(None, max_length=64)
    expires_at: Optional[datetime] = None


class OrgApiKeySpendCapRequest(BaseModel):
    endpoint: str = Field(..., min_length=1, max_length=160)
    currency: str = Field(..., min_length=1, max_length=10)
    monthly_cap: str = Field(..., min_length=1, max_length=64)

    @field_validator("endpoint")
    @classmethod
    def normalize_endpoint(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized.startswith("/"):
            raise ValueError("endpoint must start with '/'")
        return normalized

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("currency is required")
        return normalized

    @field_validator("monthly_cap")
    @classmethod
    def validate_monthly_cap(cls, value: str) -> str:
        normalized = value.strip()
        try:
            if Decimal(normalized) <= 0:
                raise ValueError("monthly_cap must be positive")
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("monthly_cap must be a positive decimal string") from exc
        return normalized


class OrgApiKeyPublic(BaseModel):
    id: str
    org_id: str
    name: str
    key_prefix: str
    scope: Optional[str] = None
    spend_caps: dict[str, dict[str, str]] = Field(default_factory=dict)
    expires_at: Optional[datetime] = None
    created_at: datetime
