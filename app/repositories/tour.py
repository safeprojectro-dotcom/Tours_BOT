from __future__ import annotations

from datetime import time as time_type
from typing import Any, Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import TourStatus
from app.models.tour import BoardingPoint, BoardingPointTranslation, Tour, TourTranslation
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

    def update_core_fields(
        self,
        session: Session,
        *,
        tour_id: int,
        fields: Mapping[str, Any],
    ) -> Tour | None:
        """Apply allowed core column updates; caller supplies validated mapping including seats if changed."""
        tour = session.get(Tour, tour_id)
        if tour is None:
            return None
        for key, value in fields.items():
            setattr(tour, key, value)
        session.add(tour)
        session.flush()
        session.refresh(tour)
        return tour

    def set_cover_media_reference(
        self,
        session: Session,
        *,
        tour_id: int,
        cover_media_reference: str,
    ) -> Tour | None:
        """Persist a single cover/media reference; returns None if tour id missing."""
        tour = session.get(Tour, tour_id)
        if tour is None:
            return None
        tour.cover_media_reference = cover_media_reference
        session.add(tour)
        session.flush()
        session.refresh(tour)
        return tour

    def get_by_id_for_admin_detail(self, session: Session, *, tour_id: int) -> Tour | None:
        """Single tour for admin read-only detail; eager-loads translations and boarding points."""
        stmt = (
            select(Tour)
            .where(Tour.id == tour_id)
            .options(
                selectinload(Tour.translations),
                selectinload(Tour.boarding_points).selectinload(BoardingPoint.translations),
            )
        )
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

    def list_by_departure_desc(
        self,
        session: Session,
        *,
        limit: int = 100,
        offset: int = 0,
        status: TourStatus | None = None,
        guaranteed_only: bool = False,
    ) -> list[Tour]:
        """Recent/upcoming tours for admin read-only lists (newest departure first)."""
        stmt = select(Tour).order_by(Tour.departure_datetime.desc(), Tour.id.desc())
        if status is not None:
            stmt = stmt.where(Tour.status == status)
        if guaranteed_only:
            stmt = stmt.where(Tour.guaranteed_flag.is_(True))
        stmt = stmt.offset(offset).limit(limit)
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

    def update_fields_for_tour_language(
        self,
        session: Session,
        *,
        tour_id: int,
        language_code: str,
        fields: Mapping[str, Any],
    ) -> TourTranslation | None:
        tr = self.get_by_tour_and_language(session, tour_id=tour_id, language_code=language_code)
        if tr is None:
            return None
        for key, value in fields.items():
            setattr(tr, key, value)
        session.add(tr)
        session.flush()
        session.refresh(tr)
        return tr

    def delete_for_tour_language(
        self,
        session: Session,
        *,
        tour_id: int,
        language_code: str,
    ) -> bool:
        tr = self.get_by_tour_and_language(session, tour_id=tour_id, language_code=language_code)
        if tr is None:
            return False
        self.delete(session, instance=tr)
        return True


class BoardingPointTranslationRepository(SQLAlchemyRepository[BoardingPointTranslation]):
    def __init__(self) -> None:
        super().__init__(BoardingPointTranslation)

    def get_by_boarding_point_and_language(
        self,
        session: Session,
        *,
        boarding_point_id: int,
        language_code: str,
    ) -> BoardingPointTranslation | None:
        stmt = select(BoardingPointTranslation).where(
            BoardingPointTranslation.boarding_point_id == boarding_point_id,
            BoardingPointTranslation.language_code == language_code,
        )
        return session.scalar(stmt)

    def update_fields_for_boarding_point_language(
        self,
        session: Session,
        *,
        boarding_point_id: int,
        language_code: str,
        fields: Mapping[str, Any],
    ) -> BoardingPointTranslation | None:
        row = self.get_by_boarding_point_and_language(
            session,
            boarding_point_id=boarding_point_id,
            language_code=language_code,
        )
        if row is None:
            return None
        for key, value in fields.items():
            setattr(row, key, value)
        session.add(row)
        session.flush()
        session.refresh(row)
        return row


class BoardingPointRepository(SQLAlchemyRepository[BoardingPoint]):
    def __init__(self) -> None:
        super().__init__(BoardingPoint)

    def create_for_tour(
        self,
        session: Session,
        *,
        tour_id: int,
        city: str,
        address: str,
        boarding_time: time_type,
        notes: str | None,
    ) -> BoardingPoint:
        return self.create(
            session,
            data={
                "tour_id": tour_id,
                "city": city,
                "address": address,
                "time": boarding_time,
                "notes": notes,
            },
        )

    def list_by_tour(self, session: Session, *, tour_id: int) -> list[BoardingPoint]:
        stmt = (
            select(BoardingPoint)
            .where(BoardingPoint.tour_id == tour_id)
            .order_by(BoardingPoint.time, BoardingPoint.id)
        )
        return list(session.scalars(stmt).all())

    def update_core_fields(
        self,
        session: Session,
        *,
        boarding_point_id: int,
        fields: Mapping[str, Any],
    ) -> BoardingPoint | None:
        bp = session.get(BoardingPoint, boarding_point_id)
        if bp is None:
            return None
        for key, value in fields.items():
            setattr(bp, key, value)
        session.add(bp)
        session.flush()
        session.refresh(bp)
        return bp
