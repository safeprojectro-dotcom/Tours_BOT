"""B10: supplier offer → tour bridge (explicit admin; no auto-publish, no execution link)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260529_27"
down_revision = "20260528_26"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_offer_tour_bridges",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("supplier_offer_id", sa.Integer(), sa.ForeignKey("supplier_offers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tour_id", sa.Integer(), sa.ForeignKey("tours.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("bridge_kind", sa.String(length=32), nullable=False),
        sa.Column("created_by", sa.String(length=256), nullable=True),
        sa.Column("source_packaging_status", sa.String(length=64), nullable=False),
        sa.Column("source_lifecycle_status", sa.String(length=64), nullable=False),
        sa.Column("packaging_snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('active', 'superseded', 'cancelled')", name="ck_sotb_status"),
        sa.CheckConstraint(
            "bridge_kind IN ('created_new_tour', 'linked_existing_tour')",
            name="ck_sotb_bridge_kind",
        ),
    )
    op.create_index("ix_supplier_offer_tour_bridges_supplier_offer_id", "supplier_offer_tour_bridges", ["supplier_offer_id"])
    op.create_index("ix_supplier_offer_tour_bridges_tour_id", "supplier_offer_tour_bridges", ["tour_id"])
    op.create_index("ix_supplier_offer_tour_bridges_status", "supplier_offer_tour_bridges", ["status"])
    op.create_index(
        "uq_sotb_one_active_per_offer",
        "supplier_offer_tour_bridges",
        ["supplier_offer_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("uq_sotb_one_active_per_offer", table_name="supplier_offer_tour_bridges")
    op.drop_index("ix_supplier_offer_tour_bridges_status", table_name="supplier_offer_tour_bridges")
    op.drop_index("ix_supplier_offer_tour_bridges_tour_id", table_name="supplier_offer_tour_bridges")
    op.drop_index("ix_supplier_offer_tour_bridges_supplier_offer_id", table_name="supplier_offer_tour_bridges")
    op.drop_table("supplier_offer_tour_bridges")
