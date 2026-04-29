"""add cancel_requested to job_items

Revision ID: 0002_add_job_items_cancel_requested
Revises: 0001_initial_schema
Create Date: 2026-04-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_add_job_items_cancel_requested"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "job_items",
        sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("job_items", "cancel_requested")

