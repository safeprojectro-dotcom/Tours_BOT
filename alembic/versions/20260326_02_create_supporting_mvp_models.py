"""create supporting mvp models

Revision ID: 20260326_02
Revises: 20260326_01
Create Date: 2026-03-26 16:50:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260326_02"
down_revision = "20260326_01"
branch_labels = None
depends_on = None


payment_status_enum = postgresql.ENUM(
    "unpaid",
    "awaiting_payment",
    "paid",
    "refunded",
    "partial_refund",
    name="payment_status",
    create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("external_payment_id", sa.String(length=255), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("status", payment_status_enum, nullable=False, server_default="unpaid"),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("amount >= 0", name="ck_payments_amount_non_negative"),
        sa.UniqueConstraint("provider", "external_payment_id", name="uq_payments_provider_external_payment_id"),
    )
    op.create_index(op.f("ix_payments_order_id"), "payments", ["order_id"], unique=False)

    op.create_table(
        "waitlist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tour_id", sa.Integer(), sa.ForeignKey("tours.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seats_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("seats_count > 0", name="ck_waitlist_seats_count_positive"),
        sa.UniqueConstraint("user_id", "tour_id", "status", name="uq_waitlist_user_tour_status"),
    )
    op.create_index(op.f("ix_waitlist_user_id"), "waitlist", ["user_id"], unique=False)
    op.create_index(op.f("ix_waitlist_tour_id"), "waitlist", ["tour_id"], unique=False)

    op.create_table(
        "handoffs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("assigned_operator_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(op.f("ix_handoffs_user_id"), "handoffs", ["user_id"], unique=False)
    op.create_index(op.f("ix_handoffs_order_id"), "handoffs", ["order_id"], unique=False)
    op.create_index(op.f("ix_handoffs_assigned_operator_id"), "handoffs", ["assigned_operator_id"], unique=False)

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chat_type", sa.String(length=32), nullable=False),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=False),
        sa.Column("direction", sa.String(length=32), nullable=False),
        sa.Column("language_code", sa.String(length=16), nullable=True),
        sa.Column("intent", sa.String(length=64), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(op.f("ix_messages_user_id"), "messages", ["user_id"], unique=False)
    op.create_index(op.f("ix_messages_telegram_chat_id"), "messages", ["telegram_chat_id"], unique=False)

    op.create_table(
        "content_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tour_id", sa.Integer(), sa.ForeignKey("tours.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel_type", sa.String(length=32), nullable=False),
        sa.Column("language_code", sa.String(length=16), nullable=False),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("media_path", sa.String(length=1024), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("title IS NOT NULL OR body IS NOT NULL", name="ck_content_items_title_or_body_present"),
    )
    op.create_index(op.f("ix_content_items_tour_id"), "content_items", ["tour_id"], unique=False)
    op.create_index(op.f("ix_content_items_approved_by"), "content_items", ["approved_by"], unique=False)

    op.create_table(
        "knowledge_base",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("language_code", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(op.f("ix_knowledge_base_category"), "knowledge_base", ["category"], unique=False)
    op.create_index(op.f("ix_knowledge_base_language_code"), "knowledge_base", ["language_code"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_knowledge_base_language_code"), table_name="knowledge_base")
    op.drop_index(op.f("ix_knowledge_base_category"), table_name="knowledge_base")
    op.drop_table("knowledge_base")

    op.drop_index(op.f("ix_content_items_approved_by"), table_name="content_items")
    op.drop_index(op.f("ix_content_items_tour_id"), table_name="content_items")
    op.drop_table("content_items")

    op.drop_index(op.f("ix_messages_telegram_chat_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_user_id"), table_name="messages")
    op.drop_table("messages")

    op.drop_index(op.f("ix_handoffs_assigned_operator_id"), table_name="handoffs")
    op.drop_index(op.f("ix_handoffs_order_id"), table_name="handoffs")
    op.drop_index(op.f("ix_handoffs_user_id"), table_name="handoffs")
    op.drop_table("handoffs")

    op.drop_index(op.f("ix_waitlist_tour_id"), table_name="waitlist")
    op.drop_index(op.f("ix_waitlist_user_id"), table_name="waitlist")
    op.drop_table("waitlist")

    op.drop_index(op.f("ix_payments_order_id"), table_name="payments")
    op.drop_table("payments")
