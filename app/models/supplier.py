from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    SupplierOfferLifecycle,
    SupplierOfferPaymentMode,
    SupplierServiceComposition,
    TourSalesMode,
    sqlalchemy_enum,
)
from app.models.mixins import TimestampMixin


class Supplier(TimestampMixin, Base):
    """Layer B supplier entity (separate from core `Tour` catalog)."""

    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    api_credentials: Mapped[list["SupplierApiCredential"]] = relationship(
        back_populates="supplier",
        cascade="all, delete-orphan",
    )
    offers: Mapped[list["SupplierOffer"]] = relationship(
        back_populates="supplier",
        cascade="all, delete-orphan",
    )


class SupplierApiCredential(Base):
    """Opaque API token (stored hashed) scoped to one supplier."""

    __tablename__ = "supplier_api_credentials"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    supplier: Mapped["Supplier"] = relationship(back_populates="api_credentials")


class SupplierOffer(TimestampMixin, Base):
    """Supplier-owned offer draft (not a core `Tour` row — publication/moderation in later tracks)."""

    __tablename__ = "supplier_offers"
    __table_args__ = (
        CheckConstraint("seats_total >= 0", name="ck_supplier_offers_seats_total_non_negative"),
        CheckConstraint("base_price IS NULL OR base_price >= 0", name="ck_supplier_offers_base_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    supplier_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    program_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    departure_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    return_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    transport_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    vehicle_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    seats_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    base_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    service_composition: Mapped[SupplierServiceComposition] = mapped_column(
        sqlalchemy_enum(SupplierServiceComposition, name="supplier_service_composition"),
        nullable=False,
        default=SupplierServiceComposition.TRANSPORT_ONLY,
    )
    sales_mode: Mapped[TourSalesMode] = mapped_column(
        sqlalchemy_enum(TourSalesMode, name="tour_sales_mode"),
        nullable=False,
        default=TourSalesMode.PER_SEAT,
    )
    payment_mode: Mapped[SupplierOfferPaymentMode] = mapped_column(
        sqlalchemy_enum(SupplierOfferPaymentMode, name="supplier_offer_payment_mode"),
        nullable=False,
        default=SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
    )
    lifecycle_status: Mapped[SupplierOfferLifecycle] = mapped_column(
        sqlalchemy_enum(SupplierOfferLifecycle, name="supplier_offer_lifecycle"),
        nullable=False,
        default=SupplierOfferLifecycle.DRAFT,
    )
    moderation_rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    showcase_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    showcase_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    supplier: Mapped["Supplier"] = relationship(back_populates="offers")
