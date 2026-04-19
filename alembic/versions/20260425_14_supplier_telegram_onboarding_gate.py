"""Y2.1: supplier Telegram identity binding + onboarding review gate.

Revision ID: 20260425_14
Revises: 20260424_13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260425_14"
down_revision = "20260424_13"
branch_labels = None
depends_on = None

supplier_onboarding_status = postgresql.ENUM(
    "pending_review",
    "approved",
    "rejected",
    name="supplier_onboarding_status",
)

supplier_service_composition = postgresql.ENUM(
    "transport_only",
    "transport_guide",
    "transport_water",
    "transport_guide_water",
    name="supplier_service_composition",
    create_type=False,
)


def upgrade() -> None:
    supplier_onboarding_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "suppliers",
        sa.Column(
            "primary_telegram_user_id",
            sa.BigInteger(),
            nullable=True,
        ),
    )
    op.add_column(
        "suppliers",
        sa.Column(
            "onboarding_status",
            supplier_onboarding_status,
            nullable=False,
            server_default="approved",
        ),
    )
    op.add_column("suppliers", sa.Column("onboarding_contact_info", sa.String(length=255), nullable=True))
    op.add_column("suppliers", sa.Column("onboarding_region", sa.String(length=255), nullable=True))
    op.add_column(
        "suppliers",
        sa.Column("onboarding_service_composition", supplier_service_composition, nullable=True),
    )
    op.add_column("suppliers", sa.Column("onboarding_fleet_summary", sa.Text(), nullable=True))
    op.add_column("suppliers", sa.Column("onboarding_rejection_reason", sa.Text(), nullable=True))
    op.add_column("suppliers", sa.Column("onboarding_submitted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("suppliers", sa.Column("onboarding_reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "ix_suppliers_primary_telegram_user_id",
        "suppliers",
        ["primary_telegram_user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_suppliers_primary_telegram_user_id", table_name="suppliers")
    op.drop_column("suppliers", "onboarding_reviewed_at")
    op.drop_column("suppliers", "onboarding_submitted_at")
    op.drop_column("suppliers", "onboarding_rejection_reason")
    op.drop_column("suppliers", "onboarding_fleet_summary")
    op.drop_column("suppliers", "onboarding_service_composition")
    op.drop_column("suppliers", "onboarding_region")
    op.drop_column("suppliers", "onboarding_contact_info")
    op.drop_column("suppliers", "onboarding_status")
    op.drop_column("suppliers", "primary_telegram_user_id")
    supplier_onboarding_status.drop(op.get_bind(), checkfirst=True)
