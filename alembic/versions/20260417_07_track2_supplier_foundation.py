"""Track 2: supplier domain + supplier offers (Layer B extension; core tours unchanged).

Revision ID: 20260417_07
Revises: 20260416_06
Create Date: 2026-04-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260417_07"
down_revision = "20260416_06"
branch_labels = None
depends_on = None

supplier_service_composition = postgresql.ENUM(
    "transport_only",
    "transport_guide",
    "transport_water",
    "transport_guide_water",
    name="supplier_service_composition",
    create_type=False,
)

supplier_offer_payment_mode = postgresql.ENUM(
    "platform_checkout",
    "assisted_closure",
    name="supplier_offer_payment_mode",
    create_type=False,
)

supplier_offer_lifecycle = postgresql.ENUM(
    "draft",
    "ready_for_moderation",
    name="supplier_offer_lifecycle",
    create_type=False,
)

tour_sales_mode = postgresql.ENUM(
    "per_seat",
    "full_bus",
    name="tour_sales_mode",
    create_type=False,
)

supplier_service_composition_create = postgresql.ENUM(
    "transport_only",
    "transport_guide",
    "transport_water",
    "transport_guide_water",
    name="supplier_service_composition",
    create_type=True,
)

supplier_offer_payment_mode_create = postgresql.ENUM(
    "platform_checkout",
    "assisted_closure",
    name="supplier_offer_payment_mode",
    create_type=True,
)

supplier_offer_lifecycle_create = postgresql.ENUM(
    "draft",
    "ready_for_moderation",
    name="supplier_offer_lifecycle",
    create_type=True,
)


def upgrade() -> None:
    bind = op.get_bind()
    supplier_service_composition_create.create(bind, checkfirst=True)
    supplier_offer_payment_mode_create.create(bind, checkfirst=True)
    supplier_offer_lifecycle_create.create(bind, checkfirst=True)

    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("code", name="uq_suppliers_code"),
    )

    op.create_table(
        "supplier_api_credentials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("token_hash", name="uq_supplier_api_credentials_token_hash"),
    )
    op.create_index(
        op.f("ix_supplier_api_credentials_supplier_id"),
        "supplier_api_credentials",
        ["supplier_id"],
        unique=False,
    )

    op.create_table(
        "supplier_offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_reference", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("program_text", sa.Text(), nullable=True),
        sa.Column("departure_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("return_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("transport_notes", sa.Text(), nullable=True),
        sa.Column("vehicle_label", sa.String(length=128), nullable=True),
        sa.Column("seats_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("base_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True),
        sa.Column(
            "service_composition",
            supplier_service_composition,
            nullable=False,
            server_default="transport_only",
        ),
        sa.Column("sales_mode", tour_sales_mode, nullable=False, server_default="per_seat"),
        sa.Column(
            "payment_mode",
            supplier_offer_payment_mode,
            nullable=False,
            server_default="platform_checkout",
        ),
        sa.Column(
            "lifecycle_status",
            supplier_offer_lifecycle,
            nullable=False,
            server_default="draft",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("seats_total >= 0", name="ck_supplier_offers_seats_total_non_negative"),
        sa.CheckConstraint(
            "base_price IS NULL OR base_price >= 0",
            name="ck_supplier_offers_base_price_non_negative",
        ),
    )
    op.create_index(op.f("ix_supplier_offers_supplier_id"), "supplier_offers", ["supplier_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_supplier_offers_supplier_id"), table_name="supplier_offers")
    op.drop_table("supplier_offers")

    op.drop_index(op.f("ix_supplier_api_credentials_supplier_id"), table_name="supplier_api_credentials")
    op.drop_table("supplier_api_credentials")

    op.drop_table("suppliers")

    bind = op.get_bind()
    supplier_offer_lifecycle_create.drop(bind, checkfirst=True)
    supplier_offer_payment_mode_create.drop(bind, checkfirst=True)
    supplier_service_composition_create.drop(bind, checkfirst=True)
