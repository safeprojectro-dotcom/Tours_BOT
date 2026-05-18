"""S1D-2: admin-gated operational sales push channel publish."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.admin_operational_sales_push_preview import AdminOperationalSalesPushPreviewRead


class AdminOperationalSalesPushPublishBody(BaseModel):
    """Explicit confirmation required for live channel send (parity with other guarded admin POSTs)."""

    model_config = ConfigDict(extra="forbid")

    confirm: bool = Field(default=False, description="Must be true to send to Telegram channel.")


class AdminOperationalSalesPushChannelPublishResultRead(BaseModel):
    """Result after recheck + successful channel send."""

    model_config = ConfigDict(extra="forbid")

    tour_id: int
    telegram_message_id: int
    telegram_chat_id: str
    message_plain_sent: str
    eligibility_recheck: AdminOperationalSalesPushPreviewRead
