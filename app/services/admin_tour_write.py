"""Admin tour mutations — narrow slices; validation stays here (not in routes)."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.tour import BoardingPoint, Tour
from app.repositories.tour import BoardingPointRepository, TourRepository
from app.schemas.admin import (
    AdminBoardingPointCreate,
    AdminBoardingPointUpdate,
    AdminTourCoreUpdate,
    AdminTourCoverSet,
    AdminTourCreate,
    AdminTourDetailRead,
)
from app.services.admin_read import AdminReadService


class AdminTourCreateValidationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AdminTourDuplicateCodeError(Exception):
    """Another tour already uses this code (or unique constraint race)."""


class AdminTourNotFoundError(Exception):
    """No tour row for the given id."""


class AdminBoardingPointNotFoundError(Exception):
    """No boarding point row for the given id."""


class AdminTourWriteService:
    def __init__(
        self,
        *,
        tour_repository: TourRepository | None = None,
        boarding_point_repository: BoardingPointRepository | None = None,
        read_service: AdminReadService | None = None,
    ) -> None:
        self._tours = tour_repository or TourRepository()
        self._boarding_points = boarding_point_repository or BoardingPointRepository()
        self._read = read_service or AdminReadService()

    def create_tour(self, session: Session, *, payload: AdminTourCreate) -> AdminTourDetailRead:
        code = payload.code
        if self._tours.get_by_code(session, code=code) is not None:
            raise AdminTourDuplicateCodeError()

        if payload.return_datetime <= payload.departure_datetime:
            raise AdminTourCreateValidationError("return_datetime must be after departure_datetime.")

        if payload.sales_deadline is not None and payload.sales_deadline >= payload.departure_datetime:
            raise AdminTourCreateValidationError("sales_deadline must be before departure_datetime.")

        seats_available = payload.seats_total

        data = {
            "code": code,
            "title_default": payload.title_default,
            "short_description_default": payload.short_description_default,
            "full_description_default": payload.full_description_default,
            "duration_days": payload.duration_days,
            "departure_datetime": payload.departure_datetime,
            "return_datetime": payload.return_datetime,
            "base_price": payload.base_price,
            "currency": payload.currency,
            "seats_total": payload.seats_total,
            "seats_available": seats_available,
            "sales_deadline": payload.sales_deadline,
            "status": payload.status,
            "guaranteed_flag": payload.guaranteed_flag,
        }

        try:
            tour = self._tours.create(session, data=data)
        except IntegrityError as exc:
            session.rollback()
            raise AdminTourDuplicateCodeError() from exc

        detail = self._read.get_tour_detail(session, tour_id=tour.id)
        assert detail is not None
        return detail

    def set_tour_cover(
        self,
        session: Session,
        *,
        tour_id: int,
        payload: AdminTourCoverSet,
    ) -> AdminTourDetailRead:
        ref = payload.cover_media_reference
        updated = self._tours.set_cover_media_reference(
            session,
            tour_id=tour_id,
            cover_media_reference=ref,
        )
        if updated is None:
            raise AdminTourNotFoundError()

        detail = self._read.get_tour_detail(session, tour_id=tour_id)
        assert detail is not None
        return detail

    def update_tour_core(
        self,
        session: Session,
        *,
        tour_id: int,
        payload: AdminTourCoreUpdate,
    ) -> AdminTourDetailRead:
        """
        Patch core tour fields. Seats rule (conservative): let committed = seats_total - seats_available
        (inventory already allocated away from the free pool). When seats_total changes, require
        new_total >= committed and set seats_available = new_total - committed. Does not attempt
        to reconcile order rows — only enforces non-negative remaining capacity.
        """
        tour = session.get(Tour, tour_id)
        if tour is None:
            raise AdminTourNotFoundError()

        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise AdminTourCreateValidationError("No fields to update.")

        departure = updates.get("departure_datetime", tour.departure_datetime)
        return_dt = updates.get("return_datetime", tour.return_datetime)
        if return_dt <= departure:
            raise AdminTourCreateValidationError("return_datetime must be after departure_datetime.")

        sales_deadline = (
            updates["sales_deadline"] if "sales_deadline" in updates else tour.sales_deadline
        )
        if sales_deadline is not None and sales_deadline >= departure:
            raise AdminTourCreateValidationError("sales_deadline must be before departure_datetime.")

        committed_seats = tour.seats_total - tour.seats_available
        if "seats_total" in updates:
            new_total = updates["seats_total"]
            if new_total < committed_seats:
                raise AdminTourCreateValidationError(
                    "seats_total cannot be less than seats already allocated "
                    f"({committed_seats} seats; computed as seats_total minus seats_available).",
                )
            # Keep remaining sellable seats coherent: new_available = new_total - committed
            updates["seats_available"] = new_total - committed_seats

        self._tours.update_core_fields(session, tour_id=tour_id, fields=updates)

        detail = self._read.get_tour_detail(session, tour_id=tour_id)
        assert detail is not None
        return detail

    def add_boarding_point(
        self,
        session: Session,
        *,
        tour_id: int,
        payload: AdminBoardingPointCreate,
    ) -> AdminTourDetailRead:
        """Create one boarding point row for an existing tour; returns refreshed admin tour detail."""
        tour = session.get(Tour, tour_id)
        if tour is None:
            raise AdminTourNotFoundError()

        self._boarding_points.create_for_tour(
            session,
            tour_id=tour_id,
            city=payload.city,
            address=payload.address,
            boarding_time=payload.time,
            notes=payload.notes,
        )

        detail = self._read.get_tour_detail(session, tour_id=tour_id)
        assert detail is not None
        return detail

    def update_boarding_point(
        self,
        session: Session,
        *,
        boarding_point_id: int,
        payload: AdminBoardingPointUpdate,
    ) -> AdminTourDetailRead:
        """Patch core boarding point fields; tour association is fixed (no reassignment). Returns refreshed tour detail."""
        bp = session.get(BoardingPoint, boarding_point_id)
        if bp is None:
            raise AdminBoardingPointNotFoundError()

        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise AdminTourCreateValidationError("No fields to update.")

        for key in ("city", "address", "time"):
            if key in updates and updates[key] is None:
                raise AdminTourCreateValidationError(f"{key} cannot be cleared.")

        self._boarding_points.update_core_fields(
            session,
            boarding_point_id=boarding_point_id,
            fields=updates,
        )

        detail = self._read.get_tour_detail(session, tour_id=bp.tour_id)
        assert detail is not None
        return detail
