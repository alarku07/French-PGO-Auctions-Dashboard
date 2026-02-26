"""Add auction_event table and link auction records

Revision ID: 002_add_auction_event
Revises: 001_initial_schema
Create Date: 2026-02-25 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "002_add_auction_event"
down_revision: str | None = "001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create auction_event table
    op.create_table(
        "auction_event",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("is_cancelled", sa.Boolean(), nullable=False, server_default="false"),
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
        sa.UniqueConstraint("event_date", name="uq_auction_event_date"),
    )
    op.create_index(
        "idx_auction_event_cancelled", "auction_event", ["is_cancelled"]
    )

    # 2. Add nullable FK column to auction table
    # Use batch_alter_table for SQLite compatibility (batch = copy-and-move)
    with op.batch_alter_table("auction") as batch_op:
        batch_op.add_column(
            sa.Column("auction_event_id", sa.Integer(), nullable=True),
        )
        batch_op.create_foreign_key(
            "fk_auction_auction_event",
            "auction_event",
            ["auction_event_id"],
            ["id"],
        )
        batch_op.create_index("idx_auction_event_id", ["auction_event_id"])


def downgrade() -> None:
    # Reverse in exact opposite order of upgrade
    with op.batch_alter_table("auction") as batch_op:
        batch_op.drop_index("idx_auction_event_id")
        batch_op.drop_constraint("fk_auction_auction_event", type_="foreignkey")
        batch_op.drop_column("auction_event_id")

    op.drop_index("idx_auction_event_cancelled", table_name="auction_event")
    op.drop_table("auction_event")
