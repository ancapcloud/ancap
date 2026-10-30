"""WebID KYC partner slot — public schemas only; never put secrets here."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl


class WebIdAdapterStatusPublic(BaseModel):
    configured: bool = False
    enabled: bool = False
    role: str = "kyc_partner_slot"
    issues_cards: bool = False
    apple_pay_ready: bool = False
    sessions_ready: bool = False
    webhook_secret_present: bool = False
    partner_url: str = "https://webid-solutions.com/en/"
    waitlist_path: str = "/cards"
    waitlist_interest: str = "physical_card_apple_pay"
    status_path: str = "/v1/commerce/webid/status"
    session_path: str = "/v1/commerce/webid/session"
    webhook_path: str = "/v1/commerce/webid/webhook"
    docs_path: str = "docs/WEBID_KYC_AND_CARD_ISSUING_PATH.md"
    product_hint: str = "VideoID"
    notes: list[str] = Field(default_factory=list)


class WebIdSessionStartRequest(BaseModel):
    """Start a light-integration / API identification session (KYC only)."""

    return_url: Optional[HttpUrl] = None
    product: Optional[str] = Field(default=None, max_length=64)
    locale: Optional[str] = Field(default=None, max_length=16)


class WebIdSessionStartResponse(BaseModel):
    status: str = "ready"
    action_id: Optional[str] = None
    redirect_url: Optional[str] = None
    product: str = "VideoID"
    issues_cards: bool = False
    notes: list[str] = Field(default_factory=list)


class WebIdWebhookAck(BaseModel):
    status: str = "ok"
    event: Optional[str] = None
    action_id: Optional[str] = None
    identification_status: Optional[str] = None


class WebIdWebhookDebugPublic(BaseModel):
    """Operator-facing summary only — never echo secrets or raw signatures."""

    received: bool = True
    verified: bool
    event: Optional[str] = None
    meta: dict[str, Any] = Field(default_factory=dict)
