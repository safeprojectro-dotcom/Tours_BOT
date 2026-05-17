"""S1B: read-only admin resolution of supplier Telegram contact (no send, no customer PII)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AdminTelegramContactContext = Literal["supplier", "supplier_offer", "tour", "order"]

AdminTelegramContactResolutionStatus = Literal[
    "resolved_with_contact",
    "resolved_missing_contact",
    "missing_relationship",
    "ambiguous_suppliers",
]


class AdminSupplierTelegramContactResolutionRead(BaseModel):
    """Whether a future supplier Telegram DM can target ``suppliers.primary_telegram_user_id`` (private chat id)."""

    model_config = ConfigDict(extra="forbid")

    context_type: AdminTelegramContactContext
    context_id: int = Field(ge=1)

    resolution_status: AdminTelegramContactResolutionStatus

    supplier_id: int | None = Field(default=None, description="Layer B supplier when relationship is unambiguous.")
    supplier_code: str | None = None
    supplier_display_name: str | None = None
    supplier_is_active: bool | None = None

    primary_telegram_user_id: int | None = Field(
        default=None,
        description="Supplier primary Telegram user id (private chat target). None if not configured or unresolved.",
    )
    telegram_contact_configured: bool = Field(
        description="True when primary_telegram_user_id is non-null on the resolved supplier row.",
    )

    resolution_path_codes: list[str] = Field(
        default_factory=list,
        description="Machine-readable trace (e.g. supplier_row, supplier_offer_owner, tour_active_execution_links).",
    )
    linked_supplier_ids: list[int] = Field(
        default_factory=list,
        description="All supplier ids tied to the context when ambiguous or for audit; empty when a single supplier wins.",
    )
    readiness_warnings: list[str] = Field(default_factory=list)
