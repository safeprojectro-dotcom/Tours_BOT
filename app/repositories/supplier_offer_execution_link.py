from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus
from app.models.order import Order
from app.models.supplier import SupplierOfferExecutionLink
from app.models.tour import Tour


@dataclass(frozen=True)
class TourExecutionAggregates:
    seats_total: int
    seats_available: int
    active_reserved_hold_seats: int
    confirmed_paid_seats: int


class SupplierOfferExecutionLinkRepository:
    def get_active_for_offer(
        self,
        session: Session,
        *,
        supplier_offer_id: int,
        for_update: bool = False,
    ) -> SupplierOfferExecutionLink | None:
        stmt = (
            select(SupplierOfferExecutionLink)
            .where(
                SupplierOfferExecutionLink.supplier_offer_id == supplier_offer_id,
                SupplierOfferExecutionLink.link_status == "active",
            )
            .order_by(SupplierOfferExecutionLink.id.desc())
            .limit(1)
        )
        if for_update:
            stmt = stmt.with_for_update()
        return session.scalars(stmt).first()

    def list_for_offer(self, session: Session, *, supplier_offer_id: int) -> list[SupplierOfferExecutionLink]:
        stmt = (
            select(SupplierOfferExecutionLink)
            .where(SupplierOfferExecutionLink.supplier_offer_id == supplier_offer_id)
            .order_by(SupplierOfferExecutionLink.created_at.desc(), SupplierOfferExecutionLink.id.desc())
        )
        return list(session.scalars(stmt).all())

    def get_tour_execution_aggregates(
        self,
        session: Session,
        *,
        tour_id: int,
        now_utc: datetime,
    ) -> TourExecutionAggregates | None:
        tour = session.get(Tour, tour_id)
        if tour is None:
            return None

        active_hold_case = case(
            (
                and_(
                    Order.booking_status == BookingStatus.RESERVED,
                    Order.payment_status == PaymentStatus.AWAITING_PAYMENT,
                    Order.cancellation_status == CancellationStatus.ACTIVE,
                    Order.reservation_expires_at.is_not(None),
                    Order.reservation_expires_at > now_utc,
                ),
                Order.seats_count,
            ),
            else_=0,
        )
        confirmed_paid_case = case(
            (
                and_(
                    Order.booking_status.in_((BookingStatus.CONFIRMED, BookingStatus.READY_FOR_DEPARTURE)),
                    Order.payment_status == PaymentStatus.PAID,
                    Order.cancellation_status == CancellationStatus.ACTIVE,
                ),
                Order.seats_count,
            ),
            else_=0,
        )

        sums_stmt = select(
            func.coalesce(func.sum(active_hold_case), 0),
            func.coalesce(func.sum(confirmed_paid_case), 0),
        ).where(Order.tour_id == tour_id)
        hold_sum, confirmed_sum = session.execute(sums_stmt).one()
        return TourExecutionAggregates(
            seats_total=int(tour.seats_total),
            seats_available=int(tour.seats_available),
            active_reserved_hold_seats=int(hold_sum or 0),
            confirmed_paid_seats=int(confirmed_sum or 0),
        )
