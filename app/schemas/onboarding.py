"""L3: Proof-of-Agent onboarding schemas."""
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# Supported challenge types (PLAN L3 §12). Payload shapes:
# - reasoning: { "prompt": str, "nonce": str }; solution = first 8 hex chars of SHA256(nonce); solution_hash = SHA256(solution).hexdigest()
# - tool_use:  { "task": str, "input": str, "nonce": str }; solution = SHA256(input).hexdigest(); solution_hash = solution (64 hex chars)
ChallengeType = Literal["reasoning", "tool_use"]


class ChallengeCreateRequest(BaseModel):
    challenge_type: ChallengeType = "reasoning"


class ChallengePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    challenge_type: str
    payload: dict[str, Any]
    nonce: str
    expires_at: datetime


class AttestRequest(BaseModel):
    challenge_id: str
    solution_hash: str = Field(..., min_length=32, max_length=64)  # hex hash of solution
    attestation_sig: Optional[str] = Field(None, max_length=2048)


class AttestationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    challenge_id: str
    created_at: datetime


# --- ROP-05: Onboarding templates schemas ---
class TemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = Field(None, max_length=4096)
    template_type: str = Field(..., pattern=r'^[a-z][a-z0-9-]{0,62}$')  # e.g., "quickstart", "faucet"
    config_json: dict = Field(default_factory=dict, description="Template configuration as JSON")


class TemplatePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    description: Optional[str]
    template_type: str
    config_json: dict
    created_by_user_id: Optional[str]
    created_at: datetime
    updated_at: datetime
