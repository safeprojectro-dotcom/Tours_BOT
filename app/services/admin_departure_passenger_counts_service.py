"""S1A: read-only departure passenger aggregates from Layer A orders + tour inventory."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus
from app.models.order import Order
from app.models.supplier import Supplier, SupplierOffer, SupplierOfferExecutionLink
from app.models.supplier_offer_tour_bridge import SupplierOfferTourBridge
from app.models.tour import Tour
from app.repositories.supplier_offer_execution_link import SupplierOfferExecutionLinkRepository
from app.repositories.supplier_offer_tour_bridge import SupplierOfferTourBridgeRepository
from app.repositories.tour import TourRepository
from app.schemas.admin_departure_passenger_counts import (
    AdminDeparturePassengerCountsListRead,
    AdminDeparturePassengerCountsRead,
    AdminDepartureSupplierAssociationRead,
)

ResolutionSource = Literal["tour_scoped", "supplier_offer_execution_link", "supplier_offer_tour_bridge"]


@dataclass(frozen=True)
class _OrderBuckets:
    total_orders_count: int
    active_orders_count: int
    reserved_unpaid_orders_count: int
    paid_confirmed_orders_count: int
    cancelled_orders_count: int
    other_active_orders_count: int
    active_passenger_count: int
    reserved_unpaid_passenger_count: int
    paid_confirmed_passenger_count: int
    cancelled_passenger_count: int
    other_active_passenger_count: int


class AdminDeparturePassengerCountsService:
    """Read-only aggregates for supplier departure ops (no notifications, no manifest)."""

    def __init__(
        self,
        *,
        tour_repository: TourRepository | None = None,
        execution_link_repository: SupplierOfferExecutionLinkRepository | None = None,
        tour_bridge_repository: SupplierOfferTourBridgeRepository | None = None,
    ) -> None:
        self._tours = tour_repository or TourRepository()
        self._exec_links = execution_link_repository or SupplierOfferExecutionLinkRepository()
        self._bridges = tour_bridge_repository or SupplierOfferTourBridgeRepository()

    def read_for_tour(
        self,
        session: Session,
        *,
        tour_id: int,
        now: datetime | None = None,
        resolution_source: ResolutionSource | None = "tour_scoped",
    ) -> AdminDeparturePassengerCountsRead | None:
        tour = self._tours.get(session, tour_id)
        if tour is None:
            return None
        return self._build_read(session, tour=tour, now=now, resolution_source=resolution_source)

    def read_for_supplier_offer(
        self,
        session: Session,
        *,
        supplier_offer_id: int,
        now: datetime | None = None,
    ) -> AdminDeparturePassengerCountsRead | None:
        link = self._exec_links.get_active_for_offer(session, supplier_offer_id=supplier_offer_id)
        if link is not None:
            return self.read_for_tour(
                session,
                tour_id=link.tour_id,
                now=now,
                resolution_source="supplier_offer_execution_link",
            )
        bridge = self._bridges.get_active_for_offer(session, supplier_offer_id=supplier_offer_id)
        if bridge is not None:
            return self.read_for_tour(
                session,
                tour_id=bridge.tour_id,
                now=now,
                resolution_source="supplier_offer_tour_bridge",
            )
        return None

    def list_for_supplier(
        self,
        session: Session,
        *,
        supplier_id: int,
        now: datetime | None = None,
    ) -> AdminDeparturePassengerCountsListRead:
        current = now or datetime.now(UTC)
        tour_ids = self._distinct_tour_ids_for_supplier(session, supplier_id=supplier_id)
        global_warnings: list[str] = []
        if not tour_ids:
            global_warnings.append("s1a_supplier_no_active_tour_links")

        items: list[AdminDeparturePassengerCountsRead] = []
        for tid in sorted(tour_ids):
            row = self.read_for_tour(session, tour_id=tid, now=current, resolution_source="tour_scoped")
            if row is not None:
                items.append(row)

        items.sort(key=lambda r: r.departure_datetime)
        return AdminDeparturePassengerCountsListRead(
            supplier_id=supplier_id,
            items=items,
            readiness_warnings=global_warnings,
            computed_at_utc=current,
        )

    def _distinct_tour_ids_for_supplier(self, session: Session, *, supplier_id: int) -> set[int]:
        offer_ids_stmt = select(SupplierOffer.id).where(SupplierOffer.supplier_id == supplier_id)
        offer_ids = {int(x) for x in session.scalars(offer_ids_stmt).all()}
        if not offer_ids:
            return set()

        exec_stmt = select(SupplierOfferExecutionLink.tour_id).where(
            SupplierOfferExecutionLink.supplier_offer_id.in_(offer_ids),
            SupplierOfferExecutionLink.link_status == "active",
        )
        bridge_stmt = select(SupplierOfferTourBridge.tour_id).where(
            SupplierOfferTourBridge.supplier_offer_id.in_(offer_ids),
            SupplierOfferTourBridge.status == "active",
        )

        from_exec = {int(x) for x in session.scalars(exec_stmt).all()}
        from_bridge = {int(x) for x in session.scalars(bridge_stmt).all()}
        return from_exec | from_bridge

    def _build_read(
        self,
        session: Session,
        *,
        tour: Tour,
        now: datetime | None,
        resolution_source: ResolutionSource | None,
    ) -> AdminDeparturePassengerCountsRead:
        current = now or datetime.now(UTC)
        orders = list(session.scalars(select(Order).where(Order.tour_id == tour.id).order_by(Order.id.asc())).all())
        buckets = self._bucket_orders(orders)
        warnings = self._warnings_for_orders_inventory(
            orders=orders,
            tour=tour,
            buckets=buckets,
            now=current,
        )

        assoc = self._supplier_associations(session, tour_id=tour.id)
        load_pct = None
        if tour.seats_total > 0:
            load_pct = round(100.0 * (tour.seats_total - tour.seats_available) / tour.seats_total, 2)
            load_pct = max(0.0, min(100.0, load_pct))

        return AdminDeparturePassengerCountsRead(
            tour_id=tour.id,
            tour_code=tour.code,
            tour_title_default=tour.title_default,
            departure_datetime=tour.departure_datetime,
            total_orders_count=buckets.total_orders_count,
            active_orders_count=buckets.active_orders_count,
            reserved_unpaid_orders_count=buckets.reserved_unpaid_orders_count,
            paid_confirmed_orders_count=buckets.paid_confirmed_orders_count,
            cancelled_orders_count=buckets.cancelled_orders_count,
            other_active_orders_count=buckets.other_active_orders_count,
            active_passenger_count=buckets.active_passenger_count,
            reserved_unpaid_passenger_count=buckets.reserved_unpaid_passenger_count,
            paid_confirmed_passenger_count=buckets.paid_confirmed_passenger_count,
            cancelled_passenger_count=buckets.cancelled_passenger_count,
            other_active_passenger_count=buckets.other_active_passenger_count,
            capacity=tour.seats_total,
            seats_available=tour.seats_available,
            remaining_capacity=tour.seats_available,
            load_percentage=load_pct,
            supplier_associations=assoc,
            readiness_warnings=warnings,
            computed_at_utc=current,
            resolution_source=resolution_source,
        )

    def _supplier_associations(self, session: Session, *, tour_id: int) -> list[AdminDepartureSupplierAssociationRead]:
        rows: dict[tuple[int, str], AdminDepartureSupplierAssociationRead] = {}

        el_stmt = (
            select(SupplierOfferExecutionLink, SupplierOffer, Supplier)
            .join(SupplierOffer, SupplierOffer.id == SupplierOfferExecutionLink.supplier_offer_id)
            .join(Supplier, Supplier.id == SupplierOffer.supplier_id)
            .where(
                SupplierOfferExecutionLink.tour_id == tour_id,
                SupplierOfferExecutionLink.link_status == "active",
            )
            .order_by(SupplierOfferExecutionLink.id.desc())
        )
        for _link, offer, sup in session.execute(el_stmt).all():
            key = (offer.id, "execution_link")
            rows[key] = AdminDepartureSupplierAssociationRead(
                supplier_id=sup.id,
                supplier_code=sup.code,
                supplier_display_name=sup.display_name,
                supplier_offer_id=offer.id,
                supplier_offer_title=offer.title,
                association_kind="execution_link",
            )

        br_stmt = (
            select(SupplierOfferTourBridge, SupplierOffer, Supplier)
            .join(SupplierOffer, SupplierOffer.id == SupplierOfferTourBridge.supplier_offer_id)
            .join(Supplier, Supplier.id == SupplierOffer.supplier_id)
            .where(
                SupplierOfferTourBridge.tour_id == tour_id,
                SupplierOfferTourBridge.status == "active",
            )
            .order_by(SupplierOfferTourBridge.id.desc())
        )
        for _bridge, offer, sup in session.execute(br_stmt).all():
            key = (offer.id, "tour_bridge")
            rows[key] = AdminDepartureSupplierAssociationRead(
                supplier_id=sup.id,
                supplier_code=sup.code,
                supplier_display_name=sup.display_name,
                supplier_offer_id=offer.id,
                supplier_offer_title=offer.title,
                association_kind="tour_bridge",
            )

        return sorted(rows.values(), key=lambda r: (r.supplier_code, r.supplier_offer_id, r.association_kind))

    def _bucket_orders(self, orders: list[Order]) -> _OrderBuckets:
        total_orders = len(orders)
        c_res_unpaid_o = c_paid_o = c_cancelled_o = c_other_o = 0
        s_ru = s_paid = s_cx = s_other = 0
        for o in orders:
            seats = int(o.seats_count)
            if o.cancellation_status != CancellationStatus.ACTIVE:
                c_cancelled_o += 1
                s_cx += seats
                continue

            if o.payment_status == PaymentStatus.PAID:
                c_paid_o += 1
                s_paid += seats
                continue

            if o.booking_status == BookingStatus.RESERVED and o.payment_status in (
                PaymentStatus.AWAITING_PAYMENT,
                PaymentStatus.UNPAID,
            ):
                c_res_unpaid_o += 1
                s_ru += seats
                continue

            c_other_o += 1
            s_other += seats

        active_o = c_res_unpaid_o + c_paid_o + c_other_o
        active_pax = s_ru + s_paid + s_other
        return _OrderBuckets(
            total_orders_count=total_orders,
            active_orders_count=active_o,
            reserved_unpaid_orders_count=c_res_unpaid_o,
            paid_confirmed_orders_count=c_paid_o,
            cancelled_orders_count=c_cancelled_o,
            other_active_orders_count=c_other_o,
            active_passenger_count=active_pax,
            reserved_unpaid_passenger_count=s_ru,
            paid_confirmed_passenger_count=s_paid,
            cancelled_passenger_count=s_cx,
            other_active_passenger_count=s_other,
        )

    def _warnings_for_orders_inventory(
        self,
        *,
        orders: list[Order],
        tour: Tour,
        buckets: _OrderBuckets,
        now: datetime,
    ) -> list[str]:
        warnings: list[str] = []

        if buckets.other_active_orders_count:
            warnings.append("s1a_unexpected_active_order_state_mix")

        inventory_held = max(0, int(tour.seats_total) - int(tour.seats_available))
        if inventory_held != buckets.active_passenger_count:
            warnings.append("s1a_inventory_vs_active_order_seats_mismatch")

        for o in orders:
            if (
                o.cancellation_status == CancellationStatus.ACTIVE
                and o.booking_status == BookingStatus.RESERVED
                and o.payment_status == PaymentStatus.AWAITING_PAYMENT
                and o.reservation_expires_at is not None
                and o.reservation_expires_at <= now
            ):
                warnings.append("s1a_expired_temporary_hold_not_released")
                break

        return warnings
