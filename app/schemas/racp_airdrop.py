"""Opt-in rACP campaign: public status and authenticated wallet vouchers."""
from pydantic import BaseModel, Field


class RacpAirdropVoucherRequest(BaseModel):
    address: str = Field(min_length=42, max_length=42)
    turnstile_token: str | None = Field(default=None, max_length=4096)


class RacpAirdropStatus(BaseModel):
    enabled: bool
    chain_id: int = 4663
    token_contract: str
    airdrop_contract: str | None = None
    grant: str = "500"
    budget: str = "1000000"
    distributed: str = "0"
    available: str = "0"
    remaining_claims: int = 0
    paused: bool = True
    recipient_pays_network_fee: bool = True


class RacpAirdropVoucher(BaseModel):
    chain_id: int = 4663
    airdrop_contract: str
    token_contract: str
    recipient: str
    eligibility_id: str
    deadline: int
    grant: str = "500"
    signature: str
