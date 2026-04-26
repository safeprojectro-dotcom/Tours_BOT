"""Y43: supplier execution persistence — Y41 data contract, no runtime execution or messaging."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    OperatorWorkflowIntent,
    SupplierExecutionAttemptChannel,
    SupplierExecutionAttemptStatus,
    SupplierExecutionRequestStatus,
    SupplierExecutionSourceEntityType,
    SupplierExecutionSourceEntryPoint,
    sqlalchemy_enum,
)
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class SupplierExecutionRequest(TimestampMixin, Base):
    """Y41 execution request: audit anchor for a future supplier-impacting run; intent here is snapshot only."""

    __tablename__ = "supplier_execution_requests"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_supplier_execution_requests_idempotency_key"),
        CheckConstraint("source_entity_id > 0", name="ck_supplier_execution_requests_source_entity_id_positive"),
        CheckConstraint("char_length(btrim(idempotency_key::text)) > 0", name="ck_supplier_execution_requests_idempotency_key_nonempty"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_entry_point: Mapped[SupplierExecutionSourceEntryPoint] = mapped_column(
        sqlalchemy_enum(SupplierExecutionSourceEntryPoint, name="supplier_execution_source_entry_point"),
        nullable=False,
    )
    source_entity_type: Mapped[SupplierExecutionSourceEntityType] = mapped_column(
        sqlalchemy_enum(SupplierExecutionSourceEntityType, name="supplier_execution_source_entity_type"),
        nullable=False,
    )
    source_entity_id: Mapped[int] = mapped_column(nullable=False, index=True)
    operator_workflow_intent_snapshot: Mapped[OperatorWorkflowIntent | None] = mapped_column(
        sqlalchemy_enum(OperatorWorkflowIntent, name="operator_workflow_intent"),
        nullable=True,
    )
    requested_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[SupplierExecutionRequestStatus] = mapped_column(
        sqlalchemy_enum(SupplierExecutionRequestStatus, name="supplier_execution_request_status"),
        nullable=False,
        default=SupplierExecutionRequestStatus.PENDING,
    )
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    raw_response_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)
    audit_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    requested_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[requested_by_user_id],
    )
    completed_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[completed_by_user_id],
    )
    attempts: Mapped[list[SupplierExecutionAttempt]] = relationship(
        "SupplierExecutionAttempt",
        back_populates="execution_request",
        cascade="all, delete-orphan",
    )


class SupplierExecutionAttempt(Base):
    """Y41 attempt row — no outbound I/O in Y43; persistence only."""

    __tablename__ = "supplier_execution_attempts"
    __table_args__ = (
        UniqueConstraint(
            "execution_request_id",
            "attempt_number",
            name="uq_supplier_execution_attempts_request_attempt",
        ),
        CheckConstraint("attempt_number >= 1", name="ck_supplier_execution_attempts_attempt_number_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    execution_request_id: Mapped[int] = mapped_column(
        ForeignKey("supplier_execution_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(nullable=False)
    channel_type: Mapped[SupplierExecutionAttemptChannel] = mapped_column(
        sqlalchemy_enum(SupplierExecutionAttemptChannel, name="supplier_execution_attempt_channel"),
        nullable=False,
    )
    target_supplier_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[SupplierExecutionAttemptStatus] = mapped_column(
        sqlalchemy_enum(SupplierExecutionAttemptStatus, name="supplier_execution_attempt_status"),
        nullable=False,
    )
    provider_reference: Mapped[str | None] = mapped_column(String(256), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    execution_request: Mapped[SupplierExecutionRequest] = relationship(
        "SupplierExecutionRequest",
        back_populates="attempts",
    )


class SupplierExecutionAttemptTelegramIdempotency(Base):
    """Y50: one row per successful (attempt_id, idempotency_key) to block duplicate Telegram sends on replay."""

    __tablename__ = "supplier_execution_attempt_telegram_idempotency"
    __table_args__ = (
        UniqueConstraint(
            "supplier_execution_attempt_id",
            "idempotency_key",
            name="uq_ser_tg_idem_attempt_key",
        ),
        CheckConstraint(
            "char_length(btrim(idempotency_key::text)) > 0",
            name="ck_ser_tg_idem_key_nonempty",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    supplier_execution_attempt_id: Mapped[int] = mapped_column(
        ForeignKey("supplier_execution_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
