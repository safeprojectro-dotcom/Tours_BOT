from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.tour import BoardingPointRepository, TourRepository, TourTranslationRepository
from app.schemas.tour import BoardingPointRead, TourDetailRead, TourRead, TourTranslationRead


class TourDetailService:
    def __init__(
        self,
        tour_repository: TourRepository | None = None,
        translation_repository: TourTranslationRepository | None = None,
        boarding_point_repository: BoardingPointRepository | None = None,
    ) -> None:
        self.tour_repository = tour_repository or TourRepository()
        self.translation_repository = translation_repository or TourTranslationRepository()
        self.boarding_point_repository = boarding_point_repository or BoardingPointRepository()

    def get_tour_detail(self, session: Session, *, tour_id: int) -> TourDetailRead | None:
        tour = self.tour_repository.get(session, tour_id)
        if tour is None:
            return None

        translations = self.translation_repository.list_by_tour(session, tour_id=tour_id)
        boarding_points = self.boarding_point_repository.list_by_tour(session, tour_id=tour_id)

        return TourDetailRead(
            tour=TourRead.model_validate(tour),
            translations=[TourTranslationRead.model_validate(item) for item in translations],
            boarding_points=[BoardingPointRead.model_validate(item) for item in boarding_points],
        )
