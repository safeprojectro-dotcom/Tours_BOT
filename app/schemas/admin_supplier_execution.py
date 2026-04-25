"""Y44: read-only admin API for supplier execution persistence (Y43)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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
