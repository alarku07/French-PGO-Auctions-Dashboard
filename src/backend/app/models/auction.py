from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.auction_event import AuctionEvent


class Auction(Base):
    __tablename__ = "auction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Natural key fields
    auction_date: Mapped[date] = mapped_column(Date, nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    production_period: Mapped[str] = mapped_column(String(20), nullable=False)
    technology: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="upcoming")

    # Result fields (NULL for upcoming auctions)
    volume_offered_mwh: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    volume_allocated_mwh: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    num_bids: Mapped[int | None] = mapped_column(Integer, nullable=True)
    num_winning_bids: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weighted_avg_price_eur: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True
    )
    reserve_price_eur: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True
    )

    # Calendar fields (NULL for past results, populated for upcoming)
    order_book_open: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    order_book_close: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    order_matching: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # AuctionEvent association (nullable — historical records pre-feature have no event)
    auction_event_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("auction_event.id"), nullable=True
    )
    auction_event: Mapped[AuctionEvent | None] = relationship(
        "AuctionEvent",
        back_populates="auctions",
        lazy="select",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        UniqueConstraint(
            "auction_date",
            "region",
            "production_period",
            "technology",
            name="uq_auction_natural_key",
        ),
        CheckConstraint("status IN ('past', 'upcoming')", name="ck_auction_status"),
        CheckConstraint(
            "technology IN ('Wind', 'Hydro', 'Solar', 'Thermal') OR technology IS NULL",
            name="ck_auction_technology",
        ),
        CheckConstraint(
            "volume_offered_mwh >= 0 OR volume_offered_mwh IS NULL",
            name="ck_volume_offered_nonneg",
        ),
        CheckConstraint(
            "volume_allocated_mwh >= 0 OR volume_allocated_mwh IS NULL",
            name="ck_volume_allocated_nonneg",
        ),
        CheckConstraint(
            "weighted_avg_price_eur >= 0 OR weighted_avg_price_eur IS NULL",
            name="ck_price_nonneg",
        ),
        CheckConstraint(
            "reserve_price_eur >= 0 OR reserve_price_eur IS NULL",
            name="ck_reserve_price_nonneg",
        ),
        Index("idx_auction_date", "auction_date"),
        Index("idx_auction_region", "region"),
        Index("idx_auction_status", "status"),
        Index(
            "idx_auction_composite",
            "auction_date",
            "region",
            "production_period",
            "technology",
        ),
        Index("idx_auction_event_id", "auction_event_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Auction id={self.id} date={self.auction_date} "
            f"region={self.region!r} status={self.status!r}>"
        )


# Unused imports kept for type annotation completeness
__all__ = ["Auction"]
_text_type = Text  # referenced in SyncLog
