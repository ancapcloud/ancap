from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.common import Money
from app.schemas.settlements import ChainReceiptPublic, SettlementIntentPublic


class WorkflowTemplatePublic(BaseModel):
    slug: str
    title: str
    category: str
    summary: str
    description: str
    price: Money
    accepted_currencies: list[str] = Field(default_factory=list)
    estimated_time_minutes: int
    preview_items: list[str] = Field(default_factory=list)
    output_items: list[str] = Field(default_factory=list)
    receipt_items: list[str] = Field(default_factory=list)
    status: str = "active"
    tags: list[str] = Field(default_factory=list)
    billing: str = "one_shot"
    subscription_price_monthly: Optional[Money] = None
    subscription_price_quarterly: Optional[Money] = None
    subscription_price_annual: Optional[Money] = None
    # Market-aligned retail face (USD) + live ACP checkout amount when enriched.
    usd_sticker: Optional[Money] = None  # Historical responses only.
    eur_sticker: Optional[Money] = None
    price_acp: Optional[Money] = None
    oracle_wacp_usd: Optional[str] = None
    # Phase 4: AI system card for governance workflows
    ai_system_card: Optional[dict[str, Any]] = Field(
        default=None,
        description="AI system card metadata for premium governance workflows: capability, supplier controls, audit evidence, corrective-action plan.",
    )


class WorkflowTemplatesResponse(BaseModel):
    items: list[WorkflowTemplatePublic]


class WorkflowBundlePublic(BaseModel):
    slug: str
    title: str
    category: str
    summary: str
    description: str
    workflow_slugs: list[str] = Field(default_factory=list)
    price: Money
    accepted_currencies: list[str] = Field(default_factory=list)
    discount_percent: int = 0
    estimated_time_minutes: int
    output_items: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    usd_sticker: Optional[Money] = None  # Historical responses only.
    eur_sticker: Optional[Money] = None
    price_acp: Optional[Money] = None
    oracle_wacp_usd: Optional[str] = None


class WorkflowBundlesResponse(BaseModel):
    items: list[WorkflowBundlePublic]


class WorkflowRunStatus(str, Enum):
    quoted = "quoted"
    paid = "paid"
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class WorkflowRunCreateRequest(BaseModel):
    workflow_slug: str
    payment_currency: str = "ACP"
    unlock_full_result: bool = True
    inputs: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunStatusUpdateRequest(BaseModel):
    status: WorkflowRunStatus


class WorkflowRunPaymentConfirmRequest(BaseModel):
    payment_reference: str = Field(..., min_length=3, max_length=128)
    payment_method: str = Field(default="manual")
    payment_amount: Optional[Money] = None
    note: Optional[str] = Field(default=None, max_length=500)


class WorkflowRunPaymentIntentCreateRequest(BaseModel):
    payment_method: str = Field(default="credits", min_length=3, max_length=64)
    payment_reference: Optional[str] = Field(default=None, max_length=128)
    note: Optional[str] = Field(default=None, max_length=500)


class WorkflowBundleCheckoutRequest(BaseModel):
    payment_currency: str = "ACP"
    payment_method: str = Field(default="credits", min_length=3, max_length=64)
    project_name: Optional[str] = Field(default=None, max_length=120)
    unlock_full_result: bool = True
    reserve_credits: bool = True
    inputs_by_workflow: dict[str, dict[str, Any]] = Field(default_factory=dict)
    note: Optional[str] = Field(default=None, max_length=500)


class WorkflowRunPaymentIntentPublic(BaseModel):
    id: str
    workflow_run_id: Optional[str] = None
    owner_user_id: str
    intent_type: str
    status: str
    payment_method: str
    amount: Money
    payment_reference: Optional[str] = None
    reserved_ledger_event_id: Optional[str] = None
    capture_ledger_event_id: Optional[str] = None
    refund_ledger_event_id: Optional[str] = None
    provider_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class WorkflowRunReceiptPublic(BaseModel):
    workflow_slug: str
    payment_currency: str
    quoted_price: Money
    status: str
    receipt_items: list[str] = Field(default_factory=list)
    proof: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunPublic(BaseModel):
    result_hash: Optional[str] = None
    id: str
    workflow_slug: str
    title: str
    category: str
    status: WorkflowRunStatus
    price: Money
    payment_currency: str
    unlock_full_result: bool
    inputs: dict[str, Any] = Field(default_factory=dict)
    preview: dict[str, Any] = Field(default_factory=dict)
    result: Optional[dict[str, Any]] = None
    receipt: WorkflowRunReceiptPublic
    created_at: datetime
    owner_user_id: Optional[str] = None
    # Phase 4: degraded run signal — present when LLM call failed and template fallback was used
    degraded_run: bool = False
    degraded_reason: Optional[str] = None


class WorkflowRunPaymentIntentCreateResponse(BaseModel):
    item: WorkflowRunPaymentIntentPublic
    run: WorkflowRunPublic
    reserved: bool = False


class WorkflowBundleCheckoutResponse(BaseModel):
    bundle: WorkflowBundlePublic
    bundle_checkout_id: str
    payment_currency: str
    quoted_total: Money
    original_total: Money
    discount_amount: Money
    reserved: bool
    runs: list[WorkflowRunPublic] = Field(default_factory=list)
    payment_intents: list[WorkflowRunPaymentIntentPublic] = Field(default_factory=list)


