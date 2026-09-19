"""Footage reserve and the daily-check ledger.

Forward-only and safe on a database with data: two new tables, nothing reshaped.

Revision ID: 0002
Revises: 0001
Created: 2026-09-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "footage_reserve",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clips_available", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clips_per_publish", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "daily_check",
        sa.Column("name", sa.String(length=64), primary_key=True),
        # The user's local date, because "today" is a wall-clock idea.
        sa.Column("last_local_day", sa.String(length=10), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("daily_check")
    op.drop_table("footage_reserve")
