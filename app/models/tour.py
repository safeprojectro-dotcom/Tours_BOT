from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TourStatus, sqlalchemy_enum
from app.models.mixins import TimestampMixin


class Tour(TimestampMixin, Base):
    __tablename__ = "tours"
    __table_args__ = (
        CheckConstraint("duration_days > 0", name="ck_tours_duration_days_positive"),
        CheckConstraint("base_price >= 0", name="ck_tours_base_price_non_negative"),
        CheckConstraint("seats_total >= 0", name="ck_tours_seats_total_non_negative"),
        CheckConstraint("seats_available >= 0", name="ck_tours_seats_available_non_negative"),
        CheckConstraint("seats_available <= seats_total", name="ck_tours_seats_available_le_total"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title_default: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description_default: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_description_default: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    departure_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    return_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    seats_total: Mapped[int] = mapped_column(Integer, nullable=False)
    seats_available: Mapped[int] = mapped_column(Integer, nullable=False)
    sales_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[TourStatus] = mapped_column(
        sqlalchemy_enum(TourStatus, name="tour_status"),
        nullable=False,
        default=TourStatus.DRAFT,
    )
    guaranteed_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    translations: Mapped[list["TourTranslation"]] = relationship(
        back_populates="tour",
        cascade="all, delete-orphan",
    )
    boarding_points: Mapped[list["BoardingPoint"]] = relationship(
        back_populates="tour",
        cascade="all, delete-orphan",
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="tour")
    waitlist_entries: Mapped[list["WaitlistEntry"]] = relationship(back_populates="tour")
    content_items: Mapped[list["ContentItem"]] = relationship(back_populates="tour")


class TourTranslation(Base):
    __tablename__ = "tour_translations"
    __table_args__ = (UniqueConstraint("tour_id", "language_code", name="uq_tour_translation_language"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tour_id: Mapped[int] = mapped_column(
        ForeignKey("tours.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    language_code: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    program_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    included_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    excluded_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    tour: Mapped["Tour"] = relationship(back_populates="translations")


class BoardingPoint(Base):
    __tablename__ = "boarding_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    tour_id: Mapped[int] = mapped_column(
        ForeignKey("tours.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    time: Mapped[time] = mapped_column(Time, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    tour: Mapped["Tour"] = relationship(back_populates="boarding_points")
    orders: Mapped[list["Order"]] = relationship(back_populates="boarding_point")
