"""add notification outbox

Revision ID: 20260327_03
Revises: 20260326_02
Create Date: 2026-03-27 20:35:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260327_03"
down_revision = "20260326_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_outbox",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dispatch_key", sa.String(length=255), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("language_code", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("dispatch_key", name="uq_notification_outbox_dispatch_key"),
    )
    op.create_index(op.f("ix_notification_outbox_order_id"), "notification_outbox", ["order_id"], unique=False)
    op.create_index(op.f("ix_notification_outbox_user_id"), "notification_outbox", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_notification_outbox_telegram_user_id"),
        "notification_outbox",
        ["telegram_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_notification_outbox_telegram_user_id"), table_name="notification_outbox")
    op.drop_index(op.f("ix_notification_outbox_user_id"), table_name="notification_outbox")
    op.drop_index(op.f("ix_notification_outbox_order_id"), table_name="notification_outbox")
    op.drop_table("notification_outbox")
