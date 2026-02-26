from __future__ import annotations

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.auction import Auction


class AuctionEvent(Base):
    __tablename__ = "auction_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Natural key — no two events share the same calendar date
    event_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Set when the event disappears from the EEX calendar; record is never deleted
    is_cancelled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Human-readable labels from the EEX calendar table
    auctioning_month: Mapped[str | None] = mapped_column(String(50), nullable=True)
    production_month: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Datetime columns — closure date drives event_date
    order_book_open: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cash_trading_limits_modification: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    order_book_close: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    order_matching: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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

    # One-to-many: one AuctionEvent groups many Auction records sharing the same date
    auctions: Mapped[list[Auction]] = relationship(
        "Auction",
        back_populates="auction_event",
        cascade="save-update",
        lazy="select",
    )

    __table_args__ = (
        UniqueConstraint("event_date", name="uq_auction_event_date"),
        Index("idx_auction_event_cancelled", "is_cancelled"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuctionEvent id={self.id} date={self.event_date} "
            f"cancelled={self.is_cancelled!r}>"
        )


__all__ = ["AuctionEvent"]
