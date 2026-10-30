"""Pydantic models for wACP clearing rail API."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BridgeIntentAcpToBscCreate(BaseModel):
    user_bsc_address: str = Field(..., min_length=42, max_length=66)
    amount_acp: str = Field(..., description="Decimal ACP amount, e.g. 1.25")
    user_acp_address: str | None = Field(None, max_length=128)


class BridgeIntentBscToAcpCreate(BaseModel):
    user_bsc_address: str = Field(..., min_length=42, max_length=66)
    user_acp_address: str = Field(..., min_length=3, max_length=128)
    amount_wacp: str = Field(..., description="Decimal wACP amount in 18-decimal token units, e.g. 1 or 1.5")


class BridgeRedeemQuoteRequest(BaseModel):
    amount_wacp: str = Field(..., description="Decimal wACP amount in 18-decimal token units")


class BridgeRedeemQuoteResponse(BaseModel):
    amount_wacp: str
    amount_wacp_wei: str
    acp_amount_floor: str
    acp_smallest_floor: str
    remainder_wacp_wei: str
    remainder_wacp: str
    policy: str


class BridgeOperationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    direction: str
    status: str
    user_bsc_address: str | None
    user_acp_address: str | None
    amount_acp_smallest: str
    amount_wacp_wei: str
    remainder_wacp_wei: str = "0"
    acp_tx_hash: str | None = None
    bsc_tx_hash_mint: str | None = None
    bsc_tx_hash_burn: str | None = None
    deposit_ref_hex: str | None = None
    bsc_log_index: int | None = None
    version: int | None = None
    created_at: datetime | None


class BridgeStatusResponse(BaseModel):
    new_wacp_intents_allowed: bool = False
    bridge_rail_enabled: bool
    bridge_rail_paused: bool
    dry_run: bool
    wacp_contract: str
    gateway_contract: str
    reserve_acp_address: str
    confirmations_acp: int
    confirmations_bsc: int
    bsc_explorer_base: str
    acp_explorer_tx_base: str
    counts_by_status: dict[str, int]
    checkpoint_acp: int | None
    checkpoint_bsc: int | None
    checkpoint_acp_deposit: int | None = None
    last_reconciliation: dict[str, Any] | None = None


class BridgeReserveSummaryResponse(BaseModel):
    total_acp_smallest_locked_intent: str
    total_wacp_wei_completed_mints: str
    # Human-readable displays (ACP 8dp / wACP 18dp) for UI — raw fields kept for machines.
    total_acp_display: str = "0"
    total_wacp_display: str = "0"
    wacp_per_acp: int = 10
    ops_note: str = (
        "DB ledger of bridge forward ops only. Pre-cutover wraps may be 1:1; "
        "treasury/Gate A mints appear in on-chain supply (reserve-proof), not here."
    )
    operations_pending: int
    operations_completed: int


class BridgeSnapshotResponse(BaseModel):
    id: str
    snapshot_at: datetime
    reserve_balance_acp_smallest: int
    total_wacp_wei_completed: str
    total_wacp_wei_implied: str
    backing_ratio: float | None
    delta_wacp_wei: str
    reconciliation_ok: bool
    status: str
    reserve_health: str
    notes: list[str]
    last_acp_block_height: int | None
    last_bsc_block_number: int | None


class BridgeAlertsResponse(BaseModel):
    stale_snapshot: dict | None = None
    reconciliation_mismatch: dict | None = None


class WacpReserveProofResponse(BaseModel):
    status: str
    bridge_enabled: bool
    bridge_paused: bool
    acp_reserve_address: str
    acp_reserve_balance_smallest: str
    wacp_contract: str
    wacp_total_supply_wei: str
    wacp_total_supply_acp_smallest: str
    operational_buffer_smallest: str
    backing_ratio: str | None = None
    reserve_health: str
    last_acp_block_height: int | None = None
    last_bsc_block_number: int | None = None
    last_updated_at: datetime | None = None
    notes: list[str] = Field(default_factory=list)
    max_additional_mint_acp_smallest: str | None = None
    mint_envelope_notes: list[str] = Field(default_factory=list)


class WacpPublicStatusResponse(BaseModel):
    status: str
    bridge_enabled: bool
    bridge_paused: bool
    mint_available: bool
    redeem_available: bool
    redeem_mode: str = "disabled"
    reserve_proof_status: str
    reserve_health: str
    wacp_contract: str
    gateway_contract: str
    reserve_acp_address: str
    confirmations_acp: int
    confirmations_bsc: int
    bsc_explorer_base: str
    acp_explorer_tx_base: str
    checkpoint_acp: int | None = None
    checkpoint_bsc: int | None = None
    last_updated_at: datetime | None = None
    pair_live: bool = False
    pair_dex: str | None = None
    pair_symbol: str | None = None
    pair_address: str | None = None
    pair_url: str | None = None
    swap_url: str | None = None
    liquidity_tx_hash: str | None = None
    first_swap_buy_tx_hash: str | None = None
    first_swap_sell_tx_hash: str | None = None
    bsc_contract_verified: bool = False
    token_metadata_live: bool = False
    docs: dict[str, str]
    counts_by_status: dict[str, int]
    notes: list[str] = Field(default_factory=list)


class BridgeAllowlistAddRequest(BaseModel):
    bsc_address: str = Field(..., min_length=42, max_length=66)
    note: str | None = None


class BridgeAdminReverseBindBurnRequest(BaseModel):
    operation_id: str
    bsc_tx_hash_burn: str = Field(..., min_length=3, max_length=128)
    bsc_log_index: int = Field(..., ge=0)
    correlation_id: str | None = Field(None, max_length=128)
    note: str | None = None


class BridgeAdminReverseBindPayoutRequest(BaseModel):
    operation_id: str
    acp_tx_hash: str = Field(..., min_length=3, max_length=128)
    note: str | None = None


class BridgeAdminForwardBindDepositRequest(BaseModel):
    operation_id: str
    acp_tx_hash: str = Field(..., min_length=3, max_length=128)
    note: str | None = None


class BridgeAdminForwardRequeueMintRequest(BaseModel):
    operation_id: str
    note: str | None = None


class BridgeAdminReverseRequeuePayoutRequest(BaseModel):
    operation_id: str
    note: str | None = None


class BridgeAdminReverseMarkDisputedRequest(BaseModel):
    operation_id: str
    note: str


class BridgeReverseLiabilitySummaryResponse(BaseModel):
    reverse_enabled_runtime: bool
    reverse_public_mode: str
    counts_by_status: dict[str, int]
    total_pending_burn_wacp_wei: str
    total_confirmed_burn_wacp_wei: str
    total_confirmed_burn_acp_smallest: str
    total_payout_sent_wacp_wei: str
    total_payout_sent_acp_smallest: str
    total_disputed_wacp_wei: str
    total_disputed_acp_smallest: str
    total_completed_wacp_wei: str
    total_completed_acp_smallest: str
    outstanding_operator_liability_acp_smallest: str
    notes: list[str] = Field(default_factory=list)
