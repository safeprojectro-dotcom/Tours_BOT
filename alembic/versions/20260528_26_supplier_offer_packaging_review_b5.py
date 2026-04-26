"""B5: packaging review audit columns + extra packaging_status enum values (no publish / no lifecycle change in migration)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260528_26"
down_revision = "20260527_25"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE supplier_offer_packaging_status ADD VALUE IF NOT EXISTS 'packaging_rejected'")
    op.execute("ALTER TYPE supplier_offer_packaging_status ADD VALUE IF NOT EXISTS 'clarification_requested'")
    op.add_column(
        "supplier_offers",
        sa.Column("packaging_reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("supplier_offers", sa.Column("packaging_reviewed_by", sa.String(length=256), nullable=True))
    op.add_column("supplier_offers", sa.Column("packaging_rejection_reason", sa.Text(), nullable=True))
    op.add_column("supplier_offers", sa.Column("clarification_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("supplier_offers", "clarification_reason")
    op.drop_column("supplier_offers", "packaging_rejection_reason")
    op.drop_column("supplier_offers", "packaging_reviewed_by")
    op.drop_column("supplier_offers", "packaging_reviewed_at")
    # enum values are not removed in PostgreSQL safely here