class WorkflowCreditPackagePublic(BaseModel):
    fiat_price: Optional[Money] = None
    pricing_version: str = "credit-packages-v1"
    slug: str
    title: str
    description: str
    price: Money
    credit_amount: Money
    accepted_currencies: list[str] = Field(default_factory=list)
    bonus_percent: int = 0
    recommended_for: list[str] = Field(default_factory=list)


class CreditTopUpPricingSnapshot(BaseModel):
    schema_version: Literal[1] = 1
    package: WorkflowCreditPackagePublic
    payment_amount: Money


class WorkflowCreditPackagesResponse(BaseModel):
    items: list[WorkflowCreditPackagePublic]


class WorkflowCreditTopUpIntentCreateRequest(BaseModel):
    payment_currency: str = "ACP"
    payment_method: str = Field(default="manual", min_length=3, max_length=64)
    note: Optional[str] = Field(default=None, max_length=500)


class WorkflowCreditTopUpIntentConfirmRequest(BaseModel):
    payment_reference: str = Field(..., min_length=3, max_length=128)
    note: Optional[str] = Field(default=None, max_length=500)


class WorkflowCreditTopUpIntentResponse(BaseModel):
    item: WorkflowRunPaymentIntentPublic
    package: WorkflowCreditPackagePublic
    credited: bool = False


class WorkflowCreditTopUpIntentsResponse(BaseModel):
    items: list[WorkflowCreditTopUpIntentResponse] = Field(default_factory=list)


class WorkflowRevenueCurrencyTotalPublic(BaseModel):
    currency: str
    status: str
    amount: str
    count: int


class WorkflowRevenueMoneyPublic(BaseModel):
    currency: str
    amount: str


class WorkflowRevenueSkuPublic(BaseModel):
    workflow_slug: str
    title: str
    category: str
    currency: str
    quote_count: int = 0
    payment_intent_count: int = 0
    requires_payment_count: int = 0
    reserved_count: int = 0
    captured_count: int = 0
    refunded_count: int = 0
    failed_count: int = 0
    cancelled_count: int = 0
    open_reserved_amount: str = "0"
    captured_amount: str = "0"
    refunded_amount: str = "0"
    estimated_cost_amount: str = "0"
    estimated_margin_amount: str = "0"
    referral_commission_amount: str = "0"


class WorkflowRevenueSummaryPublic(BaseModel):
    generated_at: datetime
    since: datetime
    window_days: int
    quote_count: int
    run_status_counts: dict[str, int] = Field(default_factory=dict)
    payment_status_counts: dict[str, int] = Field(default_factory=dict)
    totals: list[WorkflowRevenueCurrencyTotalPublic] = Field(default_factory=list)
    skus: list[WorkflowRevenueSkuPublic] = Field(default_factory=list)
    gross_captured_totals: list[WorkflowRevenueMoneyPublic] = Field(default_factory=list)
    estimated_cost_totals: list[WorkflowRevenueMoneyPublic] = Field(default_factory=list)
    estimated_margin_totals: list[WorkflowRevenueMoneyPublic] = Field(default_factory=list)
    referral_commission_totals: list[WorkflowRevenueMoneyPublic] = Field(default_factory=list)


class WorkflowRunsResponse(BaseModel):
    items: list[WorkflowRunPublic]


class WorkflowRunStatusUpdateResponse(BaseModel):
    item: WorkflowRunPublic
    previous_status: WorkflowRunStatus


class WorkflowRunExecuteResponse(BaseModel):
    item: WorkflowRunPublic
    execution_mode: str = "template_stub"


class WorkflowRunPaymentConfirmResponse(BaseModel):
    item: WorkflowRunPublic
    previous_status: WorkflowRunStatus
    payment_confirmed: bool = True


class WorkflowRunReceiptTrailPublic(BaseModel):
    workflow_run_id: str
    settlement_intent: Optional[SettlementIntentPublic] = None
    chain_receipts: list[ChainReceiptPublic] = Field(default_factory=list)


class WorkflowRunProofBundleSummaryPublic(BaseModel):
    payment_confirmed: bool = False
    settlement_status: Optional[str] = None
    chain_receipt_count: int = 0
    finalized_receipt_count: int = 0
    failed_receipt_count: int = 0
    submitted_receipt_count: int = 0
    execution_mode: Optional[str] = None
    executed_at: Optional[datetime] = None
    latest_chain_receipt_status: Optional[str] = None


class WorkflowRunProofBundlePublic(BaseModel):
    bundle_version: str = "workflow-run-proof-bundle/v1"
    generated_at: datetime
    workflow_run_id: str
    proof_hash: str
    run: WorkflowRunPublic
    receipt_items: list[str] = Field(default_factory=list)
    payment_confirmation: Optional[dict[str, Any]] = None
    execution: dict[str, Any] = Field(default_factory=dict)
    settlement_intent: Optional[SettlementIntentPublic] = None
    chain_receipts: list[ChainReceiptPublic] = Field(default_factory=list)
    status_timeline: list[dict[str, Any]] = Field(default_factory=list)
    summary: WorkflowRunProofBundleSummaryPublic
