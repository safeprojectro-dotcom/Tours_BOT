"""Admin tour mutations — narrow slices; validation stays here (not in routes)."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.tour import TourRepository
from app.schemas.admin import AdminTourCreate, AdminTourDetailRead
from app.services.admin_read import AdminReadService


class AdminTourCreateValidationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AdminTourDuplicateCodeError(Exception):
    """Another tour already uses this code (or unique constraint race)."""


class AdminTourWriteService:
    def __init__(
        self,
        *,
        tour_repository: TourRepository | None = None,
        read_service: AdminReadService | None = None,
    ) -> None:
        self._tours = tour_repository or TourRepository()
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
