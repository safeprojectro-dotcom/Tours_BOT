"""A4: supplier clarification outbox items (internal admin workflow; no supplier send).

Revision: 20260610_31
Revises: 20260609_30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260610_31"
down_revision = "20260609_30"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_clarification_outbox_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("supplier_offer_id", sa.Integer(), nullable=False),
        sa.Column("workflow_status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("draft_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by_telegram_user_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "workflow_status IN ('open', 'done', 'dismissed')",
            name="ck_supplier_clarification_outbox_items_workflow_status",
        ),
        sa.ForeignKeyConstraint(
            ["supplier_offer_id"],
            ["supplier_offers.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_supplier_clarification_outbox_items_supplier_offer_id"),
        "supplier_clarification_outbox_items",
        ["supplier_offer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_supplier_clarification_outbox_items_created_by_telegram_user_id"),
        "supplier_clarification_outbox_items",
        ["created_by_telegram_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_supplier_clarification_outbox_items_created_by_telegram_user_id"),
        table_name="supplier_clarification_outbox_items",
    )
    op.drop_index(
        op.f("ix_supplier_clarification_outbox_items_supplier_offer_id"),
        table_name="supplier_clarification_outbox_items",
    )
    op.drop_table("supplier_clarification_outbox_items")
