from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

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
