"""B16D2A: persistence for generic guarded admin actions (audit + idempotency only)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class AdminGuardedActionAttempt(TimestampMixin, Base):
    """One operator/API invocation of a guarded action, keyed for idempotent replay."""

    __tablename__ = "admin_guarded_action_attempts"
    __table_args__ = (
        UniqueConstraint(
            "action_code",
            "source_entity_type",
            "source_entity_id",
            "idempotency_key",
            name="uq_admin_guarded_action_attempt_idempotency",
        ),
        CheckConstraint("source_entity_id > 0", name="ck_admin_guarded_action_attempts_source_entity_id_positive"),
        CheckConstraint(
            "char_length(btrim(idempotency_key::text)) > 0",
            name="ck_admin_guarded_action_attempts_idempotency_key_nonempty",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    action_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_entity_id: Mapped[int] = mapped_column(nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="pending")
    requested_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    dry_run: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default="false")
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    steps: Mapped[list[AdminGuardedActionStep]] = relationship(
        "AdminGuardedActionStep",
        back_populates="attempt",
        cascade="all, delete-orphan",
        order_by="AdminGuardedActionStep.step_order",
    )


class AdminGuardedActionStep(Base):
    """Sub-step row for a guarded action attempt (e.g. bridge / catalog / execution link)."""

    __tablename__ = "admin_guarded_action_steps"
    __table_args__ = (
        UniqueConstraint("attempt_id", "step_order", name="uq_admin_guarded_action_steps_attempt_order"),
        CheckConstraint("step_order >= 1", name="ck_admin_guarded_action_steps_step_order_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("admin_guarded_action_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_code: Mapped[str] = mapped_column(String(64), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer(), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="pending")
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    attempt: Mapped[AdminGuardedActionAttempt] = relationship("AdminGuardedActionAttempt", back_populates="steps")
