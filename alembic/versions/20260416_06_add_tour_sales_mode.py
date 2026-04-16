"""add tour sales_mode

Revision ID: 20260416_06
Revises: 20260405_05
Create Date: 2026-04-16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260416_06"
down_revision = "20260405_05"
branch_labels = None
depends_on = None

tour_sales_mode_enum = postgresql.ENUM(
    "per_seat",
    "full_bus",
    name="tour_sales_mode",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    tour_sales_mode_enum.create(bind, checkfirst=True)

    op.add_column(
        "tours",
        sa.Column(
            "sales_mode",
            tour_sales_mode_enum,
            nullable=False,
            server_default="per_seat",
        ),
    )


def downgrade() -> None:
    op.drop_column("tours", "sales_mode")

    bind = op.get_bind()
    tour_sales_mode_enum.drop(bind, checkfirst=True)
