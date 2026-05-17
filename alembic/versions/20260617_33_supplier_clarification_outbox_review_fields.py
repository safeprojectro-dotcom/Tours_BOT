"""A5: outbox review metadata (last_reviewed_*, review_note).

Revision: 20260617_33
Revises: 20260611_32
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260617_33"
down_revision = "20260611_32"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "supplier_clarification_outbox_items",
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "supplier_clarification_outbox_items",
        sa.Column("last_reviewed_by_telegram_user_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "supplier_clarification_outbox_items",
        sa.Column("review_note", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_supplier_clarification_outbox_items_last_reviewed_at",
        "supplier_clarification_outbox_items",
        ["last_reviewed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_supplier_clarification_outbox_items_last_reviewed_at",
        table_name="supplier_clarification_outbox_items",
    )
    op.drop_column("supplier_clarification_outbox_items", "review_note")
    op.drop_column("supplier_clarification_outbox_items", "last_reviewed_by_telegram_user_id")
    op.drop_column("supplier_clarification_outbox_items", "last_reviewed_at")
