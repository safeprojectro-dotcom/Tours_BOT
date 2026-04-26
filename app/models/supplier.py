from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    SupplierLegalEntityType,
    SupplierOnboardingStatus,
    SupplierOfferLifecycle,
    SupplierOfferPackagingStatus,
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
    primary_telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    onboarding_status: Mapped[SupplierOnboardingStatus] = mapped_column(
        sqlalchemy_enum(SupplierOnboardingStatus, name="supplier_onboarding_status"),
        nullable=False,
        default=SupplierOnboardingStatus.APPROVED,
    )
    onboarding_contact_info: Mapped[str | None] = mapped_column(String(255), nullable=True)
    onboarding_region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    legal_entity_type: Mapped[SupplierLegalEntityType | None] = mapped_column(
        sqlalchemy_enum(SupplierLegalEntityType, name="supplier_legal_entity_type"),
        nullable=True,
    )
    legal_registered_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    legal_registration_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    permit_license_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    permit_license_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    onboarding_service_composition: Mapped[SupplierServiceComposition | None] = mapped_column(
        sqlalchemy_enum(SupplierServiceComposition, name="supplier_service_composition"),
        nullable=True,
    )
    onboarding_fleet_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    onboarding_rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    onboarding_suspension_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    onboarding_revocation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    onboarding_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    onboarding_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    api_credentials: Mapped[list["SupplierApiCredential"]] = relationship(
        back_populates="supplier",
        cascade="all, delete-orphan",
    )
    offers: Mapped[list["SupplierOffer"]] = relationship(
        back_populates="supplier",
        cascade="all, delete-orphan",
    )
    custom_request_responses: Mapped[list["SupplierCustomRequestResponse"]] = relationship(
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
        CheckConstraint("discount_amount IS NULL OR discount_amount >= 0", name="ck_supplier_offers_discount_amount_non_negative"),
        CheckConstraint(
            "discount_percent IS NULL OR (discount_percent >= 0 AND discount_percent <= 100)",
            name="ck_supplier_offers_discount_percent_range",
        ),
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
    showcase_photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    boarding_places_text: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    # B2 — extended intake / packaging storage (no AI, no Tour, no publish logic changes)
    cover_media_reference: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    media_references: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    included_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    excluded_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_hook: Mapped[str | None] = mapped_column(String(512), nullable=True)
    marketing_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    discount_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    discount_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    discount_valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recurrence_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    recurrence_rule: Mapped[str | None] = mapped_column(Text, nullable=True)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    supplier_admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    packaging_status: Mapped[SupplierOfferPackagingStatus] = mapped_column(
        sqlalchemy_enum(SupplierOfferPackagingStatus, name="supplier_offer_packaging_status"),
        nullable=False,
        default=SupplierOfferPackagingStatus.NONE,
    )
    missing_fields_json: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    quality_warnings_json: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    # B4: AI/deterministic packaging extras (Telegram post draft, CTA list, Mini App bodies, layout hints). Admin read only.
    packaging_draft_json: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)

    supplier: Mapped["Supplier"] = relationship(back_populates="offers")
    execution_links: Mapped[list["SupplierOfferExecutionLink"]] = relationship(
        back_populates="supplier_offer",
        cascade="all, delete-orphan",
    )


class SupplierOfferExecutionLink(TimestampMixin, Base):
    """Explicit supplier_offer -> Layer A tour execution linkage (Y27.1)."""

    __tablename__ = "supplier_offer_execution_links"
    __table_args__ = (
        CheckConstraint("link_status IN ('active', 'closed')", name="ck_supplier_offer_exec_links_status"),
        CheckConstraint(
            "close_reason IS NULL OR close_reason IN ('replaced', 'unlinked', 'retracted', 'invalidated')",
            name="ck_supplier_offer_exec_links_close_reason",
        ),
        CheckConstraint(
            "("
            "(link_status = 'active' AND closed_at IS NULL AND close_reason IS NULL)"
            " OR "
            "(link_status = 'closed' AND closed_at IS NOT NULL)"
            ")",
            name="ck_supplier_offer_exec_links_active_closed_consistency",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_offer_id: Mapped[int] = mapped_column(
        ForeignKey("supplier_offers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tour_id: Mapped[int] = mapped_column(
        ForeignKey("tours.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    link_status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    close_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    link_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    supplier_offer: Mapped["SupplierOffer"] = relationship(back_populates="execution_links")
