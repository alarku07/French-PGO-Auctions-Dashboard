from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

# ─── Auction ────────────────────────────────────────────────────────────────


class TechnologyRowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    auction_date: date
    region: str
    production_period: str
    technology: str | None
    volume_offered_mwh: Decimal | None
    volume_allocated_mwh: Decimal | None
    num_bids: int | None
    num_winning_bids: int | None
    weighted_avg_price_eur: Decimal | None
    status: str


class AuctionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    auction_date: date
    region: str
    production_period: str
    technology: str | None
    volume_offered_mwh: Decimal | None
    volume_allocated_mwh: Decimal | None
    num_bids: int | None
    num_winning_bids: int | None
    weighted_avg_price_eur: Decimal | None
    status: str
    technology_rows: list[TechnologyRowResponse] = []


class UpcomingAuctionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    auction_date: date
    region: str
    production_period: str
    order_book_open: datetime | None
    order_book_close: datetime | None
    order_matching: datetime | None


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class AuctionListResponse(BaseModel):
    data: list[AuctionResponse]
    pagination: PaginationMeta


class UpcomingAuctionListResponse(BaseModel):
    data: list[UpcomingAuctionResponse]
    count: int


# ─── Stats ──────────────────────────────────────────────────────────────────


class StatsResponse(BaseModel):
    total_auctions_held: int
    total_volume_awarded_mwh: Decimal | None
    overall_weighted_avg_price_eur: Decimal | None
    last_updated: datetime | None


# ─── Charts ─────────────────────────────────────────────────────────────────


class PriceChartDataPoint(BaseModel):
    auction_date: date
    region: str
    weighted_avg_price_eur: Decimal | None
    volume_allocated_mwh: Decimal | None


class PriceChartFilters(BaseModel):
    start_date: date | None
    end_date: date | None
    region: str | None
    technology: str | None


class PriceChartResponse(BaseModel):
    data: list[PriceChartDataPoint]
    filters: PriceChartFilters


class VolumeChartDataPoint(BaseModel):
    period: str  # YYYY-MM-DD, YYYY-MM, or YYYY depending on aggregation
    region: str
    volume_offered_mwh: Decimal | None
    volume_allocated_mwh: Decimal | None


class VolumeChartFilters(BaseModel):
    start_date: date | None
    end_date: date | None
    region: str | None
    technology: str | None
    aggregation: str


class VolumeChartResponse(BaseModel):
    data: list[VolumeChartDataPoint]
    filters: VolumeChartFilters


# ─── Lookups ─────────────────────────────────────────────────────────────────


class RegionListResponse(BaseModel):
    data: list[str]


class TechnologyListResponse(BaseModel):
    data: list[str]


# ─── Errors ──────────────────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ─── Health ──────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    database: str
