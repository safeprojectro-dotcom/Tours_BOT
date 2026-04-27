"""B8: explicit admin generation of additional draft `Tour` rows from a packaging-approved supplier offer template.

- Reuses :meth:`SupplierOfferTourBridgeService.create_draft_tour_from_offer_dates` for **field mapping only**; does
  **not** create or update ``SupplierOfferTourBridge`` (that remains B10-only for the primary bridge when used).
- **Idempotency:** none. Re-posting the same parameters creates **more** draft tours and audit rows (accepted tech debt
  until a batch key or uniqueness on ``(source_supplier_offer_id, departure)`` is designed).
- **start_offset_days=0:** the first instance uses the template offer’s **same** ``departure_datetime`` /
  implied return. If a B10 bridge already materialized a ``Tour`` for that offer on those dates, operators may
  now have a **second** distinct draft for the same calendar slot — use ``start_offset_days`` / ops discipline to avoid.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.supplier import SupplierOffer
from app.repositories.supplier_offer_recurrence_generated_tour import (
    SupplierOfferRecurrenceGeneratedTourRepository,
)
from app.services.supplier_offer_tour_bridge_service import (
    SupplierOfferTourBridgeNotFoundError,
    SupplierOfferTourBridgeService,
    SupplierOfferTourBridgeValidationError,
)

if TYPE_CHECKING:
    pass


class SupplierOfferRecurrenceParameterError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class SupplierOfferRecurrenceDraftItem:
    tour_id: int
    sequence_index: int
    departure_datetime: object
    return_datetime: object


@dataclass(frozen=True, slots=True)
class SupplierOfferRecurrenceGenerationResult:
    source_supplier_offer_id: int
    items: list[SupplierOfferRecurrenceDraftItem]


_MAX_INSTANCES = 24
_MAX_INTERVAL_DAYS = 366
_MAX_START_OFFSET_DAYS = 730


class SupplierOfferRecurrenceService:
    def __init__(
        self,
        *,
        bridge: SupplierOfferTourBridgeService | None = None,
        audit_repo: SupplierOfferRecurrenceGeneratedTourRepository | None = None,
    ) -> None:
        self._bridge = bridge or SupplierOfferTourBridgeService()
        self._audit = audit_repo or SupplierOfferRecurrenceGeneratedTourRepository()

    @staticmethod
    def _lock_offer_for_update(session: Session, *, supplier_offer_id: int) -> None:
        stmt = select(SupplierOffer.id).where(SupplierOffer.id == supplier_offer_id).with_for_update()
        row = session.execute(stmt).one_or_none()
        if row is None:
            raise SupplierOfferTourBridgeNotFoundError()

    def generate_draft_tours(
        self,
        session: Session,
        *,
        supplier_offer_id: int,
        count: int,
        interval_days: int,
        start_offset_days: int = 0,
    ) -> SupplierOfferRecurrenceGenerationResult:
        """
        Create ``count`` draft tours by shifting the template offer's departure/return by calendar days.

        - Preserves trip length (return - departure) from the template offer.
        - Does **not** create ``SupplierOfferTourBridge`` rows; does **not** activate catalog; does **not** book.
        - Each generated tour is ``draft``; use B10.2 + execution links per product rules for bookability.
        """
        if count < 1 or count > _MAX_INSTANCES:
            raise SupplierOfferRecurrenceParameterError(
                "count_range",
                f"count must be between 1 and {_MAX_INSTANCES}.",
            )
        if interval_days < 1 or interval_days > _MAX_INTERVAL_DAYS:
            raise SupplierOfferRecurrenceParameterError(
                "interval_days_range",
                f"interval_days must be between 1 and {_MAX_INTERVAL_DAYS}.",
            )
        if start_offset_days < 0 or start_offset_days > _MAX_START_OFFSET_DAYS:
            raise SupplierOfferRecurrenceParameterError(
                "start_offset_range",
                f"start_offset_days must be between 0 and {_MAX_START_OFFSET_DAYS}.",
            )

        self._lock_offer_for_update(session, supplier_offer_id=supplier_offer_id)
        offer = session.get(SupplierOffer, supplier_offer_id)
        if offer is None:
            raise SupplierOfferTourBridgeNotFoundError()

        self._bridge.ensure_offer_eligible_for_tour_materialization(offer)

        span = offer.return_datetime - offer.departure_datetime
        items: list[SupplierOfferRecurrenceDraftItem] = []
        for i in range(count):
            offset_days = start_offset_days + i * interval_days
            dep = offer.departure_datetime + timedelta(days=offset_days)
            ret = dep + span
            if ret <= dep:
                raise SupplierOfferTourBridgeValidationError(["return_datetime_after_departure"])
            tour = self._bridge.create_draft_tour_from_offer_dates(
                session,
                offer=offer,
                departure_datetime=dep,
                return_datetime=ret,
                tour_code_prefix="B8R",
                skip_eligibility_check=True,
            )
            self._audit.create(
                session,
                source_supplier_offer_id=offer.id,
                tour_id=tour.id,
                sequence_index=i,
            )
            items.append(
                SupplierOfferRecurrenceDraftItem(
                    tour_id=tour.id,
                    sequence_index=i,
                    departure_datetime=tour.departure_datetime,
                    return_datetime=tour.return_datetime,
                )
            )

        return SupplierOfferRecurrenceGenerationResult(source_supplier_offer_id=offer.id, items=items)


__all__ = [
    "SupplierOfferRecurrenceService",
    "SupplierOfferRecurrenceGenerationResult",
    "SupplierOfferRecurrenceDraftItem",
    "SupplierOfferRecurrenceParameterError",
]
