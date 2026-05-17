"""S1C-1: supplier_notification_outbox — intents for future Telegram supplier DMs (no send).

Revision: 20260617_34
Revises: 20260617_33
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260617_34"
down_revision = "20260617_33"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_notification_outbox",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False, server_default="telegram_dm"),
        sa.Column("supplier_id", sa.Integer(), nullable=True),
        sa.Column("supplier_offer_id", sa.Integer(), nullable=True),
        sa.Column("tour_id", sa.Integer(), nullable=True),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
        sa.Column("contact_resolution_status", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("readiness_warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("dispatch_status", sa.String(length=32), nullable=False, server_default="pending_dispatch"),
        sa.Column("actor_surface", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "event_type IN ('supplier_offer_published', 'supplier_order_created')",
            name="ck_supplier_notification_outbox_event_type",
        ),
        sa.CheckConstraint(
            "contact_resolution_status IN ("
            "'resolved_with_contact', 'resolved_missing_contact', 'missing_relationship', "
            "'ambiguous_suppliers'"
            ")",
            name="ck_supplier_notification_outbox_contact_resolution_status",
        ),
        sa.CheckConstraint(
            "dispatch_status IN ('pending_dispatch', 'skipped_no_target')",
            name="ck_supplier_notification_outbox_dispatch_status",
        ),
        sa.CheckConstraint(
            "char_length(btrim(idempotency_key)) > 0",
            name="ck_supplier_notification_outbox_idem_nonempty",
        ),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["supplier_offer_id"], ["supplier_offers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tour_id"], ["tours.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_supplier_notification_outbox_idempotency_key"),
    )
    op.create_index(
        op.f("ix_supplier_notification_outbox_supplier_offer_id"),
        "supplier_notification_outbox",
        ["supplier_offer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_supplier_notification_outbox_tour_id"),
        "supplier_notification_outbox",
        ["tour_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_supplier_notification_outbox_order_id"),
        "supplier_notification_outbox",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_supplier_notification_outbox_telegram_user_id"),
        "supplier_notification_outbox",
        ["telegram_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_supplier_notification_outbox_telegram_user_id"), table_name="supplier_notification_outbox")
    op.drop_index(op.f("ix_supplier_notification_outbox_order_id"), table_name="supplier_notification_outbox")
    op.drop_index(op.f("ix_supplier_notification_outbox_tour_id"), table_name="supplier_notification_outbox")
    op.drop_index(op.f("ix_supplier_notification_outbox_supplier_offer_id"), table_name="supplier_notification_outbox")
    op.drop_table("supplier_notification_outbox")
