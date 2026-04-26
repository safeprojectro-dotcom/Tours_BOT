"""Y54: admin manual retry — new pending attempt only; no Telegram; no auto-send."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import (
    SupplierExecutionAttemptChannel,
    SupplierExecutionAttemptStatus,
    SupplierExecutionRequestStatus,
)
from app.models.supplier_execution import SupplierExecutionAttempt, SupplierExecutionRequest
from app.repositories import supplier_execution as se_repo
from app.schemas.admin_supplier_execution import AdminSupplierExecutionAttemptRead
from app.services.admin_supplier_execution_attempt_create import AdminAttemptRequestStatusNotAllowedError

# Same allowlist as Y48 `create_admin_supplier_execution_attempt` — parent must allow new attempt rows.
_REQUEST_STATUSES_ALLOW_RETRY_NEW_ATTEMPT: frozenset[SupplierExecutionRequestStatus] = frozenset(
    {
        SupplierExecutionRequestStatus.PENDING,
        SupplierExecutionRequestStatus.VALIDATED,
        SupplierExecutionRequestStatus.ATTEMPTED,
    },
)
from app.services.admin_supplier_execution_read import build_supplier_execution_attempt_read_bare


# Y54: only terminal failure is retry-eligible (not pending/succeeded/skipped)
_RETRY_ELIGIBLE_STATUSES: frozenset[SupplierExecutionAttemptStatus] = frozenset(
    {SupplierExecutionAttemptStatus.FAILED},
)


class AdminRetryAttemptNotFoundError(Exception):
    pass


class AdminRetryAttemptNotEligibleError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def create_admin_supplier_execution_retry(
    session: Session,
    *,
    original_attempt_id: int,
    retry_reason: str,
    requested_by_user_id: int,
) -> AdminSupplierExecutionAttemptRead:
    """
    Create a new pending attempt linked to a failed prior attempt. Does not call Telegram.
    """
    if original_attempt_id is None or int(original_attempt_id) < 1:
        raise AdminRetryAttemptNotFoundError()
    s = (retry_reason or "").strip()
    if not s:
        raise AdminRetryAttemptNotEligibleError("retry_reason is required and must be non-blank.")
    if requested_by_user_id is None or int(requested_by_user_id) < 1:
        raise AdminRetryAttemptNotEligibleError("requested_by_user_id must be a valid user id.")

    att = session.scalars(
        select(SupplierExecutionAttempt)
        .where(SupplierExecutionAttempt.id == int(original_attempt_id))
    ).first()
    if att is None:
        raise AdminRetryAttemptNotFoundError()

    if att.status not in _RETRY_ELIGIBLE_STATUSES:
        raise AdminRetryAttemptNotEligibleError(
            f"Only attempts in status {SupplierExecutionAttemptStatus.FAILED.value!r} may be retried; "
            f"current status is {att.status.value!r}."
        )

    req = session.get(SupplierExecutionRequest, att.execution_request_id)
    if req is None:
        raise AdminRetryAttemptNotFoundError()

    if req.status not in _REQUEST_STATUSES_ALLOW_RETRY_NEW_ATTEMPT:
        raise AdminAttemptRequestStatusNotAllowedError(req.status)

    n = se_repo.next_attempt_number_for_request(session, execution_request_id=req.id)
    new_att = se_repo.build_execution_attempt(
        execution_request_id=req.id,
        attempt_number=n,
        channel_type=SupplierExecutionAttemptChannel.NONE,
        status=SupplierExecutionAttemptStatus.PENDING,
        retry_from_supplier_execution_attempt_id=att.id,
        retry_reason=s,
        retry_requested_by_user_id=int(requested_by_user_id),
    )
    se_repo.add_execution_attempt(session, new_att)
    return build_supplier_execution_attempt_read_bare(session, new_att)
