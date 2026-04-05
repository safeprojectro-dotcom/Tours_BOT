"""add boarding_point_translations table

Revision ID: 20260405_05
Revises: 20260405_04
Create Date: 2026-04-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260405_05"
down_revision = "20260405_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "boarding_point_translations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("boarding_point_id", sa.Integer(), nullable=False),
        sa.Column("language_code", sa.String(length=16), nullable=False),
        sa.Column("city", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["boarding_point_id"], ["boarding_points.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("boarding_point_id", "language_code", name="uq_boarding_point_translation_language"),
    )
    op.create_index(
        "ix_boarding_point_translations_boarding_point_id",
        "boarding_point_translations",
        ["boarding_point_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_boarding_point_translations_boarding_point_id", table_name="boarding_point_translations")
    op.drop_table("boarding_point_translations")
