from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import TourStatus
from app.repositories.tour import TourRepository
from app.schemas.tour import TourRead


class CatalogLookupService:
    def __init__(self, tour_repository: TourRepository | None = None) -> None:
        self.tour_repository = tour_repository or TourRepository()

    def list_tours(
        self,
        session: Session,
        *,
        status: TourStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TourRead]:
        if status is None:
            tours = self.tour_repository.list(session, limit=limit, offset=offset)
        else:
            tours = self.tour_repository.list_by_status(
                session,
                status=status,
                limit=limit,
                offset=offset,
            )
        return [TourRead.model_validate(tour) for tour in tours]

    def get_tour_by_code(self, session: Session, *, code: str) -> TourRead | None:
        tour = self.tour_repository.get_by_code(session, code=code)
        if tour is None:
            return None
        return TourRead.model_validate(tour)
