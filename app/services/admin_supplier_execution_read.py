"""Y44: read-only admin queries for supplier execution records — no writes, no execution."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.supplier_execution import SupplierExecutionRequest
from app.models.enums import SupplierExecutionRequestStatus, SupplierExecutionSourceEntityType
from app.schemas.admin_supplier_execution import (
    AdminSupplierExecutionAttemptRead,
    AdminSupplierExecutionRequestDetailRead,
    AdminSupplierExecutionRequestListItem,
    AdminSupplierExecutionRequestListRead,
)


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
            attempts=[AdminSupplierExecutionAttemptRead.model_validate(a) for a in attempts],
        )
