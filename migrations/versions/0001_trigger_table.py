"""The scheduled routine.

Forward-only and safe to apply to a database with data in it: this creates a
table, it does not reshape one.

Revision ID: 0001
Revises:
Created: 2026-08-29
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trigger",
        sa.Column("key", sa.String(length=64), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.String(length=2000), nullable=False),
        sa.Column("at", sa.Time(), nullable=False),
        sa.Column("days", sa.String(length=16), nullable=False),
        sa.Column("notification_class", sa.String(length=16), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        # UTC. SQLite has no timezone-aware column, so the adapter attaches it
        # on the way out rather than trusting the stored value.
        sa.Column("last_fired_at", sa.DateTime(), nullable=True),
        sa.Column("next_due_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_trigger_next_due_at", "trigger", ["next_due_at"])


def downgrade() -> None:
    op.drop_index("ix_trigger_next_due_at", table_name="trigger")
    op.drop_table("trigger")
