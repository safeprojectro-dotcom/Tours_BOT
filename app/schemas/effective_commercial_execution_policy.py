"""Composed RFQ + tour commercial execution/read model (Track 5b.3a)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EffectiveCommercialExecutionPolicyRead(BaseModel):
    """Runtime composition: Layer A tour policy, supplier RFQ declaration, request resolution."""

    model_config = ConfigDict(extra="forbid")

    self_service_preparation_allowed: bool
    self_service_hold_allowed: bool
    platform_checkout_allowed: bool
    assisted_only: bool
    external_only: bool
    blocked_code: str | None = Field(
        default=None,
        description="Stable diagnostic code when self-service is not allowed.",
    )
    blocked_reason: str | None = Field(
        default=None,
        description="Short operator-facing explanation (admin/logs).",
    )
    customer_blocked_code: str | None = Field(
        default=None,
        description="Code suitable for customer-channel envelopes where applicable.",
    )
