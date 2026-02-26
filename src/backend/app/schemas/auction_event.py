from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

# ─── Auction summary (nested inside AuctionEventResponse) ────────────────────


class AuctionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    auction_date: date
    region: str
    production_period: str
    technology: str | None
    status: str


# ─── AuctionEvent ─────────────────────────────────────────────────────────────


class AuctionEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_date: date
    status: str  # computed: "upcoming" | "completed" — NOT stored in DB
    is_cancelled: bool
    auctioning_month: str | None
    production_month: str | None
    order_book_open: datetime | None
    cash_trading_limits_modification: datetime | None
    order_book_close: datetime | None
    order_matching: datetime | None
    auctions: list[AuctionSummary]

    @field_validator("status", mode="before")
    @classmethod
    def _reject_invalid_status(cls, v: str) -> str:
        if v not in ("upcoming", "completed"):
            raise ValueError(f"Invalid status value: {v!r}")
        return v


class AuctionEventListResponse(BaseModel):
    data: list[AuctionEventResponse]
    count: int


class AuctionEventYearsResponse(BaseModel):
    data: list[int]
