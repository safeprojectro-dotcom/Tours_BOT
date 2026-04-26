"""Y44: read-only admin queries for supplier execution records — no writes, no execution. Y52: messaging audit on attempt reads."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import (
    SupplierExecutionAttemptChannel,
    SupplierExecutionRequestStatus,
    SupplierExecutionSourceEntityType,
)
from app.models.supplier_execution import (
    SupplierExecutionAttempt,
    SupplierExecutionAttemptTelegramIdempotency,
    SupplierExecutionRequest,
)
from app.schemas.admin_supplier_execution import (
    Y50_OUTBOUND_TELEGRAM_OPERATION,
    AdminSupplierExecutionAttemptRead,
    AdminSupplierExecutionRequestDetailRead,
    AdminSupplierExecutionRequestListItem,
    AdminSupplierExecutionRequestListRead,
    AdminTelegramIdempotencyKeyRead,
)


def _outbound_telegram_operation(
    att: SupplierExecutionAttempt,
    idem: Sequence[SupplierExecutionAttemptTelegramIdempotency],
) -> str | None:
    if idem:
        return Y50_OUTBOUND_TELEGRAM_OPERATION
    if att.channel_type == SupplierExecutionAttemptChannel.TELEGRAM:
        return Y50_OUTBOUND_TELEGRAM_OPERATION
    if (att.error_code or "").strip() == "telegram_send_failed":
        return Y50_OUTBOUND_TELEGRAM_OPERATION
    return None


def build_supplier_execution_attempt_read(
    att: SupplierExecutionAttempt,
    *,
    idem_rows: Sequence[SupplierExecutionAttemptTelegramIdempotency],
) -> AdminSupplierExecutionAttemptRead:
    """Y52: attach Y50 idempotency keys + operation hint. Read-only: no side effects."""
    idem = sorted(
        [r for r in idem_rows],
        key=lambda r: (r.created_at, r.id),
    )
    krs = [AdminTelegramIdempotencyKeyRead(idempotency_key=r.idempotency_key, recorded_at=r.created_at) for r in idem]
    return AdminSupplierExecutionAttemptRead(
        id=att.id,
        execution_request_id=att.execution_request_id,
        attempt_number=att.attempt_number,
        channel_type=att.channel_type,
        target_supplier_ref=att.target_supplier_ref,
        status=att.status,
        provider_reference=att.provider_reference,
        error_code=att.error_code,
        error_message=att.error_message,
        created_at=att.created_at,
        telegram_idempotency=krs,
        has_telegram_send_idempotency=len(krs) > 0,
        outbound_telegram_operation=_outbound_telegram_operation(att, idem),
    )


def load_telegram_idempotency_for_attempts(
    session: Session, attempt_ids: list[int]
) -> dict[int, list[SupplierExecutionAttemptTelegramIdempotency]]:
    if not attempt_ids:
        return {}
    rows = list(
        session.scalars(
            select(SupplierExecutionAttemptTelegramIdempotency)
            .where(SupplierExecutionAttemptTelegramIdempotency.supplier_execution_attempt_id.in_(attempt_ids))
            .order_by(
                SupplierExecutionAttemptTelegramIdempotency.supplier_execution_attempt_id,
                SupplierExecutionAttemptTelegramIdempotency.created_at,
                SupplierExecutionAttemptTelegramIdempotency.id,
            )
        ).all()
    )
    by_att: dict[int, list[SupplierExecutionAttemptTelegramIdempotency]] = defaultdict(list)
    for r in rows:
        by_att[r.supplier_execution_attempt_id].append(r)
    return {k: v for k, v in by_att.items()}


def build_supplier_execution_attempt_read_bare(session: Session, att: SupplierExecutionAttempt) -> AdminSupplierExecutionAttemptRead:
    """Y52: for single attempt when batch map not used (Y48/self-contained)."""
    mp = load_telegram_idempotency_for_attempts(session, [att.id])
    return build_supplier_execution_attempt_read(att, idem_rows=mp.get(att.id, ()))


class AdminSupplierExecutionReadService:
    def list_requests(
        self,
        session: Session,
        *,
        limit: int,
        offset: int,
        status: SupplierExecutionRequestStatus | None,
        source_entity_type: SupplierExecutionSourceEntityType | None,
    ) -> AdminSupplierExecutionRequestListRead:
        q = select(SupplierExecutionRequest)
        if status is not None:
            q = q.where(SupplierExecutionRequest.status == status)
        if source_entity_type is not None:
            q = q.where(SupplierExecutionRequest.source_entity_type == source_entity_type)
        q = q.order_by(SupplierExecutionRequest.created_at.desc()).offset(offset).limit(limit)
        rows = list(session.scalars(q).all())
        items = [AdminSupplierExecutionRequestListItem.model_validate(r) for r in rows]
        return AdminSupplierExecutionRequestListRead(items=items, total_returned=len(items))

    def get_request_detail(self, session: Session, request_id: int) -> AdminSupplierExecutionRequestDetailRead | None:
        q = (
            select(SupplierExecutionRequest)
            .options(selectinload(SupplierExecutionRequest.attempts))
            .where(SupplierExecutionRequest.id == request_id)
        )
        row = session.scalars(q).first()
        if row is None:
            return None
        attempts = sorted(
            row.attempts,
            key=lambda a: (a.attempt_number, a.id),
        )
        a_ids = [a.id for a in attempts]
        idem_by = load_telegram_idempotency_for_attempts(session, a_ids)
        return AdminSupplierExecutionRequestDetailRead(
            id=row.id,
            source_entry_point=row.source_entry_point,
            source_entity_type=row.source_entity_type,
            source_entity_id=row.source_entity_id,
            operator_workflow_intent_snapshot=row.operator_workflow_intent_snapshot,
            status=row.status,
            idempotency_key=row.idempotency_key,
            requested_by_user_id=row.requested_by_user_id,
            completed_at=row.completed_at,
            completed_by_user_id=row.completed_by_user_id,
            raw_response_reference=row.raw_response_reference,
            audit_notes=row.audit_notes,
            validation_error=row.validation_error,
            created_at=row.created_at,
            updated_at=row.updated_at,
            attempts=[
                build_supplier_execution_attempt_read(a, idem_rows=idem_by.get(a.id, ())) for a in attempts
            ],
        )
