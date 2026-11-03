from typing import Literal
from pydantic import BaseModel, Field, HttpUrl, field_validator


class ListingDraft(BaseModel):
    chain_id: Literal[4663, 46630]
    address: str = Field(pattern=r"^0x[0-9a-fA-F]{40}$")
    website: HttpUrl
    description: str = Field(min_length=1, max_length=3000)
    contact: str = Field(min_length=1, max_length=320)

    @field_validator("address")
    @classmethod
    def normalize_address(cls, value: str) -> str:
        return value.lower()


class ListingReview(BaseModel):
    version: int = Field(ge=1)
    decision: Literal["approved", "revision", "rejected"]
    comment: str = Field(min_length=1, max_length=2000)


class ListingVersion(BaseModel):
    version: int = Field(ge=1)
