"""Y46: admin explicit trigger — creates supplier_execution_requests only; no messaging, no attempt rows."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.custom_marketplace_request import CustomMarketplaceRequest
from app.models.enums import (
    SupplierExecutionRequestStatus,
    SupplierExecutionSourceEntityType,
    SupplierExecutionSourceEntryPoint,
)
from app.models.supplier_execution import SupplierExecutionRequest
from app.repositories import supplier_execution as se_repo
from app.schemas.admin_supplier_execution import AdminSupplierExecutionRequestDetailRead
from app.services.admin_supplier_execution_read import AdminSupplierExecutionReadService


class AdminSupplierExecutionTriggerIdempotencyConflictError(Exception):
    """Same idempotency key already used for a different source entity."""


class AdminSupplierExecutionTriggerSourceNotFoundError(Exception):
    """source_entity_type + source_entity_id did not resolve to a row."""


class AdminSupplierExecutionTriggerUnsupportedEntityTypeError(Exception):
    """source_entity_type is not supported by this trigger slice."""


def _get_by_idempotency_key(session: Session, key: str) -> SupplierExecutionRequest | None:
    stripped = key.strip()
    q = select(SupplierExecutionRequest).where(SupplierExecutionRequest.idempotency_key == stripped)
    return session.scalars(q).first()


def _load_source_custom_marketplace_request(
    session: Session, *, entity_id: int
) -> CustomMarketplaceRequest | None:
    if entity_id < 1:
        return None
    return session.get(CustomMarketplaceRequest, entity_id)


def trigger_admin_explicit_create_request(
    session: Session,
    *,
    idempotency_key: str,
    source_entity_type: SupplierExecutionSourceEntityType,
    source_entity_id: int,
    requested_by_user_id: int,
) -> tuple[AdminSupplierExecutionRequestDetailRead, bool]:
    """
    Create a validated execution request row (Y45/Y46) or return an existing row for the same key+entity (idempotent).

    Does not commit. No attempt rows. No supplier contact.
    """
    key = idempotency_key.strip()
    existing = _get_by_idempotency_key(session, key)
    if existing is not None:
        if (
            existing.source_entity_type == source_entity_type
            and existing.source_entity_id == source_entity_id
        ):
            detail = AdminSupplierExecutionReadService().get_request_detail(session, existing.id)
            if detail is None:
                raise RuntimeError("Execution request missing after idempotency hit.")
            return detail, True
        raise AdminSupplierExecutionTriggerIdempotencyConflictError()

    if source_entity_type != SupplierExecutionSourceEntityType.CUSTOM_MARKETPLACE_REQUEST:
        raise AdminSupplierExecutionTriggerUnsupportedEntityTypeError()

    cmr = _load_source_custom_marketplace_request(session, entity_id=source_entity_id)
    if cmr is None:
        raise AdminSupplierExecutionTriggerSourceNotFoundError()

    snapshot = cmr.operator_workflow_intent
    req = se_repo.build_execution_request(
        source_entry_point=SupplierExecutionSourceEntryPoint.ADMIN_EXPLICIT,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
        idempotency_key=key,
        status=SupplierExecutionRequestStatus.VALIDATED,
        requested_by_user_id=requested_by_user_id,
        operator_workflow_intent_snapshot=snapshot,
    )
    try:
        se_repo.add_execution_request(session, req)
    except IntegrityError:
        session.rollback()
        again = _get_by_idempotency_key(session, key)
        if again is not None:
            if (
                again.source_entity_type == source_entity_type
                and again.source_entity_id == source_entity_id
            ):
                detail = AdminSupplierExecutionReadService().get_request_detail(session, again.id)
                if detail is None:
                    raise RuntimeError("Execution request missing after concurrent insert.")
                return detail, True
        raise AdminSupplierExecutionTriggerIdempotencyConflictError() from None

    detail = AdminSupplierExecutionReadService().get_request_detail(session, req.id)
    if detail is None:
        raise RuntimeError("Execution request missing after insert.")
    return detail, False
