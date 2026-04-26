"""Y44: admin read DTOs; Y46: trigger; Y48: attempt create response uses `AdminSupplierExecutionAttemptRead` (Y43)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import (
    OperatorWorkflowIntent,
    SupplierExecutionAttemptChannel,
    SupplierExecutionAttemptStatus,
    SupplierExecutionRequestStatus,
    SupplierExecutionSourceEntityType,
    SupplierExecutionSourceEntryPoint,
)


class AdminSupplierExecutionRequestListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: SupplierExecutionRequestStatus
    source_entity_type: SupplierExecutionSourceEntityType
    source_entity_id: int
    operator_workflow_intent_snapshot: OperatorWorkflowIntent | None
    created_at: datetime


class AdminSupplierExecutionRequestListRead(BaseModel):
    items: list[AdminSupplierExecutionRequestListItem]
    total_returned: int


Y50_OUTBOUND_TELEGRAM_OPERATION = "POST /admin/supplier-execution-attempts/{attempt_id}/send-telegram"
"""Y50+Y51: stable label for the only current Telegram send entry (read-only DTO, not invoked)."""


class AdminTelegramIdempotencyKeyRead(BaseModel):
    """Y52: one Y50 `supplier_execution_attempt_telegram_idempotency` row (successful deduped send)."""

    idempotency_key: str
    recorded_at: datetime


class AdminSupplierExecutionAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    execution_request_id: int
    attempt_number: int
    channel_type: SupplierExecutionAttemptChannel
    target_supplier_ref: str | None
    status: SupplierExecutionAttemptStatus
    provider_reference: str | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    # Y52: Y50 idempotency evidence + which operation last touched Telegram for this attempt (read-only; no I/O)
    telegram_idempotency: list[AdminTelegramIdempotencyKeyRead] = Field(
        default_factory=list,
        description="Successful-send idempotency keys recorded (empty if send never succeeded with dedup row).",
    )
    has_telegram_send_idempotency: bool = Field(
        default=False,
        description="True if at least one Y50 idempotency row exists for this attempt.",
    )
    outbound_telegram_operation: str | None = Field(
        default=None,
        description="Which admin send path applied, when Y50 can be inferred (idempotency, telegram channel, or telegram_send_failed).",
    )
    # Y54: set when this row was created by manual retry (POST .../retry); idempotency keys appear only after Y50 send on this attempt.
    retry_from_attempt_id: int | None = Field(
        default=None,
        description="If present, this attempt was created as a manual retry of the given prior attempt id.",
    )
    retry_reason: str | None = Field(default=None, description="Y54: ops reason when retry_from_attempt_id is set.")
    retry_requested_by_user_id: int | None = Field(
        default=None,
        description="Y54: internal users.id of the admin who requested the retry.",
    )


class AdminSupplierExecutionRequestDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_entry_point: SupplierExecutionSourceEntryPoint
    source_entity_type: SupplierExecutionSourceEntityType
    source_entity_id: int
    operator_workflow_intent_snapshot: OperatorWorkflowIntent | None
    status: SupplierExecutionRequestStatus
    idempotency_key: str
    requested_by_user_id: int | None
    completed_at: datetime | None
    completed_by_user_id: int | None
    raw_response_reference: str | None
    audit_notes: str | None
    validation_error: str | None
    created_at: datetime
    updated_at: datetime
    attempts: list[AdminSupplierExecutionAttemptRead] = Field(default_factory=list)


class AdminSupplierExecutionTriggerBody(BaseModel):
    """Y46: payload for `POST /admin/supplier-execution-requests` (admin explicit; no supplier contact)."""

    idempotency_key: str = Field(..., min_length=1, max_length=128)
    source_entity_type: SupplierExecutionSourceEntityType
    source_entity_id: int = Field(..., ge=1)

    @field_validator("idempotency_key")
    @classmethod
    def idempotency_not_blank(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("idempotency_key must be non-blank")
        return s


class AdminSupplierExecutionTriggerResponse(BaseModel):
    request: AdminSupplierExecutionRequestDetailRead
    idempotent_replay: bool = False


class AdminSupplierExecutionSendTelegramBody(BaseModel):
    """Y50: payload for `POST /admin/supplier-execution-attempts/{id}/send-telegram`. Idempotency from header or body."""

    idempotency_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        description="If `Idempotency-Key` / `X-Idempotency-Key` is absent, this field is required.",
    )
    message_text: str = Field(..., min_length=1, max_length=4096)
    target_telegram_user_id: int = Field(..., ge=1)

    @field_validator("idempotency_key")
    @classmethod
    def idempotency_strip(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        if not s:
            return None
        return s

    @field_validator("message_text")
    @classmethod
    def text_strip(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("message_text must be non-blank")
        return s


class AdminSupplierExecutionSendTelegramResponse(BaseModel):
    attempt: AdminSupplierExecutionAttemptRead
    idempotent_replay: bool = False


class AdminSupplierExecutionRetryBody(BaseModel):
    """Y54: payload for `POST /admin/supplier-execution-attempts/{attempt_id}/retry`. No Telegram send in this call."""

    retry_reason: str = Field(..., min_length=1, max_length=4096)

    @field_validator("retry_reason")
    @classmethod
    def retry_reason_strip(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("retry_reason must be non-blank")
        return s
