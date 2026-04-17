"""Track 3.1: optional showcase photo URL + boarding places text for RO channel template.

Revision ID: 20260419_09
Revises: 20260418_08
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260419_09"
down_revision = "20260418_08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "supplier_offers",
        sa.Column("showcase_photo_url", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "supplier_offers",
        sa.Column("boarding_places_text", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("supplier_offers", "boarding_places_text")
    op.drop_column("supplier_offers", "showcase_photo_url")
