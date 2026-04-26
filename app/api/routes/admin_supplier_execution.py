"""Y44: admin read; Y46: POST create request; Y48: POST create attempt; Y50: send-telegram (first outbound)."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.admin_auth import require_admin_api_token
from app.db.session import get_db
from app.models.enums import (
    SupplierExecutionAttemptStatus,
    SupplierExecutionRequestStatus,
    SupplierExecutionSourceEntityType,
)
from app.repositories.user import UserRepository
from app.core.config import get_settings
from app.schemas.admin_supplier_execution import (
    AdminSupplierExecutionAttemptRead,
    AdminSupplierExecutionRequestDetailRead,
    AdminSupplierExecutionRequestListRead,
    AdminSupplierExecutionRetryBody,
    AdminSupplierExecutionSendTelegramBody,
    AdminSupplierExecutionSendTelegramResponse,
    AdminSupplierExecutionTriggerBody,
    AdminSupplierExecutionTriggerResponse,
)
from app.services.admin_supplier_execution_attempt_create import (
    AdminAttemptExecutionRequestNotFoundError,
    AdminAttemptRequestStatusNotAllowedError,
    create_admin_supplier_execution_attempt,
)
from app.services.admin_supplier_execution_read import AdminSupplierExecutionReadService
from app.services.admin_supplier_execution_retry import (
    AdminRetryAttemptNotEligibleError,
    AdminRetryAttemptNotFoundError,
    create_admin_supplier_execution_retry,
)
from app.services.admin_supplier_execution_telegram_send import (
    AdminTelegramSendAttemptNotFoundError,
    AdminTelegramSendAttemptStateError,
    AdminTelegramSendConfigError,
    AdminTelegramSendMissingIdempotencyError,
    send_supplier_telegram_for_attempt,
)
from app.services.admin_supplier_execution_trigger import (
    AdminSupplierExecutionTriggerIdempotencyConflictError,
    AdminSupplierExecutionTriggerSourceNotFoundError,
    AdminSupplierExecutionTriggerUnsupportedEntityTypeError,
    trigger_admin_explicit_create_request,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_api_token)],
)


@router.get("/supplier-execution-requests", response_model=AdminSupplierExecutionRequestListRead)
def list_supplier_execution_requests(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0, le=100_000),
    status: SupplierExecutionRequestStatus | None = Query(default=None),
    source_entity_type: SupplierExecutionSourceEntityType | None = Query(default=None),
) -> AdminSupplierExecutionRequestListRead:
    return AdminSupplierExecutionReadService().list_requests(
        db,
        limit=limit,
        offset=offset,
        status=status,
        source_entity_type=source_entity_type,
    )


@router.get("/supplier-execution-requests/{request_id}", response_model=AdminSupplierExecutionRequestDetailRead)
def get_supplier_execution_request(
    request_id: int,
    db: Session = Depends(get_db),
) -> AdminSupplierExecutionRequestDetailRead:
    detail = AdminSupplierExecutionReadService().get_request_detail(db, request_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier execution request not found.")
    return detail


@router.post(
    "/supplier-execution-requests",
    response_model=AdminSupplierExecutionTriggerResponse,
)
def post_supplier_execution_request(
    response: Response,
    db: Session = Depends(get_db),
    payload: AdminSupplierExecutionTriggerBody = Body(...),
    x_admin_actor_telegram_id: str | None = Header(default=None, alias="X-Admin-Actor-Telegram-Id"),
) -> AdminSupplierExecutionTriggerResponse:
    """Y46: create or idempotently resolve a validated execution request (admin explicit only). No messaging, no attempts."""
    if x_admin_actor_telegram_id is None or not str(x_admin_actor_telegram_id).strip().isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Admin-Actor-Telegram-Id header is required (Telegram user id of the actor).",
        )
    actor_tg = int(str(x_admin_actor_telegram_id).strip())
    user = UserRepository().get_by_telegram_user_id(db, telegram_user_id=actor_tg)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No User record for the given X-Admin-Actor-Telegram-Id.",
        )
    try:
        detail, idempotent_replay = trigger_admin_explicit_create_request(
            db,
            idempotency_key=payload.idempotency_key,
            source_entity_type=payload.source_entity_type,
            source_entity_id=payload.source_entity_id,
            requested_by_user_id=user.id,
        )
    except AdminSupplierExecutionTriggerSourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source entity not found for the given type and id.",
        ) from None
    except AdminSupplierExecutionTriggerUnsupportedEntityTypeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source_entity_type is not supported for this trigger.",
        ) from None
    except AdminSupplierExecutionTriggerIdempotencyConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="idempotency_key already used for a different source entity.",
        ) from None
    response.status_code = status.HTTP_200_OK if idempotent_replay else status.HTTP_201_CREATED
    db.commit()
    return AdminSupplierExecutionTriggerResponse(request=detail, idempotent_replay=idempotent_replay)


@router.post(
    "/supplier-execution-requests/{request_id}/attempts",
    response_model=AdminSupplierExecutionAttemptRead,
    status_code=status.HTTP_201_CREATED,
)
def post_supplier_execution_request_attempt(
    request_id: int,
    db: Session = Depends(get_db),
    x_admin_actor_telegram_id: str | None = Header(default=None, alias="X-Admin-Actor-Telegram-Id"),
) -> AdminSupplierExecutionAttemptRead:
    """Y48: add one `pending` attempt row (channel `none` only). No supplier messaging, no request status change."""
    if x_admin_actor_telegram_id is None or not str(x_admin_actor_telegram_id).strip().isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Admin-Actor-Telegram-Id header is required (Telegram user id of the actor).",
        )
    actor_tg = int(str(x_admin_actor_telegram_id).strip())
    user = UserRepository().get_by_telegram_user_id(db, telegram_user_id=actor_tg)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No User record for the given X-Admin-Actor-Telegram-Id.",
        )
    try:
        attempt = create_admin_supplier_execution_attempt(db, execution_request_id=request_id)
    except AdminAttemptExecutionRequestNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier execution request not found.",
        ) from None
    except AdminAttemptRequestStatusNotAllowedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None
    db.commit()
    return attempt


@router.post(
    "/supplier-execution-attempts/{attempt_id}/retry",
    response_model=AdminSupplierExecutionAttemptRead,
    status_code=status.HTTP_201_CREATED,
)
def post_supplier_execution_attempt_retry(
    attempt_id: int,
    db: Session = Depends(get_db),
    body: AdminSupplierExecutionRetryBody = Body(...),
    x_admin_actor_telegram_id: str | None = Header(default=None, alias="X-Admin-Actor-Telegram-Id"),
) -> AdminSupplierExecutionAttemptRead:
    """Y54: create a new pending attempt linked to a failed prior attempt. Does not send Telegram."""
    if x_admin_actor_telegram_id is None or not str(x_admin_actor_telegram_id).strip().isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Admin-Actor-Telegram-Id header is required (Telegram user id of the actor).",
        )
    actor_tg = int(str(x_admin_actor_telegram_id).strip())
    user = UserRepository().get_by_telegram_user_id(db, telegram_user_id=actor_tg)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No User record for the given X-Admin-Actor-Telegram-Id.",
        )
    try:
        new_attempt = create_admin_supplier_execution_retry(
            db,
            original_attempt_id=attempt_id,
            retry_reason=body.retry_reason,
            requested_by_user_id=user.id,
        )
    except AdminRetryAttemptNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier execution attempt not found.",
        ) from None
    except AdminRetryAttemptNotEligibleError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    except AdminAttemptRequestStatusNotAllowedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None
    db.commit()
    return new_attempt


def _resolve_send_idempotency_key(
    *,
    header_idem: str | None,
    x_idem: str | None,
    body_key: str | None,
) -> str:
    for v in (header_idem, x_idem, body_key):
        if v is not None and (s := str(v).strip()):
            return s
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Idempotency key is required: set Idempotency-Key, X-Idempotency-Key, or idempotency_key in body.",
    )


@router.post(
    "/supplier-execution-attempts/{attempt_id}/send-telegram",
    response_model=AdminSupplierExecutionSendTelegramResponse,
)
def post_send_supplier_execution_telegram(
    attempt_id: int,
    response: Response,
    db: Session = Depends(get_db),
    body: AdminSupplierExecutionSendTelegramBody = Body(...),
    idempotency_key_header: str | None = Header(default=None, alias="Idempotency-Key"),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
    x_admin_actor_telegram_id: str | None = Header(default=None, alias="X-Admin-Actor-Telegram-Id"),
) -> AdminSupplierExecutionSendTelegramResponse:
    """Y50: send one Telegram private message; admin explicit; idempotent; no other automation."""
    if x_admin_actor_telegram_id is None or not str(x_admin_actor_telegram_id).strip().isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Admin-Actor-Telegram-Id header is required (Telegram user id of the actor).",
        )
    actor_tg = int(str(x_admin_actor_telegram_id).strip())
    if UserRepository().get_by_telegram_user_id(db, telegram_user_id=actor_tg) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No User record for the given X-Admin-Actor-Telegram-Id.",
        )
    ikey = _resolve_send_idempotency_key(
        header_idem=idempotency_key_header,
        x_idem=x_idempotency_key,
        body_key=body.idempotency_key,
    )
    settings = get_settings()
    try:
        attempt_read, idempotent_replay = send_supplier_telegram_for_attempt(
            db,
            attempt_id=attempt_id,
            idempotency_key=ikey,
            message_text=body.message_text,
            target_telegram_user_id=body.target_telegram_user_id,
            settings=settings,
        )
    except AdminTelegramSendAttemptNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier execution attempt not found or parent request missing.",
        ) from None
    except AdminTelegramSendMissingIdempotencyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency key is required: set Idempotency-Key, X-Idempotency-Key, or idempotency_key in body.",
        ) from None
    except AdminTelegramSendAttemptStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    except AdminTelegramSendConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from None
    if idempotent_replay:
        response.status_code = status.HTTP_200_OK
    elif attempt_read.status == SupplierExecutionAttemptStatus.SUCCEEDED:
        response.status_code = status.HTTP_201_CREATED
    else:
        response.status_code = status.HTTP_200_OK
    db.commit()
    return AdminSupplierExecutionSendTelegramResponse(attempt=attempt_read, idempotent_replay=idempotent_replay)
