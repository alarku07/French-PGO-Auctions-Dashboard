"""Initial schema: Auction and SyncLog tables

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-02-23 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auction",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("auction_date", sa.Date(), nullable=False),
        sa.Column("region", sa.String(100), nullable=False),
        sa.Column("production_period", sa.String(20), nullable=False),
        sa.Column("technology", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="upcoming"),
        sa.Column("volume_offered_mwh", sa.Numeric(12, 2), nullable=True),
        sa.Column("volume_allocated_mwh", sa.Numeric(12, 2), nullable=True),
        sa.Column("num_bids", sa.Integer(), nullable=True),
        sa.Column("num_winning_bids", sa.Integer(), nullable=True),
        sa.Column("weighted_avg_price_eur", sa.Numeric(10, 4), nullable=True),
        sa.Column("reserve_price_eur", sa.Numeric(10, 4), nullable=True),
        sa.Column("order_book_open", sa.DateTime(timezone=True), nullable=True),
        sa.Column("order_book_close", sa.DateTime(timezone=True), nullable=True),
        sa.Column("order_matching", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "auction_date",
            "region",
            "production_period",
            "technology",
            name="uq_auction_natural_key",
        ),
        sa.CheckConstraint("status IN ('past', 'upcoming')", name="ck_auction_status"),
        sa.CheckConstraint(
            "technology IN ('Wind', 'Hydro', 'Solar', 'Thermal') OR technology IS NULL",
            name="ck_auction_technology",
        ),
        sa.CheckConstraint(
            "volume_offered_mwh >= 0 OR volume_offered_mwh IS NULL",
            name="ck_volume_offered_nonneg",
        ),
        sa.CheckConstraint(
            "volume_allocated_mwh >= 0 OR volume_allocated_mwh IS NULL",
            name="ck_volume_allocated_nonneg",
        ),
        sa.CheckConstraint(
            "weighted_avg_price_eur >= 0 OR weighted_avg_price_eur IS NULL",
            name="ck_price_nonneg",
        ),
        sa.CheckConstraint(
            "reserve_price_eur >= 0 OR reserve_price_eur IS NULL",
            name="ck_reserve_price_nonneg",
        ),
    )
    op.create_index("idx_auction_date", "auction", ["auction_date"])
    op.create_index("idx_auction_region", "auction", ["region"])
    op.create_index("idx_auction_status", "auction", ["status"])
    op.create_index(
        "idx_auction_composite",
        "auction",
        ["auction_date", "region", "production_period", "technology"],
    )

    op.create_table(
        "sync_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "run_timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("sync_type", sa.String(20), nullable=False),
        sa.Column("records_added", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_sync_timestamp", "sync_log", ["run_timestamp"], postgresql_using="btree"
    )
    op.create_index("idx_sync_outcome", "sync_log", ["outcome"])


def downgrade() -> None:
    op.drop_table("sync_log")
    op.drop_table("auction")
