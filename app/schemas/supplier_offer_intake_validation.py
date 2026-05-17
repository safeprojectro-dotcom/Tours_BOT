"""A2: read-only supplier intake validation projection (derived from publishing console rows only)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SupplierOfferIntakeValidationRead(BaseModel):
    """Structured intake completeness / risk hints for admin review (not persisted; no supplier I/O)."""

    model_config = ConfigDict(extra="forbid")

    supplier_offer_id: int = Field(description="Supplier offer this validation row refers to.")
    validation_version: Literal["a2_v1"] = "a2_v1"
    projection_source: Literal["publishing_console_item"] = Field(
        default="publishing_console_item",
        description="Traceability: inputs are the read-only publishing-console list row only.",
    )
    headline: str = Field(description="One-line intake posture for triage.")
    projection_note: str = Field(
        default="Derived from the read-only publishing console row only; not a persisted compliance verdict.",
    )
    facts_present: list[str] = Field(
        default_factory=list,
        description="Stable fact keys detected as present enough for intake (machine-oriented labels).",
    )
    facts_missing_required: list[str] = Field(
        default_factory=list,
        description="Required intake dimensions that appear missing or blocking from this projection.",
    )
    facts_weak_or_unclear: list[str] = Field(
        default_factory=list,
        description="Fields that exist but look thin, risky, or ambiguous for the next admin step.",
    )
    blocks_publication: list[str] = Field(
        default_factory=list,
        description="Reasons this row still should not be treated as showcase-publish-ready from intake signals.",
    )
    blocks_catalog_conversion: list[str] = Field(
        default_factory=list,
        description="Reasons catalog / execution-link / prepare-chain posture is not green from this projection.",
    )
    suggested_supplier_requests: list[str] = Field(
        default_factory=list,
        description=(
            "Heuristic follow-ups from console diagnostics; may include internal/platform wording. "
            "For supplier-facing copy use clarification_draft.supplier_facing_asks (A3)."
        ),
    )


__all__ = ["SupplierOfferIntakeValidationRead"]
