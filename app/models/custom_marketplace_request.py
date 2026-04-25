"""Layer C: custom trip / group requests (RFQ) — separate from core orders (Track 4)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    CommercialResolutionKind,
    CustomMarketplaceRequestSource,
    CustomMarketplaceRequestStatus,
    CustomMarketplaceRequestType,
    OperatorWorkflowIntent,
    SupplierCustomRequestResponseKind,
    SupplierOfferPaymentMode,
    TourSalesMode,
    sqlalchemy_enum,
)
from app.models.mixins import TimestampMixin


class CustomMarketplaceRequest(TimestampMixin, Base):
    """Customer-originated structured request visible to suppliers (broadcast MVP)."""

    __tablename__ = "custom_marketplace_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    request_type: Mapped[CustomMarketplaceRequestType] = mapped_column(
        sqlalchemy_enum(CustomMarketplaceRequestType, name="custom_marketplace_request_type"),
        nullable=False,
    )
    travel_date_start: Mapped[date] = mapped_column(Date, nullable=False)
    travel_date_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    route_notes: Mapped[str] = mapped_column(Text, nullable=False)
    group_size: Mapped[int | None] = mapped_column(nullable=True)
    special_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_channel: Mapped[CustomMarketplaceRequestSource] = mapped_column(
        sqlalchemy_enum(CustomMarketplaceRequestSource, name="custom_marketplace_request_source"),
        nullable=False,
    )
    status: Mapped[CustomMarketplaceRequestStatus] = mapped_column(
        sqlalchemy_enum(CustomMarketplaceRequestStatus, name="custom_marketplace_request_status"),
        nullable=False,
        default=CustomMarketplaceRequestStatus.OPEN,
    )
    admin_intervention_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    selected_supplier_response_id: Mapped[int | None] = mapped_column(
        ForeignKey("supplier_custom_request_responses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    commercial_resolution_kind: Mapped[CommercialResolutionKind | None] = mapped_column(
        sqlalchemy_enum(CommercialResolutionKind, name="commercial_resolution_kind"),
        nullable=True,
    )
    assigned_operator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    operator_workflow_intent: Mapped[OperatorWorkflowIntent | None] = mapped_column(
        sqlalchemy_enum(OperatorWorkflowIntent, name="operator_workflow_intent"),
        nullable=True,
    )
    operator_workflow_intent_set_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    operator_workflow_intent_set_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="custom_marketplace_requests",
        foreign_keys="[CustomMarketplaceRequest.user_id]",
    )
    assigned_operator: Mapped["User | None"] = relationship(
        "User",
        back_populates="ops_assigned_custom_marketplace_requests",
        foreign_keys="[CustomMarketplaceRequest.assigned_operator_id]",
    )
    assigned_by: Mapped["User | None"] = relationship(
        "User",
        back_populates="ops_assigned_custom_marketplace_requests_by_actor",
        foreign_keys="[CustomMarketplaceRequest.assigned_by_user_id]",
    )
    operator_workflow_intent_set_by: Mapped["User | None"] = relationship(
        "User",
        back_populates="ops_set_operator_workflow_intent_on_requests",
        foreign_keys="[CustomMarketplaceRequest.operator_workflow_intent_set_by_user_id]",
    )
    supplier_responses: Mapped[list["SupplierCustomRequestResponse"]] = relationship(
        "SupplierCustomRequestResponse",
        back_populates="request",
        cascade="all, delete-orphan",
        foreign_keys="SupplierCustomRequestResponse.request_id",
        overlaps="selected_supplier_response,request",
    )
    selected_supplier_response: Mapped["SupplierCustomRequestResponse | None"] = relationship(
        "SupplierCustomRequestResponse",
        foreign_keys="[CustomMarketplaceRequest.selected_supplier_response_id]",
        viewonly=True,
        overlaps="supplier_responses",
    )


class SupplierCustomRequestResponse(TimestampMixin, Base):
    """One supplier's structured response to a custom request."""

    __tablename__ = "supplier_custom_request_responses"
    __table_args__ = (UniqueConstraint("request_id", "supplier_id", name="uq_supplier_response_per_request"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("custom_marketplace_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    response_kind: Mapped[SupplierCustomRequestResponseKind] = mapped_column(
        sqlalchemy_enum(SupplierCustomRequestResponseKind, name="supplier_custom_request_response_kind"),
        nullable=False,
    )
    supplier_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    quoted_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    quoted_currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    supplier_declared_sales_mode: Mapped[TourSalesMode | None] = mapped_column(
        sqlalchemy_enum(TourSalesMode, name="tour_sales_mode"),
        nullable=True,
    )
    supplier_declared_payment_mode: Mapped[SupplierOfferPaymentMode | None] = mapped_column(
        sqlalchemy_enum(SupplierOfferPaymentMode, name="supplier_offer_payment_mode"),
        nullable=True,
    )

    request: Mapped["CustomMarketplaceRequest"] = relationship(
        back_populates="supplier_responses",
        foreign_keys="[SupplierCustomRequestResponse.request_id]",
        overlaps="selected_supplier_response,supplier_responses",
    )
    supplier: Mapped["Supplier"] = relationship(back_populates="custom_request_responses")
