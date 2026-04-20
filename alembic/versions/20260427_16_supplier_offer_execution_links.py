"""Y27.1: explicit supplier offer execution linkage persistence.

Revision ID: 20260427_16
Revises: 20260426_15
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260427_16"
down_revision = "20260426_15"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_offer_execution_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("supplier_offer_id", sa.Integer(), sa.ForeignKey("supplier_offers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tour_id", sa.Integer(), sa.ForeignKey("tours.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("link_status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("close_reason", sa.String(length=32), nullable=True),
        sa.Column("link_note", sa.Text(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("link_status IN ('active', 'closed')", name="ck_supplier_offer_exec_links_status"),
        sa.CheckConstraint(
            "close_reason IS NULL OR close_reason IN ('replaced', 'unlinked', 'retracted', 'invalidated')",
            name="ck_supplier_offer_exec_links_close_reason",
        ),
        sa.CheckConstraint(
            "("
            "(link_status = 'active' AND closed_at IS NULL AND close_reason IS NULL)"
            " OR "
            "(link_status = 'closed' AND closed_at IS NOT NULL)"
            ")",
            name="ck_supplier_offer_exec_links_active_closed_consistency",
        ),
    )
    op.create_index(
        "ix_supplier_offer_execution_links_supplier_offer_id",
        "supplier_offer_execution_links",
        ["supplier_offer_id"],
        unique=False,
    )
    op.create_index(
        "ix_supplier_offer_execution_links_tour_id",
        "supplier_offer_execution_links",
        ["tour_id"],
        unique=False,
    )
    op.create_index(
        "uq_supplier_offer_execution_links_active_offer",
        "supplier_offer_execution_links",
        ["supplier_offer_id"],
        unique=True,
        postgresql_where=sa.text("link_status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("uq_supplier_offer_execution_links_active_offer", table_name="supplier_offer_execution_links")
    op.drop_index("ix_supplier_offer_execution_links_tour_id", table_name="supplier_offer_execution_links")
    op.drop_index("ix_supplier_offer_execution_links_supplier_offer_id", table_name="supplier_offer_execution_links")
    op.drop_table("supplier_offer_execution_links")
