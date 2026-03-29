from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.tour import BoardingPointRepository
from app.schemas.tour import BoardingPointRead


class BoardingPointService:
    def __init__(self, boarding_point_repository: BoardingPointRepository | None = None) -> None:
        self.boarding_point_repository = boarding_point_repository or BoardingPointRepository()

    def list_by_tour(self, session: Session, *, tour_id: int) -> list[BoardingPointRead]:
        boarding_points = self.boarding_point_repository.list_by_tour(session, tour_id=tour_id)
        return [BoardingPointRead.model_validate(item) for item in boarding_points]
