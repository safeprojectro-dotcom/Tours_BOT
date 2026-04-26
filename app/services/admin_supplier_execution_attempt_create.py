"""Y48: admin-only create supplier_execution_attempt row — no messaging, no outbound I/O, no request terminalization."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.schemas.admin_supplier_execution import AdminSupplierExecutionAttemptRead

from app.models.enums import (
    SupplierExecutionAttemptChannel,
    SupplierExecutionAttemptStatus,
    SupplierExecutionRequestStatus,
)
from app.models.supplier_execution import SupplierExecutionRequest
from app.repositories import supplier_execution as se_repo
from app.services.admin_supplier_execution_read import build_supplier_execution_attempt_read_bare


_REQUEST_STATUSES_ALLOW_NEW_ATTEMPT: frozenset[SupplierExecutionRequestStatus] = frozenset(
    {
        SupplierExecutionRequestStatus.PENDING,
        SupplierExecutionRequestStatus.VALIDATED,
        SupplierExecutionRequestStatus.ATTEMPTED,
    },
)


class AdminAttemptExecutionRequestNotFoundError(Exception):
    pass


class AdminAttemptRequestStatusNotAllowedError(Exception):
    def __init__(self, status: SupplierExecutionRequestStatus) -> None:
        self.status = status
        super().__init__(f"Cannot create attempt while execution request is {status.value!r}.")


def create_admin_supplier_execution_attempt(
    session: Session,
    *,
    execution_request_id: int,
) -> AdminSupplierExecutionAttemptRead:
    """
    Insert one attempt row: channel `none`, status `pending`. Does not update parent request status, does not message.

    Fails if request missing or in blocked/succeeded/failed/cancelled.
    """
    if execution_request_id is None or int(execution_request_id) < 1:
        raise AdminAttemptExecutionRequestNotFoundError()

    req = session.get(SupplierExecutionRequest, int(execution_request_id))
    if req is None:
        raise AdminAttemptExecutionRequestNotFoundError()

    if req.status not in _REQUEST_STATUSES_ALLOW_NEW_ATTEMPT:
        raise AdminAttemptRequestStatusNotAllowedError(req.status)

    n = se_repo.next_attempt_number_for_request(session, execution_request_id=req.id)
    att = se_repo.build_execution_attempt(
        execution_request_id=req.id,
        attempt_number=n,
        channel_type=SupplierExecutionAttemptChannel.NONE,
        status=SupplierExecutionAttemptStatus.PENDING,
    )
    se_repo.add_execution_attempt(session, att)
    return build_supplier_execution_attempt_read_bare(session, att)
