from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferLifecycle, TourStatus
from app.models.supplier import SupplierOfferExecutionLink
from app.models.tour import Tour
from app.repositories.supplier import SupplierOfferRepository
from app.repositories.supplier_offer_execution_link import SupplierOfferExecutionLinkRepository
from app.schemas.supplier_admin import SupplierOfferExecutionLinkRead


class SupplierOfferExecutionLinkNotFoundError(Exception):
    pass


class SupplierOfferExecutionLinkValidationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class SupplierOfferExecutionMetrics:
    declared_capacity: int
    occupied_capacity: int
    remaining_capacity: int
    active_reserved_hold_seats: int
    confirmed_paid_seats: int
    sold_out: bool


class SupplierOfferExecutionLinkService:
    _CLOSE_REASONS = {"replaced", "unlinked", "retracted", "invalidated"}

    def __init__(self) -> None:
        self._offers = SupplierOfferRepository()
        self._links = SupplierOfferExecutionLinkRepository()

    def _to_read(self, row: SupplierOfferExecutionLink) -> SupplierOfferExecutionLinkRead:
        return SupplierOfferExecutionLinkRead.model_validate(row, from_attributes=True)

    def _validate_link_target(self, session: Session, *, offer_id: int, tour_id: int) -> None:
        offer = self._offers.get_any(session, offer_id=offer_id)
        if offer is None:
            raise SupplierOfferExecutionLinkNotFoundError
        if offer.lifecycle_status != SupplierOfferLifecycle.PUBLISHED:
            raise SupplierOfferExecutionLinkValidationError("Only published offers can be linked to execution tours.")

        tour = session.get(Tour, tour_id)
        if tour is None:
            raise SupplierOfferExecutionLinkValidationError("Tour not found for execution linkage.")
        if tour.sales_mode != offer.sales_mode:
            raise SupplierOfferExecutionLinkValidationError("Tour sales_mode must match supplier offer sales_mode.")
        if tour.status in (TourStatus.CANCELLED, TourStatus.COMPLETED):
            raise SupplierOfferExecutionLinkValidationError("Tour status is not valid for operational linkage.")
        if tour.departure_datetime <= datetime.now(UTC):
            raise SupplierOfferExecutionLinkValidationError("Only future-departure tours can be linked.")

    def link_offer_to_tour(
        self,
        session: Session,
        *,
        offer_id: int,
        tour_id: int,
        link_note: str | None = None,
    ) -> SupplierOfferExecutionLinkRead:
        return self.replace_link_for_offer(
            session,
            offer_id=offer_id,
            tour_id=tour_id,
            link_note=link_note,
        )

    def create_link_for_offer(
        self,
        session: Session,
        *,
        offer_id: int,
        tour_id: int,
        link_note: str | None = None,
    ) -> SupplierOfferExecutionLinkRead:
        self._validate_link_target(session, offer_id=offer_id, tour_id=tour_id)
        active = self._links.get_active_for_offer(session, supplier_offer_id=offer_id, for_update=True)
        if active is not None:
            raise SupplierOfferExecutionLinkValidationError("Active execution link already exists for this offer.")

        row = SupplierOfferExecutionLink(
            supplier_offer_id=offer_id,
            tour_id=tour_id,
            link_status="active",
            close_reason=None,
            link_note=(link_note or "").strip() or None,
            closed_at=None,
        )
        session.add(row)
        session.flush()
        session.refresh(row)
        return self._to_read(row)

    def replace_link_for_offer(
        self,
        session: Session,
        *,
        offer_id: int,
        tour_id: int,
        link_note: str | None = None,
    ) -> SupplierOfferExecutionLinkRead:
        self._validate_link_target(session, offer_id=offer_id, tour_id=tour_id)
        now = datetime.now(UTC)
        active = self._links.get_active_for_offer(session, supplier_offer_id=offer_id, for_update=True)
        if active is not None and active.tour_id == tour_id:
            return self._to_read(active)
        if active is not None:
            active.link_status = "closed"
            active.close_reason = "replaced"
            active.closed_at = now
            session.add(active)
            session.flush()

        row = SupplierOfferExecutionLink(
            supplier_offer_id=offer_id,
            tour_id=tour_id,
            link_status="active",
            close_reason=None,
            link_note=(link_note or "").strip() or None,
            closed_at=None,
        )
        session.add(row)
        session.flush()
        session.refresh(row)
        return self._to_read(row)

    def close_active_link(
        self,
        session: Session,
        *,
        offer_id: int,
        reason: str = "unlinked",
        allow_missing: bool = False,
    ) -> SupplierOfferExecutionLinkRead | None:
        if reason not in self._CLOSE_REASONS:
            raise SupplierOfferExecutionLinkValidationError("Invalid close reason for execution linkage.")
        active = self._links.get_active_for_offer(session, supplier_offer_id=offer_id, for_update=True)
        if active is None:
            if allow_missing:
                return None
            raise SupplierOfferExecutionLinkNotFoundError
        active.link_status = "closed"
        active.close_reason = reason
        active.closed_at = datetime.now(UTC)
        session.add(active)
        session.flush()
        session.refresh(active)
        return self._to_read(active)

    def active_metrics_for_offer(
        self,
        session: Session,
        *,
        offer_id: int,
        now_utc: datetime | None = None,
    ) -> SupplierOfferExecutionMetrics | None:
        active = self._links.get_active_for_offer(session, supplier_offer_id=offer_id, for_update=False)
        if active is None:
            return None
        aggr = self._links.get_tour_execution_aggregates(
            session,
            tour_id=active.tour_id,
            now_utc=now_utc or datetime.now(UTC),
        )
        if aggr is None:
            return None
        occupied = max(aggr.seats_total - aggr.seats_available, 0)
        return SupplierOfferExecutionMetrics(
            declared_capacity=aggr.seats_total,
            occupied_capacity=occupied,
            remaining_capacity=max(aggr.seats_available, 0),
            active_reserved_hold_seats=max(aggr.active_reserved_hold_seats, 0),
            confirmed_paid_seats=max(aggr.confirmed_paid_seats, 0),
            sold_out=aggr.seats_available <= 0,
        )

    def list_links_for_offer(
        self,
        session: Session,
        *,
        offer_id: int,
    ) -> list[SupplierOfferExecutionLinkRead]:
        offer = self._offers.get_any(session, offer_id=offer_id)
        if offer is None:
            raise SupplierOfferExecutionLinkNotFoundError
        rows = self._links.list_for_offer(session, supplier_offer_id=offer_id)
        return [self._to_read(row) for row in rows]
