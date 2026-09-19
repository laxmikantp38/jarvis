"""Revenue, expenses and the goal tree.

Forward-only and safe on a database with data: three new tables.

Money is stored as integer paise, never a float, so that nothing is
approximately right about the number the whole system reasons about.

Revision ID: 0004
Revises: 0003
Created: 2026-09-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "revenue_record",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("stream", sa.String(length=24), nullable=False),
        sa.Column("certainty", sa.String(length=16), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=False, server_default=""),
    )
    op.create_index("ix_revenue_occurred_on", "revenue_record", ["occurred_on"])
    op.create_index("ix_revenue_certainty", "revenue_record", ["certainty"])

    op.create_table(
        "expense_record",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("category", sa.String(length=24), nullable=False),
        sa.Column("project_key", sa.String(length=32), nullable=True),
        sa.Column("recurrence", sa.String(length=16), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=False, server_default=""),
    )
    op.create_index("ix_expense_occurred_on", "expense_record", ["occurred_on"])

    op.create_table(
        "goal",
        sa.Column("key", sa.String(length=48), primary_key=True),
        sa.Column("parent_key", sa.String(length=48), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("goal_type", sa.String(length=20), nullable=False),
        # Null is unallocated, which is reported as such and never as zero.
        sa.Column("target", sa.Numeric(), nullable=True),
        sa.Column("current", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("unit", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("start_on", sa.Date(), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=False),
        sa.Column("rollup", sa.String(length=16), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=16), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("goal")
    op.drop_index("ix_expense_occurred_on", table_name="expense_record")
    op.drop_table("expense_record")
    op.drop_index("ix_revenue_certainty", table_name="revenue_record")
    op.drop_index("ix_revenue_occurred_on", table_name="revenue_record")
    op.drop_table("revenue_record")
