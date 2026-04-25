"""Y43: persistence-only helpers for supplier execution — Y42 fail-closed validation, no execution runtime."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import (
    OperatorWorkflowIntent,
    SupplierExecutionAttemptChannel,
    SupplierExecutionAttemptStatus,
    SupplierExecutionRequestStatus,
    SupplierExecutionSourceEntityType,
    SupplierExecutionSourceEntryPoint,
)
from app.models.supplier_execution import SupplierExecutionAttempt, SupplierExecutionRequest


def _strip(s: str | None) -> str:
    return (s or "").strip()


def validate_new_execution_request(
    *,
    idempotency_key: str,
    source_entity_id: int,
) -> None:
    """Fail-closed checks before creating a request row (Y42)."""
    if not _strip(idempotency_key):
        raise ValueError("idempotency_key is required and must be non-blank")
    if source_entity_id is None or int(source_entity_id) < 1:
        raise ValueError("source_entity_id must be a positive integer")


def build_execution_request(
    *,
    source_entry_point: SupplierExecutionSourceEntryPoint,
    source_entity_type: SupplierExecutionSourceEntityType,
    source_entity_id: int,
    idempotency_key: str,
    status: SupplierExecutionRequestStatus = SupplierExecutionRequestStatus.PENDING,
    requested_by_user_id: int | None = None,
    operator_workflow_intent_snapshot: OperatorWorkflowIntent | None = None,
) -> SupplierExecutionRequest:
    """Construct a `SupplierExecutionRequest` without I/O. Call `validate_new_execution_request` first."""
    return SupplierExecutionRequest(
        source_entry_point=source_entry_point,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
        idempotency_key=_strip(idempotency_key),
        status=status,
        requested_by_user_id=requested_by_user_id,
        operator_workflow_intent_snapshot=operator_workflow_intent_snapshot,
    )


def add_execution_request(session: Session, request: SupplierExecutionRequest) -> SupplierExecutionRequest:
    """Insert after validation. Does not start execution."""
    validate_new_execution_request(
        idempotency_key=request.idempotency_key,
        source_entity_id=request.source_entity_id,
    )
    session.add(request)
    session.flush()
    session.refresh(request)
    return request


def build_execution_attempt(
    *,
    execution_request_id: int,
    attempt_number: int,
    channel_type: SupplierExecutionAttemptChannel,
    status: SupplierExecutionAttemptStatus,
    target_supplier_ref: str | None = None,
    provider_reference: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
    created_at: datetime | None = None,
) -> SupplierExecutionAttempt:
    if execution_request_id is None or int(execution_request_id) < 1:
        raise ValueError("execution_request_id must be a positive integer")
    if attempt_number is None or int(attempt_number) < 1:
        raise ValueError("attempt_number must be >= 1")
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    return SupplierExecutionAttempt(
        execution_request_id=execution_request_id,
        attempt_number=attempt_number,
        channel_type=channel_type,
        status=status,
        target_supplier_ref=target_supplier_ref,
        provider_reference=provider_reference,
        error_code=error_code,
        error_message=error_message,
        created_at=created_at,
    )


def add_execution_attempt(session: Session, attempt: SupplierExecutionAttempt) -> SupplierExecutionAttempt:
    session.add(attempt)
    session.flush()
    session.refresh(attempt)
    return attempt


def next_attempt_number_for_request(session: Session, *, execution_request_id: int) -> int:
    """Next 1-based attempt_number for this execution request (Y48). Fails if request has no row yet; caller validates."""
    m = session.scalar(
        select(func.coalesce(func.max(SupplierExecutionAttempt.attempt_number), 0)).where(
            SupplierExecutionAttempt.execution_request_id == int(execution_request_id),
        ),
    )
    return int(m or 0) + 1
