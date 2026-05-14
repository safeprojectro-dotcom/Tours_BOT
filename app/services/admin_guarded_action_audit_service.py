"""B16D2A: orchestration for guarded admin action audit + idempotency (no business mutations)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.admin_guarded_action import AdminGuardedActionAttempt, AdminGuardedActionStep
from app.models.enums import AdminGuardedActionAttemptStatus, AdminGuardedActionStepStatus
from app.repositories.admin_guarded_action import AdminGuardedActionAttemptRepository, attempt_repository

# Reserved for future B16D2B — not used for mutations in B16D2A.
ACTION_PREPARE_CONVERSION_CHAIN = "prepare_conversion_chain"
SOURCE_ENTITY_SUPPLIER_OFFER = "supplier_offer"


class AdminGuardedActionAuditService:
    """Create and update audit/idempotency rows only."""

    def __init__(self, *, attempts: AdminGuardedActionAttemptRepository | None = None) -> None:
        self._attempts = attempts or attempt_repository

    def validate_idempotency_key(self, raw: str | None) -> str:
        key = (raw or "").strip()
        if not key:
            raise ValueError("idempotency_key is required and must be non-blank")
        return key

    def get_or_create_attempt(
        self,
        session: Session,
        *,
        action_code: str,
        source_entity_type: str,
        source_entity_id: int,
        idempotency_key: str,
        requested_by: str | None = None,
        dry_run: bool = False,
        extra: dict | None = None,
    ) -> tuple[AdminGuardedActionAttempt, bool]:
        key = self.validate_idempotency_key(idempotency_key)
        if source_entity_id < 1:
            raise ValueError("source_entity_id must be a positive integer")
        existing = self._attempts.get_by_idempotency(
            session,
            action_code=action_code,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            idempotency_key=key,
        )
        if existing is not None:
            return existing, False
        row = self._attempts.add_attempt(
            session,
            data={
                "action_code": action_code,
                "source_entity_type": source_entity_type,
                "source_entity_id": source_entity_id,
                "idempotency_key": key,
                "status": AdminGuardedActionAttemptStatus.PENDING.value,
                "requested_by": requested_by,
                "dry_run": dry_run,
                "extra": extra,
            },
        )
        return row, True

    def create_step(
        self,
        session: Session,
        *,
        attempt: AdminGuardedActionAttempt,
        step_code: str,
        step_order: int,
        detail: dict | None = None,
    ) -> AdminGuardedActionStep:
        if step_order < 1:
            raise ValueError("step_order must be >= 1")
        return self._attempts.add_step(
            session,
            data={
                "attempt_id": attempt.id,
                "step_code": step_code,
                "step_order": step_order,
                "status": AdminGuardedActionStepStatus.PENDING.value,
                "detail": detail,
            },
        )

    def set_step_running(self, session: Session, step: AdminGuardedActionStep) -> AdminGuardedActionStep:
        step.status = AdminGuardedActionStepStatus.RUNNING.value
        step.started_at = datetime.now(UTC)
        session.add(step)
        session.flush()
        session.refresh(step)
        return step

    def complete_step(
        self,
        session: Session,
        step: AdminGuardedActionStep,
        *,
        status: AdminGuardedActionStepStatus,
        error_code: str | None = None,
        error_message: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> AdminGuardedActionStep:
        step.status = status.value
        step.finished_at = datetime.now(UTC)
        step.error_code = error_code
        step.error_message = error_message
        if detail is not None:
            step.detail = detail
        session.add(step)
        session.flush()
        session.refresh(step)
        return step

    def set_attempt_status(
        self,
        session: Session,
        attempt: AdminGuardedActionAttempt,
        *,
        status: AdminGuardedActionAttemptStatus,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> AdminGuardedActionAttempt:
        attempt.status = status.value
        attempt.error_code = error_code
        attempt.error_message = error_message
        session.add(attempt)
        session.flush()
        session.refresh(attempt)
        return attempt
