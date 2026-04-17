"""Track 5b.1: persisted intent to execute Layer A booking later — no holds or payments."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CustomRequestBookingBridgeStatus, sqlalchemy_enum
from app.models.mixins import TimestampMixin


class CustomRequestBookingBridge(TimestampMixin, Base):
    __tablename__ = "custom_request_booking_bridges"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("custom_marketplace_requests.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    selected_supplier_response_id: Mapped[int] = mapped_column(
        ForeignKey("supplier_custom_request_responses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    tour_id: Mapped[int | None] = mapped_column(
        ForeignKey("tours.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    bridge_status: Mapped[CustomRequestBookingBridgeStatus] = mapped_column(
        sqlalchemy_enum(CustomRequestBookingBridgeStatus, name="custom_request_booking_bridge_status"),
        nullable=False,
    )
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    request: Mapped["CustomMarketplaceRequest"] = relationship(
        "CustomMarketplaceRequest",
        foreign_keys="[CustomRequestBookingBridge.request_id]",
        viewonly=True,
    )
    tour: Mapped["Tour | None"] = relationship(
        "Tour",
        foreign_keys="[CustomRequestBookingBridge.tour_id]",
        viewonly=True,
    )
