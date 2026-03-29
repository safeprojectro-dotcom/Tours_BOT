from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import TourStatus
from app.models.tour import BoardingPoint, Tour, TourTranslation
from app.repositories.base import SQLAlchemyRepository


class TourRepository(SQLAlchemyRepository[Tour]):
    def __init__(self) -> None:
        super().__init__(Tour)

    def get_by_code(self, session: Session, *, code: str) -> Tour | None:
        stmt = select(Tour).where(Tour.code == code)
        return session.scalar(stmt)

    def get_for_update(self, session: Session, *, tour_id: int) -> Tour | None:
        stmt = select(Tour).where(Tour.id == tour_id).with_for_update()
        return session.scalar(stmt)

    def list_by_status(
        self,
        session: Session,
        *,
        status: TourStatus,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Tour]:
        stmt = (
            select(Tour)
            .where(Tour.status == status)
            .order_by(Tour.departure_datetime, Tour.id)
            .offset(offset)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())


class TourTranslationRepository(SQLAlchemyRepository[TourTranslation]):
    def __init__(self) -> None:
        super().__init__(TourTranslation)

    def list_by_tour(self, session: Session, *, tour_id: int) -> list[TourTranslation]:
        stmt = (
            select(TourTranslation)
            .where(TourTranslation.tour_id == tour_id)
            .order_by(TourTranslation.language_code, TourTranslation.id)
        )
        return list(session.scalars(stmt).all())

    def get_by_tour_and_language(
        self,
        session: Session,
        *,
        tour_id: int,
        language_code: str,
    ) -> TourTranslation | None:
        stmt = select(TourTranslation).where(
            TourTranslation.tour_id == tour_id,
            TourTranslation.language_code == language_code,
        )
        return session.scalar(stmt)


class BoardingPointRepository(SQLAlchemyRepository[BoardingPoint]):
    def __init__(self) -> None:
        super().__init__(BoardingPoint)

    def list_by_tour(self, session: Session, *, tour_id: int) -> list[BoardingPoint]:
        stmt = (
            select(BoardingPoint)
            .where(BoardingPoint.tour_id == tour_id)
            .order_by(BoardingPoint.time, BoardingPoint.id)
        )
        return list(session.scalars(stmt).all())
