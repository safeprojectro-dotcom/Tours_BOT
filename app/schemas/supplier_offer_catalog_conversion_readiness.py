"""A6A: read-only catalog / conversion readiness snapshot for supplier-offer cockpit cards."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CatalogConversionReadinessStatus = Literal[
    "ready_for_review",
    "needs_internal_preparation",
    "blocked",
]


class CatalogConversionGuidedActionRead(BaseModel):
    """A6B: single inline action for catalog/conversion readiness (callback or external URL only)."""

    model_config = ConfigDict(extra="forbid")

    label_message_key: str = Field(description="messages.py key; never shown raw to users.")
    callback_data: str | None = Field(default=None, description="Telegram callback when not a URL action.")
    url: str | None = Field(default=None, description="HTTPS URL for open-in-browser style actions.")

    @model_validator(mode="after")
    def _xor_target(self) -> "CatalogConversionGuidedActionRead":
        has_cb = self.callback_data is not None and self.callback_data != ""
        has_url = self.url is not None and self.url != ""
        if has_cb == has_url:
            raise ValueError("Exactly one of callback_data or url must be set.")
        return self


class SupplierOfferCatalogConversionReadinessRead(BaseModel):
    """Deterministic projection from publishing-console row (+ optional detail); no I/O."""

    model_config = ConfigDict(extra="forbid")

    version: Literal["a6a_v1"] = "a6a_v1"
    readiness_status: CatalogConversionReadinessStatus
    status_label_message_key: str = Field(
        description="messages.py key for the status line (admin_a6a_…).",
    )
    main_blocker_message_key: str | None = Field(
        default=None,
        description="Optional messages.py key; never raw backend tokens.",
    )
    warnings_message_keys: list[str] = Field(
        default_factory=list,
        max_length=2,
        description="Up to two short warning keys for translate().",
    )
    next_step_message_key: str = Field(description="messages.py key for recommended internal step.")
    has_tour_link: bool | None = Field(
        default=None,
        description="Bridge / exact-tour association signal when known.",
    )
    has_execution_link: bool | None = Field(
        default=None,
        description="Active execution link for Mini App CTA path when known.",
    )
    mini_app_cta_safe: bool | None = Field(
        default=None,
        description="True when exact-tour CTA gate passes (cta_safety exact_tour_ready).",
    )
    catalog_visible: bool | None = Field(
        default=None,
        description="Tour listed for Mini App catalog when known from detail.",
    )
    guided_actions: list[CatalogConversionGuidedActionRead] = Field(
        default_factory=list,
        description="A6B: safe next-step buttons (existing guarded Telegram flows or HTTPS links).",
    )


__all__ = [
    "CatalogConversionGuidedActionRead",
    "CatalogConversionReadinessStatus",
    "SupplierOfferCatalogConversionReadinessRead",
]
