"""create core mvp models

Revision ID: 20260326_01
Revises:
Create Date: 2026-03-26 16:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260326_01"
down_revision = None
branch_labels = None
depends_on = None


booking_status_enum = postgresql.ENUM(
    "new",
    "customer_question",
    "operator_question",
    "reserved",
    "confirmed",
    "ready_for_departure",
    "completed",
    "no_show",
    name="booking_status",
    create_type=False,
)

payment_status_enum = postgresql.ENUM(
    "unpaid",
    "awaiting_payment",
    "paid",
    "refunded",
    "partial_refund",
    name="payment_status",
    create_type=False,
)

cancellation_status_enum = postgresql.ENUM(
    "active",
    "cancelled_by_client",
    "cancelled_by_operator",
    "cancelled_no_payment",
    "moved_to_another_date",
    "moved_to_another_tour",
    "no_show",
    "duplicate",
    name="cancellation_status",
    create_type=False,
)

tour_status_enum = postgresql.ENUM(
    "draft",
    "open_for_sale",
    "collecting_group",
    "guaranteed",
    "sales_closed",
    "in_progress",
    "completed",
    "postponed",
    "cancelled",
    name="tour_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    booking_status_enum.create(bind, checkfirst=True)
    payment_status_enum.create(bind, checkfirst=True)
    cancellation_status_enum.create(bind, checkfirst=True)
    tour_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("preferred_language", sa.String(length=16), nullable=True),
        sa.Column("home_city", sa.String(length=255), nullable=True),
        sa.Column("source_channel", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "tours",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("title_default", sa.String(length=255), nullable=False),
        sa.Column("short_description_default", sa.Text(), nullable=True),
        sa.Column("full_description_default", sa.Text(), nullable=True),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("departure_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("return_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("base_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("seats_total", sa.Integer(), nullable=False),
        sa.Column("seats_available", sa.Integer(), nullable=False),
        sa.Column("sales_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", tour_status_enum, nullable=False, server_default="draft"),
        sa.Column("guaranteed_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("duration_days > 0", name="ck_tours_duration_days_positive"),
        sa.CheckConstraint("base_price >= 0", name="ck_tours_base_price_non_negative"),
        sa.CheckConstraint("seats_total >= 0", name="ck_tours_seats_total_non_negative"),
        sa.CheckConstraint("seats_available >= 0", name="ck_tours_seats_available_non_negative"),
        sa.CheckConstraint("seats_available <= seats_total", name="ck_tours_seats_available_le_total"),
    )

    op.create_table(
        "tour_translations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tour_id", sa.Integer(), sa.ForeignKey("tours.id", ondelete="CASCADE"), nullable=False),
        sa.Column("language_code", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("short_description", sa.Text(), nullable=True),
        sa.Column("full_description", sa.Text(), nullable=True),
        sa.Column("program_text", sa.Text(), nullable=True),
        sa.Column("included_text", sa.Text(), nullable=True),
        sa.Column("excluded_text", sa.Text(), nullable=True),
        sa.UniqueConstraint("tour_id", "language_code", name="uq_tour_translation_language"),
    )
    op.create_index(op.f("ix_tour_translations_tour_id"), "tour_translations", ["tour_id"], unique=False)

    op.create_table(
        "boarding_points",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tour_id", sa.Integer(), sa.ForeignKey("tours.id", ondelete="CASCADE"), nullable=False),
        sa.Column("city", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("time", sa.Time(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index(op.f("ix_boarding_points_tour_id"), "boarding_points", ["tour_id"], unique=False)

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tour_id", sa.Integer(), sa.ForeignKey("tours.id", ondelete="RESTRICT"), nullable=False),
        sa.Column(
            "boarding_point_id",
            sa.Integer(),
            sa.ForeignKey("boarding_points.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("seats_count", sa.Integer(), nullable=False),
        sa.Column("booking_status", booking_status_enum, nullable=False, server_default="new"),
        sa.Column("payment_status", payment_status_enum, nullable=False, server_default="unpaid"),
        sa.Column("cancellation_status", cancellation_status_enum, nullable=False, server_default="active"),
        sa.Column("reservation_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("source_channel", sa.String(length=64), nullable=True),
        sa.Column("assigned_operator_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("seats_count > 0", name="ck_orders_seats_count_positive"),
        sa.CheckConstraint("total_amount >= 0", name="ck_orders_total_amount_non_negative"),
    )
    op.create_index(op.f("ix_orders_user_id"), "orders", ["user_id"], unique=False)
    op.create_index(op.f("ix_orders_tour_id"), "orders", ["tour_id"], unique=False)
    op.create_index(op.f("ix_orders_boarding_point_id"), "orders", ["boarding_point_id"], unique=False)
    op.create_index(op.f("ix_orders_assigned_operator_id"), "orders", ["assigned_operator_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_orders_assigned_operator_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_boarding_point_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_tour_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_user_id"), table_name="orders")
    op.drop_table("orders")

    op.drop_index(op.f("ix_boarding_points_tour_id"), table_name="boarding_points")
    op.drop_table("boarding_points")

    op.drop_index(op.f("ix_tour_translations_tour_id"), table_name="tour_translations")
    op.drop_table("tour_translations")

    op.drop_table("tours")
    op.drop_table("users")

    bind = op.get_bind()
    tour_status_enum.drop(bind, checkfirst=True)
    cancellation_status_enum.drop(bind, checkfirst=True)
    payment_status_enum.drop(bind, checkfirst=True)
    booking_status_enum.drop(bind, checkfirst=True)
