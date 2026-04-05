"""add tour.cover_media_reference

Revision ID: 20260405_04
Revises: 20260327_03
Create Date: 2026-04-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260405_04"
down_revision = "20260327_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tours",
        sa.Column("cover_media_reference", sa.String(length=1024), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tours", "cover_media_reference")
