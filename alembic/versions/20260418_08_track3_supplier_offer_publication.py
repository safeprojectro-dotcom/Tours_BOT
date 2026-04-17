"""Track 3: supplier offer moderation + showcase publication metadata.

Extends Postgres enum supplier_offer_lifecycle with approved, rejected, published.
Adds traceability columns (rejection reason, published_at, Telegram message ids).

Revision ID: 20260418_08
Revises: 20260417_07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260418_08"
down_revision = "20260417_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL: extend enum in place (one-way; downgrade does not remove labels).
    op.execute("ALTER TYPE supplier_offer_lifecycle ADD VALUE 'approved'")
    op.execute("ALTER TYPE supplier_offer_lifecycle ADD VALUE 'rejected'")
    op.execute("ALTER TYPE supplier_offer_lifecycle ADD VALUE 'published'")

    op.add_column("supplier_offers", sa.Column("moderation_rejection_reason", sa.Text(), nullable=True))
    op.add_column(
        "supplier_offers",
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "supplier_offers",
        sa.Column("showcase_chat_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "supplier_offers",
        sa.Column("showcase_message_id", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        op.f("ix_supplier_offers_lifecycle_status"),
        "supplier_offers",
        ["lifecycle_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_supplier_offers_lifecycle_status"), table_name="supplier_offers")
    op.drop_column("supplier_offers", "showcase_message_id")
    op.drop_column("supplier_offers", "showcase_chat_id")
    op.drop_column("supplier_offers", "published_at")
    op.drop_column("supplier_offers", "moderation_rejection_reason")
    # Enum labels remain on supplier_offer_lifecycle (Postgres cannot drop values trivially).
