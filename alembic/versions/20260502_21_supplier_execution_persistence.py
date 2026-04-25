"""Y43: supplier execution request + attempt tables (Y41) — persistence only, no execution runtime.

Revision: 20260502_21
Revises: 20260501_20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260502_21"
down_revision = "20260501_20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE supplier_execution_source_entry_point AS ENUM ("
        "'admin_explicit', 'scheduled_job', 'external_webhook', 'operator_do_action'"
        ")"
    )
    op.execute("CREATE TYPE supplier_execution_source_entity_type AS ENUM ('custom_marketplace_request')")
    op.execute(
        "CREATE TYPE supplier_execution_request_status AS ENUM ("
        "'pending', 'validated', 'blocked', 'attempted', 'succeeded', 'failed', 'cancelled'"
        ")"
    )
    op.execute(
        "CREATE TYPE supplier_execution_attempt_channel AS ENUM ("
        "'telegram', 'email', 'partner_api', 'internal', 'none'"
        ")"
    )
    op.execute(
        "CREATE TYPE supplier_execution_attempt_status AS ENUM ("
        "'pending', 'succeeded', 'failed', 'skipped'"
        ")"
    )

    se_source_entry = postgresql.ENUM(
        "admin_explicit",
        "scheduled_job",
        "external_webhook",
        "operator_do_action",
        name="supplier_execution_source_entry_point",
        create_type=False,
    )
    se_source_entity = postgresql.ENUM("custom_marketplace_request", name="supplier_execution_source_entity_type", create_type=False)
    se_req_status = postgresql.ENUM(
        "pending",
        "validated",
        "blocked",
        "attempted",
        "succeeded",
        "failed",
        "cancelled",
        name="supplier_execution_request_status",
        create_type=False,
    )
    se_attempt_ch = postgresql.ENUM(
        "telegram",
        "email",
        "partner_api",
        "internal",
        "none",
        name="supplier_execution_attempt_channel",
        create_type=False,
    )
    se_attempt_st = postgresql.ENUM(
        "pending",
        "succeeded",
        "failed",
        "skipped",
        name="supplier_execution_attempt_status",
        create_type=False,
    )
    opf = postgresql.ENUM("need_manual_followup", "need_supplier_offer", name="operator_workflow_intent", create_type=False)

    op.create_table(
        "supplier_execution_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_entry_point", se_source_entry, nullable=False),
        sa.Column("source_entity_type", se_source_entity, nullable=False),
        sa.Column("source_entity_id", sa.Integer(), nullable=False),
        sa.Column("operator_workflow_intent_snapshot", opf, nullable=True),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=True),
        sa.Column("status", se_req_status, nullable=False, server_default="pending"),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("raw_response_reference", sa.String(length=512), nullable=True),
        sa.Column("audit_notes", sa.Text(), nullable=True),
        sa.Column("validation_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("source_entity_id > 0", name="ck_supplier_execution_requests_source_entity_id_positive"),
        sa.CheckConstraint("char_length(btrim(idempotency_key::text)) > 0", name="ck_supplier_execution_requests_idempotency_key_nonempty"),
        sa.ForeignKeyConstraint(
            ["requested_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["completed_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_supplier_execution_requests_idempotency_key"),
    )
    op.create_index("ix_supplier_execution_requests_source_entity", "supplier_execution_requests", ["source_entity_id"])
    op.create_index("ix_supplier_execution_requests_requested_by", "supplier_execution_requests", ["requested_by_user_id"])

    op.create_table(
        "supplier_execution_attempts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("execution_request_id", sa.Integer(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("channel_type", se_attempt_ch, nullable=False),
        sa.Column("target_supplier_ref", sa.String(length=128), nullable=True),
        sa.Column("status", se_attempt_st, nullable=False),
        sa.Column("provider_reference", sa.String(length=256), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("attempt_number >= 1", name="ck_supplier_execution_attempts_attempt_number_positive"),
        sa.ForeignKeyConstraint(
            ["execution_request_id"],
            ["supplier_execution_requests.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "execution_request_id",
            "attempt_number",
            name="uq_supplier_execution_attempts_request_attempt",
        ),
    )
    op.create_index("ix_supplier_execution_attempts_request_id", "supplier_execution_attempts", ["execution_request_id"])


def downgrade() -> None:
    op.drop_index("ix_supplier_execution_attempts_request_id", table_name="supplier_execution_attempts")
    op.drop_table("supplier_execution_attempts")
    op.drop_index("ix_supplier_execution_requests_requested_by", table_name="supplier_execution_requests")
    op.drop_index("ix_supplier_execution_requests_source_entity", table_name="supplier_execution_requests")
    op.drop_table("supplier_execution_requests")

    op.execute("DROP TYPE IF EXISTS supplier_execution_attempt_status")
    op.execute("DROP TYPE IF EXISTS supplier_execution_attempt_channel")
    op.execute("DROP TYPE IF EXISTS supplier_execution_request_status")
    op.execute("DROP TYPE IF EXISTS supplier_execution_source_entity_type")
    op.execute("DROP TYPE IF EXISTS supplier_execution_source_entry_point")
