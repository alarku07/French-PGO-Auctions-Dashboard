"""Add calendar detail columns to auction_event table

Revision ID: 003_add_auction_event_details
Revises: 002_add_auction_event
Create Date: 2026-02-26 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "003_add_auction_event_details"
down_revision: str | None = "002_add_auction_event"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("auction_event") as batch_op:
        batch_op.add_column(sa.Column("auctioning_month", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("production_month", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("order_book_open", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("cash_trading_limits_modification", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("order_book_close", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("order_matching", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("auction_event") as batch_op:
        for col in (
            "order_matching",
            "order_book_close",
            "cash_trading_limits_modification",
            "order_book_open",
            "production_month",
            "auctioning_month",
        ):
            batch_op.drop_column(col)
