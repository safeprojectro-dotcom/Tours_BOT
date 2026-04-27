from __future__ import annotations

from datetime import UTC, datetime, time as time_type
from typing import Any, Mapping

from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import TourStatus
from app.models.supplier_offer_recurrence_generated_tour import SupplierOfferRecurrenceGeneratedTour
from app.models.supplier_offer_tour_bridge import SupplierOfferTourBridge
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

    def list_by_status_customer_catalog_visible(
        self,
        session: Session,
        *,
        status: TourStatus,
        now_utc: datetime,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Tour]:
        """Open (or other) status tours that are still sellable by time window — customer catalog only."""
        ref = now_utc if now_utc.tzinfo else now_utc.replace(tzinfo=UTC)
        ref = ref.astimezone(UTC)
        stmt = (
            select(Tour)
            .where(Tour.status == status)
            .where(Tour.departure_datetime >= ref)
            .where(or_(Tour.sales_deadline.is_(None), Tour.sales_deadline >= ref))
            .order_by(Tour.departure_datetime, Tour.id)
            .offset(offset)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def get_open_for_sale_conflict_for_recurrence_activation(
        self,
        session: Session,
        *,
        source_supplier_offer_id: int,
        departure_datetime: datetime,
        exclude_tour_id: int,
    ) -> int | None:
        """
        B8.3: Another ``open_for_sale`` tour for the same template offer and same
        ``departure_datetime`` blocks activating a second recurring-generated instance.

        Includes sibling rows in ``supplier_offer_recurrence_generated_tours`` and
        the B10 active ``supplier_offer_tour_bridges`` row for the offer (primary tour).
        """
        sibling_b8 = exists(
            select(1)
            .select_from(SupplierOfferRecurrenceGeneratedTour)
            .where(
                SupplierOfferRecurrenceGeneratedTour.source_supplier_offer_id
                == source_supplier_offer_id,
                SupplierOfferRecurrenceGeneratedTour.tour_id == Tour.id,
            ),
        )
        active_bridge = exists(
            select(1)
            .select_from(SupplierOfferTourBridge)
            .where(
                SupplierOfferTourBridge.supplier_offer_id == source_supplier_offer_id,
                SupplierOfferTourBridge.tour_id == Tour.id,
                SupplierOfferTourBridge.status == "active",
            ),
        )
        stmt = (
            select(Tour.id)
            .where(Tour.id != exclude_tour_id)
            .where(Tour.status == TourStatus.OPEN_FOR_SALE)
            .where(Tour.departure_datetime == departure_datetime)
            .where(or_(sibling_b8, active_bridge))
            .limit(1)
        )
        return session.scalar(stmt)

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

    def delete_for_boarding_point_language(
        self,
        session: Session,
        *,
        boarding_point_id: int,
        language_code: str,
    ) -> bool:
        row = self.get_by_boarding_point_and_language(
            session,
            boarding_point_id=boarding_point_id,
            language_code=language_code,
        )
        if row is None:
            return False
        self.delete(session, instance=row)
        return True


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
