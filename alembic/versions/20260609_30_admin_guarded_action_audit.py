"""B16D2A: admin guarded action attempts + steps — audit/idempotency only (no business mutations).

Revision: 20260609_30
Revises: 20260531_29
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260609_30"
down_revision = "20260531_29"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_guarded_action_attempts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("action_code", sa.String(length=64), nullable=False),
        sa.Column("source_entity_type", sa.String(length=64), nullable=False),
        sa.Column("source_entity_id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("requested_by", sa.String(length=256), nullable=True),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("source_entity_id > 0", name="ck_admin_guarded_action_attempts_source_entity_id_positive"),
        sa.CheckConstraint(
            "char_length(btrim(idempotency_key::text)) > 0",
            name="ck_admin_guarded_action_attempts_idempotency_key_nonempty",
        ),
        sa.UniqueConstraint(
            "action_code",
            "source_entity_type",
            "source_entity_id",
            "idempotency_key",
            name="uq_admin_guarded_action_attempt_idempotency",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_admin_guarded_action_attempts_source_entity_id"),
        "admin_guarded_action_attempts",
        ["source_entity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_admin_guarded_action_attempts_action_code"),
        "admin_guarded_action_attempts",
        ["action_code"],
        unique=False,
    )

    op.create_table(
        "admin_guarded_action_steps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("step_code", sa.String(length=64), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("detail", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["admin_guarded_action_attempts.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("step_order >= 1", name="ck_admin_guarded_action_steps_step_order_positive"),
        sa.UniqueConstraint(
            "attempt_id",
            "step_order",
            name="uq_admin_guarded_action_steps_attempt_order",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_admin_guarded_action_steps_attempt_id"),
        "admin_guarded_action_steps",
        ["attempt_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_guarded_action_steps_attempt_id"), table_name="admin_guarded_action_steps")
    op.drop_table("admin_guarded_action_steps")
    op.drop_index(op.f("ix_admin_guarded_action_attempts_action_code"), table_name="admin_guarded_action_attempts")
    op.drop_index(op.f("ix_admin_guarded_action_attempts_source_entity_id"), table_name="admin_guarded_action_attempts")
    op.drop_table("admin_guarded_action_attempts")
