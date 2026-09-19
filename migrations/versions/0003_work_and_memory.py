"""Projects, tasks, events and user memory.

Forward-only and safe on a database with data: four new tables.

Revision ID: 0003
Revises: 0002
Created: 2026-09-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project",
        sa.Column("key", sa.String(length=32), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("objective", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
    )
    op.create_table(
        "task",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "project_key",
            sa.String(length=32),
            sa.ForeignKey("project.key"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attention", sa.String(length=16), nullable=False),
        # Never nullable: an unclassified record would have to be given a
        # default, and any permissive default is a leak waiting to happen.
        sa.Column("confidentiality", sa.String(length=24), nullable=False),
        sa.Column("notes", sa.String(length=4000), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_task_project_status", "task", ["project_key", "status"])

    op.create_table(
        "event",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("project_key", sa.String(length=32), nullable=True),
        sa.Column("task_id", sa.String(length=36), nullable=True),
    )
    op.create_index("ix_event_occurred_at", "event", ["occurred_at"])

    op.create_table(
        "user_fact",
        sa.Column("key", sa.String(length=64), primary_key=True),
        sa.Column("value", sa.String(length=4000), nullable=False),
        sa.Column("confidentiality", sa.String(length=24), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # AD-8: append-only is enforced by the storage layer, not by discipline.
    op.execute(
        "CREATE TRIGGER event_is_append_only_update "
        "BEFORE UPDATE ON event BEGIN "
        "SELECT RAISE(ABORT, 'event is append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER event_is_append_only_delete "
        "BEFORE DELETE ON event BEGIN "
        "SELECT RAISE(ABORT, 'event is append-only'); END"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS event_is_append_only_delete")
    op.execute("DROP TRIGGER IF EXISTS event_is_append_only_update")
    op.drop_table("user_fact")
    op.drop_index("ix_event_occurred_at", table_name="event")
    op.drop_table("event")
    op.drop_index("ix_task_project_status", table_name="task")
    op.drop_table("task")
    op.drop_table("project")
