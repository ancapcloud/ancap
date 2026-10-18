from __future__ import annotations

from pydantic import BaseModel, Field


class PaymentScannerParseRequest(BaseModel):
    raw_text: str = Field(min_length=1, max_length=8000)
    source: str = Field(default="paste", pattern="^(paste|qr|ocr)$")


class PaymentScannerPreview(BaseModel):
    detected_network: str | None
    address: str | None
    amount: str | None
    currency: str | None
    label: str | None
    confidence: float
    requires_manual_confirm: bool = True
    parse_notes: list[str]
    recommendations: list[str] = Field(default_factory=list)
    can_pay_acp: bool = False
