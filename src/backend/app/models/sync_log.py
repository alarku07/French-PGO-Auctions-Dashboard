from datetime import UTC, datetime

from sqlalchemy import (
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class SyncLog(Base):
    __tablename__ = "sync_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    sync_type: Mapped[str] = mapped_column(String(20), nullable=False)
    records_added: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    __table_args__ = (
        Index("idx_sync_timestamp", run_timestamp.desc()),
        Index("idx_sync_outcome", "outcome"),
    )

    def __repr__(self) -> str:
        return (
            f"<SyncLog id={self.id} type={self.sync_type!r} "
            f"outcome={self.outcome!r}>"
        )


__all__ = ["SyncLog"]
