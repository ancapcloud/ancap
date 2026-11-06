from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Money
from app.schemas.strategies import FeeModel


class ListingStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class MarketplaceSort(str, Enum):
    popular = "popular"
    recent = "recent"
    price_asc = "price_asc"
    price_desc = "price_desc"
    rating = "rating"


class ListingCreateRequest(BaseModel):
    strategy_id: str
    strategy_version_id: str
    fee_model: FeeModel
    status: ListingStatus = ListingStatus.active
    terms_url: str | None = None
    notes: str | None = None


class ListingPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    strategy_id: str
    strategy_version_id: str | None = None
    fee_model: dict
    status: ListingStatus
    terms_url: str | None = None
    notes: str | None = None
    created_at: datetime


class MarketplaceListingPublic(BaseModel):
    id: str
    strategy_id: str
    strategy_version_id: str | None = None
    strategy_name: str
    strategy_description: str | None = None
    category: str | None = None
    fee_model: dict
    price: Money
    status: ListingStatus
    terms_url: str | None = None
    notes: str | None = None
    listing_views: int
    listing_purchases: int
    rating: float
    rating_count: int
    is_featured: bool
    is_trending: bool
    # Paid placement. Clients must label these "Sponsored"/"Реклама" (EU DSA Art. 26).
    is_sponsored: bool = False
    sponsored_until: datetime | None = None
    created_at: datetime


class MarketplaceListingsResponse(BaseModel):
    items: list[MarketplaceListingPublic]
    total: int
    limit: int
    offset: int
    available_categories: list[str]


class ListingPromotionPricingPublic(BaseModel):
    enabled: bool
    daily_fee: Money
    max_days: int
    slots_per_category: int
    disclosure: str = "Promoted listings are shown first and always labelled as sponsored."


class ListingPromotionCreateRequest(BaseModel):
    days: int = Field(..., ge=1, le=365)


class ListingPromotionPublic(BaseModel):
    id: str
    listing_id: str
    days: int
    starts_at: datetime
    ends_at: datetime
    amount: Money
    ledger_event_id: str | None = None
    created_at: datetime


class ListingPromotionsResponse(BaseModel):
    items: list[ListingPromotionPublic]
    active_until: datetime | None = None
