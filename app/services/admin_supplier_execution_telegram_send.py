"""Y50: explicit admin-only Telegram send bound to one supplier_execution_attempt — idempotent, audited, fail-closed."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.enums import SupplierExecutionAttemptChannel, SupplierExecutionAttemptStatus
from app.models.supplier_execution import (
    SupplierExecutionAttempt,
    SupplierExecutionAttemptTelegramIdempotency,
    SupplierExecutionRequest,
)
from app.schemas.admin_supplier_execution import AdminSupplierExecutionAttemptRead
from app.services.telegram_showcase_client import TelegramShowcaseSendError, send_private_text_message


class AdminTelegramSendAttemptNotFoundError(Exception):
    pass


class AdminTelegramSendAttemptStateError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AdminTelegramSendMissingIdempotencyError(Exception):
    pass


class AdminTelegramSendConfigError(Exception):
    pass


def _norm_idem(key: str | None) -> str:
    s = (key or "").strip()
    if not s:
        raise AdminTelegramSendMissingIdempotencyError()
    return s


def send_supplier_telegram_for_attempt(
    session: Session,
    *,
    attempt_id: int,
    idempotency_key: str,
    message_text: str,
    target_telegram_user_id: int,
    settings: Settings,
) -> tuple[AdminSupplierExecutionAttemptRead, bool]:
    """
    Send exactly one Telegram private message in the context of one pending attempt.

    Idempotent: same (attempt_id, idempotency_key) after a prior success replays without calling Telegram.
    """
    if attempt_id is None or int(attempt_id) < 1:
        raise AdminTelegramSendAttemptNotFoundError()

    text = (message_text or "").strip()
    if not text:
        raise AdminTelegramSendAttemptStateError("message_text is required and must be non-blank.")
    if len(text) > 4096:
        raise AdminTelegramSendAttemptStateError("message_text exceeds Telegram 4096 character limit.")
    if target_telegram_user_id is None or int(target_telegram_user_id) < 1:
        raise AdminTelegramSendAttemptStateError("target_telegram_user_id must be a positive integer.")

    ikey = _norm_idem(idempotency_key)

    att: SupplierExecutionAttempt | None = session.scalars(
        select(SupplierExecutionAttempt)
        .where(SupplierExecutionAttempt.id == int(attempt_id))
        .with_for_update(),
    ).one_or_none()
    if att is None:
        raise AdminTelegramSendAttemptNotFoundError()

    req: SupplierExecutionRequest | None = session.get(SupplierExecutionRequest, int(att.execution_request_id))
    if req is None:
        raise AdminTelegramSendAttemptNotFoundError()

    done = session.scalar(
        select(SupplierExecutionAttemptTelegramIdempotency.id)
        .where(
            SupplierExecutionAttemptTelegramIdempotency.supplier_execution_attempt_id == att.id,
            SupplierExecutionAttemptTelegramIdempotency.idempotency_key == ikey,
        )
        .limit(1),
    )
    if done is not None:
        session.refresh(att)
        return AdminSupplierExecutionAttemptRead.model_validate(att), True

    if att.status != SupplierExecutionAttemptStatus.PENDING:
        raise AdminTelegramSendAttemptStateError(
            f"Send allowed only for pending attempts; current status is {att.status.value!r}.",
        )
    if att.channel_type not in (SupplierExecutionAttemptChannel.NONE, SupplierExecutionAttemptChannel.TELEGRAM):
        raise AdminTelegramSendAttemptStateError(
            f"Channel must be {SupplierExecutionAttemptChannel.NONE.value!r} or "
            f"{SupplierExecutionAttemptChannel.TELEGRAM.value!r}; got {att.channel_type.value!r}.",
        )
    if att.channel_type == SupplierExecutionAttemptChannel.TELEGRAM and att.target_supplier_ref:
        if att.target_supplier_ref.strip() != str(int(target_telegram_user_id)):
            raise AdminTelegramSendAttemptStateError(
                "target_telegram_user_id does not match this attempt's target_supplier_ref.",
            )

    token = (settings.telegram_bot_token or "").strip()
    if not token:
        raise AdminTelegramSendConfigError("TELEGRAM_BOT_TOKEN is not set; outbound Telegram is disabled.")

    try:
        msg_id = send_private_text_message(
            bot_token=token,
            telegram_user_id=int(target_telegram_user_id),
            text=text,
        )
    except TelegramShowcaseSendError as exc:
        att.status = SupplierExecutionAttemptStatus.FAILED
        att.error_code = "telegram_send_failed"
        desc = getattr(exc, "telegram_description", None) or str(exc)
        att.error_message = (desc)[:2000] if desc else "telegram_send_failed"
        att.provider_reference = None
        session.flush()
        return AdminSupplierExecutionAttemptRead.model_validate(att), False

    att.channel_type = SupplierExecutionAttemptChannel.TELEGRAM
    att.target_supplier_ref = str(int(target_telegram_user_id))
    att.status = SupplierExecutionAttemptStatus.SUCCEEDED
    att.provider_reference = str(msg_id)
    att.error_code = None
    att.error_message = None
    session.add(
        SupplierExecutionAttemptTelegramIdempotency(
            supplier_execution_attempt_id=att.id,
            idempotency_key=ikey,
        ),
    )
    session.flush()
    return AdminSupplierExecutionAttemptRead.model_validate(att), False
