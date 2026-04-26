"""B2: supplier_offer extended intake + packaging storage (no AI, no Tour, no publish logic).

Revision: 20260526_24
Revises: 20260526_23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260526_24"
down_revision = "20260526_23"
branch_labels = None
depends_on = None


def upgrade() -> None:
    packaging_status = postgresql.ENUM(
        "none",
        "packaging_pending",
        "packaging_generated",
        "needs_admin_review",
        "approved_for_publish",
        name="supplier_offer_packaging_status",
    )
    packaging_status.create(op.get_bind(), checkfirst=True)

    op.add_column("supplier_offers", sa.Column("cover_media_reference", sa.String(length=1024), nullable=True))
    op.add_column("supplier_offers", sa.Column("media_references", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("supplier_offers", sa.Column("included_text", sa.Text(), nullable=True))
    op.add_column("supplier_offers", sa.Column("excluded_text", sa.Text(), nullable=True))
    op.add_column("supplier_offers", sa.Column("short_hook", sa.String(length=512), nullable=True))
    op.add_column("supplier_offers", sa.Column("marketing_summary", sa.Text(), nullable=True))
    op.add_column("supplier_offers", sa.Column("discount_code", sa.String(length=64), nullable=True))
    op.add_column("supplier_offers", sa.Column("discount_percent", sa.Numeric(5, 2), nullable=True))
    op.add_column("supplier_offers", sa.Column("discount_amount", sa.Numeric(10, 2), nullable=True))
    op.add_column("supplier_offers", sa.Column("discount_valid_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("supplier_offers", sa.Column("recurrence_type", sa.String(length=64), nullable=True))
    op.add_column("supplier_offers", sa.Column("recurrence_rule", sa.Text(), nullable=True))
    op.add_column("supplier_offers", sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True))
    op.add_column("supplier_offers", sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("supplier_offers", sa.Column("supplier_admin_notes", sa.Text(), nullable=True))
    op.add_column("supplier_offers", sa.Column("admin_internal_notes", sa.Text(), nullable=True))
    op.add_column(
        "supplier_offers",
        sa.Column(
            "packaging_status",
            postgresql.ENUM(
                "none",
                "packaging_pending",
                "packaging_generated",
                "needs_admin_review",
                "approved_for_publish",
                name="supplier_offer_packaging_status",
                create_type=False,
            ),
            server_default=sa.text("'none'::supplier_offer_packaging_status"),
            nullable=False,
        ),
    )
    op.add_column("supplier_offers", sa.Column("missing_fields_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("supplier_offers", sa.Column("quality_warnings_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.create_check_constraint(
        "ck_supplier_offers_discount_amount_non_negative",
        "supplier_offers",
        "discount_amount IS NULL OR discount_amount >= 0",
    )
    op.create_check_constraint(
        "ck_supplier_offers_discount_percent_range",
        "supplier_offers",
        "discount_percent IS NULL OR (discount_percent >= 0 AND discount_percent <= 100)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_supplier_offers_discount_percent_range", "supplier_offers", type_="check")
    op.drop_constraint("ck_supplier_offers_discount_amount_non_negative", "supplier_offers", type_="check")
    op.drop_column("supplier_offers", "quality_warnings_json")
    op.drop_column("supplier_offers", "missing_fields_json")
    op.drop_column("supplier_offers", "packaging_status")
    op.drop_column("supplier_offers", "admin_internal_notes")
    op.drop_column("supplier_offers", "supplier_admin_notes")
    op.drop_column("supplier_offers", "valid_until")
    op.drop_column("supplier_offers", "valid_from")
    op.drop_column("supplier_offers", "recurrence_rule")
    op.drop_column("supplier_offers", "recurrence_type")
    op.drop_column("supplier_offers", "discount_valid_until")
    op.drop_column("supplier_offers", "discount_amount")
    op.drop_column("supplier_offers", "discount_percent")
    op.drop_column("supplier_offers", "discount_code")
    op.drop_column("supplier_offers", "marketing_summary")
    op.drop_column("supplier_offers", "short_hook")
    op.drop_column("supplier_offers", "excluded_text")
    op.drop_column("supplier_offers", "included_text")
    op.drop_column("supplier_offers", "media_references")
    op.drop_column("supplier_offers", "cover_media_reference")
    op.execute(sa.text("DROP TYPE IF EXISTS supplier_offer_packaging_status"))
