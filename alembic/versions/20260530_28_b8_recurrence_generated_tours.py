"""B8: audit rows for draft tours generated from a supplier offer template (no bridge, no auto-activate)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260530_28"
down_revision = "20260529_27"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_offer_recurrence_generated_tours",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "source_supplier_offer_id",
            sa.Integer(),
            sa.ForeignKey("supplier_offers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tour_id", sa.Integer(), sa.ForeignKey("tours.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("sequence_index >= 0", name="ck_sorgt_sequence_non_negative"),
    )
    op.create_index(
        "ix_sorgt_source_supplier_offer_id",
        "supplier_offer_recurrence_generated_tours",
        ["source_supplier_offer_id"],
    )
    op.create_index("ix_sorgt_tour_id", "supplier_offer_recurrence_generated_tours", ["tour_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_sorgt_tour_id", table_name="supplier_offer_recurrence_generated_tours")
    op.drop_index("ix_sorgt_source_supplier_offer_id", table_name="supplier_offer_recurrence_generated_tours")
    op.drop_table("supplier_offer_recurrence_generated_tours")
