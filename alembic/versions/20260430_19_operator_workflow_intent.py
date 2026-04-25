"""Y37.4: additive operator workflow intent on custom_marketplace_requests.

Revision: 20260430_19
Revises: 20260429_18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260430_19"
down_revision = "20260429_18"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE operator_workflow_intent AS ENUM ('need_manual_followup')")
    op.add_column(
        "custom_marketplace_requests",
        sa.Column("operator_workflow_intent", postgresql.ENUM("need_manual_followup", name="operator_workflow_intent", create_type=False), nullable=True),
    )
    op.add_column(
        "custom_marketplace_requests",
        sa.Column("operator_workflow_intent_set_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "custom_marketplace_requests",
        sa.Column("operator_workflow_intent_set_by_user_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_cmr_operator_workflow_intent_set_by_user_id",
        "custom_marketplace_requests",
        "users",
        ["operator_workflow_intent_set_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_cmr_operator_workflow_intent_set_by_user_id", "custom_marketplace_requests", type_="foreignkey")
    op.drop_column("custom_marketplace_requests", "operator_workflow_intent_set_by_user_id")
    op.drop_column("custom_marketplace_requests", "operator_workflow_intent_set_at")
    op.drop_column("custom_marketplace_requests", "operator_workflow_intent")
    op.execute("DROP TYPE operator_workflow_intent")
