"""rACP → ACP redemption public schemas — never put secrets here."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RacpRedeemPublicStatus(BaseModel):
    enabled: bool = False
    configured: bool = False
    paused: bool = False
    dry_run: bool = True
    chain_id: int = 4663
    token_contract: str = ""
    reserve_acp_address: str = ""
    reserve_balance_acp: Optional[str] = None
    racp_per_acp: int = 10
    open_liability_count: int = 0
    completed_count: int = 0
    redeem_path: str = "/tokens/racp/redeem"
    status_path: str = "/v1/racp/redeem/status"
    notes: list[str] = Field(default_factory=list)


class RacpRedemptionPublic(BaseModel):
    id: str
    status: str
    redemption_id: int
    holder: str
    amount_racp_wei: str
    amount_racp: str
    amount_acp_smallest: str
    amount_acp: str
    user_acp_address: str
    rh_tx_hash: str
    rh_log_index: int
    rh_block_number: Optional[int] = None
    acp_tx_hash: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RacpRedeemAdminBindPayoutRequest(BaseModel):
    redemption_uuid: str
    acp_tx_hash: str = Field(min_length=8, max_length=128)


class RacpRedeemAdminNoteRequest(BaseModel):
    redemption_uuid: str
    notes: Optional[str] = Field(default=None, max_length=500)
