from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus
from app.models.order import Order
from app.models.tour import Tour
from app.repositories.base import SQLAlchemyRepository


class OrderRepository(SQLAlchemyRepository[Order]):
    def __init__(self) -> None:
        super().__init__(Order)

    def get_for_update(self, session: Session, *, order_id: int) -> Order | None:
        stmt = select(Order).where(Order.id == order_id).with_for_update()
        return session.scalar(stmt)

    def get_by_id_for_admin_detail(self, session: Session, *, order_id: int) -> Order | None:
        """Single order for admin read-only detail; eager-loads display relations (no payments — loaded separately)."""
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.tour),
                selectinload(Order.boarding_point),
                selectinload(Order.handoffs),
            )
        )
        return session.scalar(stmt)

    def list_recent_for_admin(
        self,
        session: Session,
        *,
        limit: int = 100,
        offset: int = 0,
        tour_id: int | None = None,
        lifecycle_where: Any | None = None,
    ) -> list[Order]:
        """Recent orders for admin read-only lists (newest first); loads tour for display code."""
        stmt = select(Order).options(selectinload(Order.tour)).order_by(
            Order.created_at.desc(),
            Order.id.desc(),
        )
        if tour_id is not None:
            stmt = stmt.where(Order.tour_id == tour_id)
        if lifecycle_where is not None:
            stmt = stmt.where(lifecycle_where)
        stmt = stmt.offset(offset).limit(limit)
        return list(session.scalars(stmt).all())

    def list_by_user(self, session: Session, *, user_id: int, limit: int = 100, offset: int = 0) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc(), Order.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def list_by_tour(self, session: Session, *, tour_id: int, limit: int = 100, offset: int = 0) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.tour_id == tour_id)
            .order_by(Order.created_at.desc(), Order.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def list_by_booking_status(
        self,
        session: Session,
        *,
        booking_status: BookingStatus,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.booking_status == booking_status)
            .order_by(Order.created_at.desc(), Order.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def list_expired_temporary_reservation_ids(
        self,
        session: Session,
        *,
        now: datetime,
        limit: int = 100,
    ) -> list[int]:
        stmt = (
            select(Order.id)
            .where(
                Order.booking_status == BookingStatus.RESERVED,
                Order.payment_status == PaymentStatus.AWAITING_PAYMENT,
                Order.cancellation_status == CancellationStatus.ACTIVE,
                Order.reservation_expires_at.is_not(None),
                Order.reservation_expires_at <= now,
            )
            .order_by(Order.reservation_expires_at, Order.id)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def list_payment_pending_reminder_order_ids(
        self,
        session: Session,
        *,
        now: datetime,
        due_within: timedelta,
        limit: int = 100,
    ) -> list[int]:
        due_before = now + due_within
        stmt = (
            select(Order.id)
            .where(
                Order.booking_status == BookingStatus.RESERVED,
                Order.payment_status == PaymentStatus.AWAITING_PAYMENT,
                Order.cancellation_status == CancellationStatus.ACTIVE,
                Order.reservation_expires_at.is_not(None),
                Order.reservation_expires_at > now,
                Order.reservation_expires_at <= due_before,
            )
            .order_by(Order.reservation_expires_at, Order.id)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def list_predeparture_reminder_order_ids(
        self,
        session: Session,
        *,
        now: datetime,
        due_within: timedelta,
        limit: int = 100,
    ) -> list[int]:
        due_before = now + due_within
        stmt = (
            select(Order.id)
            .join(Tour, Tour.id == Order.tour_id)
            .where(
                Order.booking_status == BookingStatus.CONFIRMED,
                Order.payment_status == PaymentStatus.PAID,
                Order.cancellation_status == CancellationStatus.ACTIVE,
                Tour.departure_datetime > now,
                Tour.departure_datetime <= due_before,
            )
            .order_by(Tour.departure_datetime, Order.id)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def list_departure_day_reminder_order_ids(
        self,
        session: Session,
        *,
        now: datetime,
        due_within: timedelta,
        limit: int = 100,
    ) -> list[int]:
        due_before = now + due_within
        same_day_cutoff = datetime(
            year=now.year,
            month=now.month,
            day=now.day,
            tzinfo=now.tzinfo,
        ) + timedelta(days=1)
        effective_due_before = min(due_before, same_day_cutoff)
        stmt = (
            select(Order.id)
            .join(Tour, Tour.id == Order.tour_id)
            .where(
                Order.booking_status == BookingStatus.CONFIRMED,
                Order.payment_status == PaymentStatus.PAID,
                Order.cancellation_status == CancellationStatus.ACTIVE,
                Tour.departure_datetime > now,
                Tour.departure_datetime < same_day_cutoff,
                Tour.departure_datetime <= effective_due_before,
            )
            .order_by(Tour.departure_datetime, Order.id)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def list_post_trip_reminder_order_ids(
        self,
        session: Session,
        *,
        now: datetime,
        due_within: timedelta,
        limit: int = 100,
    ) -> list[int]:
        due_after = now - due_within
        stmt = (
            select(Order.id)
            .join(Tour, Tour.id == Order.tour_id)
            .where(
                Order.booking_status == BookingStatus.CONFIRMED,
                Order.payment_status == PaymentStatus.PAID,
                Order.cancellation_status == CancellationStatus.ACTIVE,
                Tour.return_datetime <= now,
                Tour.return_datetime > due_after,
            )
            .order_by(Tour.return_datetime.desc(), Order.id)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())
