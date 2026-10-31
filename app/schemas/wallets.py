from __future__ import annotations

import math
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator
from typing import Literal


class AcpTokenomicsBucket(BaseModel):
    key: str
    label: str
    acp: str
    utxo_count: int = 0


class AcpDepositAddressResponse(BaseModel):
    address: str
    mode: Literal["standard", "privacy"] = "standard"
    sub_index: int | None = None
    redacted: str | None = None
    privacy_profile: str | None = None
    reuse_policy: str | None = None
    note: str | None = None
    needs_personalize: bool = False


class AcpPrivacyDepositRequest(BaseModel):
    wallet_password: str | None = Field(
        default=None,
        min_length=8,
        description="Required once if view key not cached yet — unlocks keystore to bind privacy receive set",
    )
    label: str | None = Field(default=None, max_length=120)


class AcpPersonalizeWalletRequest(BaseModel):
    wallet_password: str = Field(
        ...,
        min_length=8,
        description="Account password used to decrypt the current wallet binding and encrypt the new personal wallet",
    )


class AcpPersonalizeWalletResponse(BaseModel):
    address: str
    wallet_backup_mnemonic: str
    note: str = (
        "Personal ACP deposit address created. Save the mnemonic offline; "
        "the shared custodial hot address is no longer bound to this account."
    )


class AcpPrivacyStatusPublic(BaseModel):
    privacy_profile: str
    view_key_bound: bool
    privacy_next_index: int
    unlinkable_receive_count: int
    note: str


class AcpBalanceResponse(BaseModel):
    address: str
    units: str
    acp: str
    utxo_count: int = 0
    on_chain_acp: str | None = None
    ledger_credits_acp: str | None = None
    headline_acp: str | None = None
    in_work_acp: str | None = None
    in_work_staked_acp: str | None = None
    in_work_ledger_acp: str | None = None
    available_acp: str | None = None
    platform_credits_acp: str | None = None
    tokenomics_buckets: list[AcpTokenomicsBucket] | None = None
    view_mode: Literal["user", "operator_hot"] | None = None
    balance_status: Literal["live", "degraded", "warming"] | None = None
    vested_unlocked_acp: str | None = None
    vested_locked_acp: str | None = None
    balance_note: str | None = None
    # Non-overlapping breakdown (compat fields above retained).
    on_chain_at_deposit_acp: str | None = None
    privacy_receive_acp: str | None = None
    platform_ledger_acp: str | None = None
    staked_acp: str | None = None
    reserved_total_acp: str | None = None
    withdrawable_now_acp: str | None = None
    withdraw_source: Literal["personal_utxo", "custodial_hot", "none"] | None = None
    operator_hot_live_acp: str | None = None
    operator_controlled_live_acp: str | None = None
    chain_supply_acp: str | None = None
    supply_cap_acp: str | None = None
    supply_invariant_ok: bool | None = None
    primary_acp: str | None = None
    primary_kind: Literal["on_chain", "platform_credits", "operator_total", "chain_supply"] | None = None
    probe_status: Literal["live", "degraded", "unavailable"] | None = None
    chain_height: int | None = None


class AcpWithdrawRequest(BaseModel):
    to_address: str
    amount_acp: str = Field(..., description="Decimal string, e.g. 1.5")
    fee_acp: str | None = Field(default=None, description="Optional fee in ACP (must be >= network minimum)")
    wallet_password: str = Field(..., min_length=8, description="Account password used to decrypt wallet seed")

    @field_validator("amount_acp", "fee_acp", mode="before")
    @classmethod
    def _coerce_decimal_field(cls, v: object) -> str | None:
        if v is None:
            return None
        if isinstance(v, bool):
            raise ValueError("expected a number or decimal string, not a boolean")
        if isinstance(v, int):
            return str(v)
        if isinstance(v, float):
            if not math.isfinite(v):
                raise ValueError("expected a finite number")
            # Avoid scientific notation and stray float artifacts where possible.
            d = Decimal(str(v))
            return format(d, "f").rstrip("0").rstrip(".") or "0"
        return str(v).strip()


class AcpWithdrawResponse(BaseModel):
    accepted: bool | None = None
    txid: str | None = None
    reason: str | None = None
    # Async withdraw (avoids Cloudflare ~100s edge cutoffs on tip-scan transfers).
    status: Literal["pending", "completed", "failed"] | None = None
    job_id: str | None = None


class AcpWithdrawJobResponse(BaseModel):
    job_id: str
    status: Literal["pending", "completed", "failed"]
    accepted: bool | None = None
    txid: str | None = None
    reason: str | None = None
    error: str | None = None


class AcpSwapQuoteRequest(BaseModel):
    usdt_trc20_amount: str = Field(..., description="Decimal string, e.g. 25")


class AcpSwapQuoteResponse(BaseModel):
    usdt_trc20_amount: str
    rate_acp_per_usdt: str
    estimated_acp_amount: str


class AcpSwapOrderCreateRequest(BaseModel):
    usdt_trc20_amount: str = Field(..., description="Decimal string, e.g. 25")
    payout_acp_address: str = Field(..., description="ACP address where converted funds are sent")
    note: str | None = None


class AcpSwapOrderConfirmRequest(BaseModel):
    tron_txid: str | None = None


class AcpSwapOrderPublic(BaseModel):
    id: str
    user_id: str
    status: Literal["awaiting_deposit", "pending_review", "completed", "cancelled", "rejected"]
    usdt_trc20_amount: str
    rate_acp_per_usdt: str
    estimated_acp_amount: str
    payout_acp_address: str
    deposit_trc20_address: str
    deposit_reference: str
    tron_txid: str | None = None
    payout_txid: str | None = None
    note: str | None = None
    created_at: str
    updated_at: str


class AcpSwapCompleteResponse(BaseModel):
    order: AcpSwapOrderPublic
    transfer: AcpWithdrawResponse


class AcpSwapCompleteRequest(BaseModel):
    wallet_password: str = Field(..., min_length=8, description="Account password used to decrypt wallet seed")


class AcpTransactionIoPublic(BaseModel):
    address: str | None = None
    units: str
    acp: str
    vout: int | None = None


class AcpTransactionDetailsPublic(BaseModel):
    txid: str
    block_height: int
    block_hash: str | None = None
    block_time: str
    confirmations: int
    total_input_units: str
    total_input_acp: str
    total_output_units: str
    total_output_acp: str
    fee_units: str
    fee_acp: str
    inputs: list[AcpTransactionIoPublic]
    outputs: list[AcpTransactionIoPublic]


class AcpTransactionPublic(BaseModel):
    txid: str
    block_height: int
    block_time: str
    confirmations: int
    direction: Literal["in", "out", "self"]
    sent_units: str
    sent_acp: str
    received_units: str
    received_acp: str
    net_units: str
    net_acp: str
