"""Admin tour mutations — narrow slices; validation stays here (not in routes)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import TourSalesMode, TourStatus
from app.models.tour import BoardingPoint, Tour
from app.repositories.order import OrderRepository
from app.repositories.supplier_offer_recurrence_generated_tour import (
    SupplierOfferRecurrenceGeneratedTourRepository,
)
from app.repositories.tour import (
    BoardingPointRepository,
    BoardingPointTranslationRepository,
    TourRepository,
    TourTranslationRepository,
)
from app.schemas.admin import (
    AdminBoardingPointCreate,
    AdminBoardingPointTranslationUpsert,
    AdminBoardingPointUpdate,
    AdminTourCoreUpdate,
    AdminTourCoverSet,
    AdminTourCreate,
    AdminTourDetailRead,
    AdminTourTranslationUpsert,
)
from app.services.admin_read import AdminReadService
from app.services.tour_sales_mode_policy import TourSalesModePolicyService
from app.schemas.tour_sales_mode_policy import TourSalesModePolicyRead


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


class AdminBoardingPointInUseError(Exception):
    """At least one order references this boarding point (FK RESTRICT)."""


class AdminTourTranslationNotFoundError(Exception):
    """No tour translation row for this tour and language."""


class AdminBoardingPointTranslationNotFoundError(Exception):
    """No boarding point translation row for this boarding point and language."""


class AdminTourCatalogActivationValidationError(Exception):
    def __init__(self, missing_fields: list[str]) -> None:
        self.missing_fields = list(missing_fields)
        super().__init__(f"Not ready for catalog: {', '.join(missing_fields)}")


class AdminTourCatalogActivationStateError(Exception):
    """Draft-only activation, or disallowed :class:`TourStatus` (e.g. cancelled / archived)."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class AdminTourCatalogActivationResult:
    """B10.2: `draft` → :attr:`~TourStatus.OPEN_FOR_SALE` for Mini App ``STATUS_SCOPE`` (idempotent if already open)."""

    tour_id: int
    code: str
    status: TourStatus
    idempotent_replay: bool
    sales_mode: TourSalesMode
    policy: TourSalesModePolicyRead


def _collect_catalog_activation_missing(tour: Tour) -> list[str]:
    """Core fields required before listing the tour in the Mini App catalog (B10.2)."""
    missing: list[str] = []
    if not (tour.title_default or "").strip():
        missing.append("title_default")
    if tour.departure_datetime is None:
        missing.append("departure_datetime")
    if tour.return_datetime is None:
        missing.append("return_datetime")
    if (
        tour.departure_datetime is not None
        and tour.return_datetime is not None
        and tour.return_datetime <= tour.departure_datetime
    ):
        missing.append("return_datetime_after_departure")
    if tour.base_price is None:
        missing.append("base_price")
    if not (tour.currency or "").strip():
        missing.append("currency")
    if tour.seats_total is None or tour.seats_total <= 0:
        missing.append("seats_total")
    if tour.sales_mode is None:  # pragma: no cover — column is non-null
        missing.append("sales_mode")
    return missing


# Phase 6 / Step 15 — narrow archive/unarchive (no new enum member).
# Reuse SALES_CLOSED as the admin "archived" bucket: Mini App catalog lists only OPEN_FOR_SALE,
# so moving here hides the tour from public catalog without hard delete.
# Unarchive restores a single return path: OPEN_FOR_SALE (sale-ready).
_TOUR_ARCHIVE_SOURCE_STATUSES: frozenset[TourStatus] = frozenset(
    {
        TourStatus.DRAFT,
        TourStatus.OPEN_FOR_SALE,
        TourStatus.COLLECTING_GROUP,
        TourStatus.GUARANTEED,
    },
)
_TOUR_ARCHIVED_STATUS = TourStatus.SALES_CLOSED


class AdminTourWriteService:
    def __init__(
        self,
        *,
        tour_repository: TourRepository | None = None,
        boarding_point_repository: BoardingPointRepository | None = None,
        boarding_point_translation_repository: BoardingPointTranslationRepository | None = None,
        tour_translation_repository: TourTranslationRepository | None = None,
        order_repository: OrderRepository | None = None,
        read_service: AdminReadService | None = None,
        recurrence_generated_tour_repository: SupplierOfferRecurrenceGeneratedTourRepository | None = None,
    ) -> None:
        self._tours = tour_repository or TourRepository()
        self._boarding_points = boarding_point_repository or BoardingPointRepository()
        self._bp_translations = boarding_point_translation_repository or BoardingPointTranslationRepository()
        self._translations = tour_translation_repository or TourTranslationRepository()
        self._orders = order_repository or OrderRepository()
        self._read = read_service or AdminReadService()
        self._b8_recurrence_audit = recurrence_generated_tour_repository or SupplierOfferRecurrenceGeneratedTourRepository()

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
            "sales_mode": payload.sales_mode,
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

    def delete_boarding_point(self, session: Session, *, boarding_point_id: int) -> None:
        """Delete one boarding point row by id; raises if referenced by any order."""
        bp = session.get(BoardingPoint, boarding_point_id)
        if bp is None:
            raise AdminBoardingPointNotFoundError()

        if self._orders.count_by_boarding_point(session, boarding_point_id=boarding_point_id) > 0:
            raise AdminBoardingPointInUseError()

        self._boarding_points.delete(session, instance=bp)

    def upsert_tour_translation(
        self,
        session: Session,
        *,
        tour_id: int,
        language_code: str,
        payload: AdminTourTranslationUpsert,
    ) -> AdminTourDetailRead:
        """Create or merge-update a single `TourTranslation` for one supported language; returns refreshed admin tour detail."""
        lc = language_code.strip().lower()
        allowed = get_settings().telegram_supported_language_codes
        if lc not in allowed:
            raise AdminTourCreateValidationError("Unsupported language code.")

        tour = session.get(Tour, tour_id)
        if tour is None:
            raise AdminTourNotFoundError()

        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise AdminTourCreateValidationError("No fields to update.")

        existing = self._translations.get_by_tour_and_language(session, tour_id=tour_id, language_code=lc)

        if existing is None:
            if "title" not in updates:
                raise AdminTourCreateValidationError("title is required when creating a tour translation.")
            data = {
                "tour_id": tour_id,
                "language_code": lc,
                "title": updates["title"],
                "short_description": updates.get("short_description"),
                "full_description": updates.get("full_description"),
                "program_text": updates.get("program_text"),
                "included_text": updates.get("included_text"),
                "excluded_text": updates.get("excluded_text"),
            }
            self._translations.create(session, data=data)
        else:
            if "title" in updates and updates["title"] is None:
                raise AdminTourCreateValidationError("title cannot be cleared.")
            self._translations.update_fields_for_tour_language(
                session,
                tour_id=tour_id,
                language_code=lc,
                fields=updates,
            )

        detail = self._read.get_tour_detail(session, tour_id=tour_id)
        assert detail is not None
        return detail

    def delete_tour_translation(
        self,
        session: Session,
        *,
        tour_id: int,
        language_code: str,
    ) -> None:
        """Delete one `TourTranslation` row for a supported language; raises if tour or row missing."""
        lc = language_code.strip().lower()
        allowed = get_settings().telegram_supported_language_codes
        if lc not in allowed:
            raise AdminTourCreateValidationError("Unsupported language code.")

        if session.get(Tour, tour_id) is None:
            raise AdminTourNotFoundError()

        deleted = self._translations.delete_for_tour_language(session, tour_id=tour_id, language_code=lc)
        if not deleted:
            raise AdminTourTranslationNotFoundError()

    def upsert_boarding_point_translation(
        self,
        session: Session,
        *,
        boarding_point_id: int,
        language_code: str,
        payload: AdminBoardingPointTranslationUpsert,
    ) -> AdminTourDetailRead:
        """Create or merge-update localized city/address/notes for one boarding point; does not change core `time` or tour link."""
        lc = language_code.strip().lower()
        allowed = get_settings().telegram_supported_language_codes
        if lc not in allowed:
            raise AdminTourCreateValidationError("Unsupported language code.")

        bp = session.get(BoardingPoint, boarding_point_id)
        if bp is None:
            raise AdminBoardingPointNotFoundError()

        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise AdminTourCreateValidationError("No fields to update.")

        existing = self._bp_translations.get_by_boarding_point_and_language(
            session,
            boarding_point_id=boarding_point_id,
            language_code=lc,
        )

        if existing is None:
            if "city" not in updates or "address" not in updates:
                raise AdminTourCreateValidationError(
                    "city and address are required when creating a boarding point translation.",
                )
            data = {
                "boarding_point_id": boarding_point_id,
                "language_code": lc,
                "city": updates["city"],
                "address": updates["address"],
                "notes": updates.get("notes"),
            }
            self._bp_translations.create(session, data=data)
        else:
            for key in ("city", "address"):
                if key in updates and updates[key] is None:
                    raise AdminTourCreateValidationError(f"{key} cannot be cleared.")
            self._bp_translations.update_fields_for_boarding_point_language(
                session,
                boarding_point_id=boarding_point_id,
                language_code=lc,
                fields=updates,
            )

        detail = self._read.get_tour_detail(session, tour_id=bp.tour_id)
        assert detail is not None
        return detail

    def delete_boarding_point_translation(
        self,
        session: Session,
        *,
        boarding_point_id: int,
        language_code: str,
    ) -> None:
        """Delete one `BoardingPointTranslation` row for a supported language; raises if point or row missing."""
        lc = language_code.strip().lower()
        allowed = get_settings().telegram_supported_language_codes
        if lc not in allowed:
            raise AdminTourCreateValidationError("Unsupported language code.")

        if session.get(BoardingPoint, boarding_point_id) is None:
            raise AdminBoardingPointNotFoundError()

        deleted = self._bp_translations.delete_for_boarding_point_language(
            session,
            boarding_point_id=boarding_point_id,
            language_code=lc,
        )
        if not deleted:
            raise AdminBoardingPointTranslationNotFoundError()

    def archive_tour(self, session: Session, *, tour_id: int) -> AdminTourDetailRead:
        """Set `status` to SALES_CLOSED when allowed; idempotent if already archived."""
        tour = session.get(Tour, tour_id)
        if tour is None:
            raise AdminTourNotFoundError()

        if tour.status == _TOUR_ARCHIVED_STATUS:
            detail = self._read.get_tour_detail(session, tour_id=tour_id)
            assert detail is not None
            return detail

        if tour.status not in _TOUR_ARCHIVE_SOURCE_STATUSES:
            raise AdminTourCreateValidationError(
                "Cannot archive tour from the current status.",
            )

        self._tours.update_core_fields(
            session,
            tour_id=tour_id,
            fields={"status": _TOUR_ARCHIVED_STATUS},
        )
        detail = self._read.get_tour_detail(session, tour_id=tour_id)
        assert detail is not None
        return detail

    def unarchive_tour(self, session: Session, *, tour_id: int) -> AdminTourDetailRead:
        """Restore from SALES_CLOSED to OPEN_FOR_SALE; idempotent if already open for sale."""
        tour = session.get(Tour, tour_id)
        if tour is None:
            raise AdminTourNotFoundError()

        if tour.status == TourStatus.OPEN_FOR_SALE:
            detail = self._read.get_tour_detail(session, tour_id=tour_id)
            assert detail is not None
            return detail

        if tour.status != _TOUR_ARCHIVED_STATUS:
            raise AdminTourCreateValidationError(
                "Tour is not archived (expected sales_closed status).",
            )

        self._tours.update_core_fields(
            session,
            tour_id=tour_id,
            fields={"status": TourStatus.OPEN_FOR_SALE},
        )
        detail = self._read.get_tour_detail(session, tour_id=tour_id)
        assert detail is not None
        return detail

    def activate_tour_for_catalog(
        self,
        session: Session,
        *,
        tour_id: int,
        activated_by: str | None = None,
        notes: str | None = None,
    ) -> AdminTourCatalogActivationResult:
        """
        B10.2: `draft` → `open_for_sale` so :class:`MiniAppCatalogService` can list the tour.
        Idempotent if already `open_for_sale`. Does not change `seats_available` (full_bus safety).
        B8.3: for tours in ``supplier_offer_recurrence_generated_tours``, blocks if another
        ``open_for_sale`` tour exists for the same template offer and ``departure_datetime``
        (sibling B8 instance or B10 active bridge tour).
        ``activated_by`` / ``notes`` are accepted for API clients; no new audit row in this slice.
        """
        _ = activated_by, notes
        stmt = select(Tour).where(Tour.id == tour_id).with_for_update()
        tour = session.execute(stmt).scalar_one_or_none()
        if tour is None:
            raise AdminTourNotFoundError()

        if tour.status == TourStatus.OPEN_FOR_SALE:
            policy = TourSalesModePolicyService.policy_for_sales_mode(tour.sales_mode)
            return AdminTourCatalogActivationResult(
                tour_id=tour.id,
                code=tour.code,
                status=tour.status,
                idempotent_replay=True,
                sales_mode=tour.sales_mode,
                policy=policy,
            )
        if tour.status in (TourStatus.CANCELLED, _TOUR_ARCHIVED_STATUS):
            raise AdminTourCatalogActivationStateError(
                "Cannot activate a cancelled or archived tour for catalog.",
            )
        if tour.status != TourStatus.DRAFT:
            raise AdminTourCatalogActivationStateError(
                f"Only draft tours can be activated for catalog (current status: {tour.status.value}).",
            )

        missing = _collect_catalog_activation_missing(tour)
        if missing:
            raise AdminTourCatalogActivationValidationError(missing)

        source_offer_id = self._b8_recurrence_audit.get_source_supplier_offer_id_for_tour(
            session,
            tour_id=tour_id,
        )
        if source_offer_id is not None:
            conflict = self._tours.get_open_for_sale_conflict_for_recurrence_activation(
                session,
                source_supplier_offer_id=source_offer_id,
                departure_datetime=tour.departure_datetime,
                exclude_tour_id=tour_id,
            )
            if conflict is not None:
                raise AdminTourCatalogActivationStateError(
                    "Cannot activate this recurring-generated tour: another catalog-active tour already exists "
                    "for the same supplier offer and departure.",
                )

        self._tours.update_core_fields(
            session,
            tour_id=tour_id,
            fields={"status": TourStatus.OPEN_FOR_SALE},
        )
        session.refresh(tour)
        policy = TourSalesModePolicyService.policy_for_sales_mode(tour.sales_mode)
        return AdminTourCatalogActivationResult(
            tour_id=tour.id,
            code=tour.code,
            status=tour.status,
            idempotent_replay=False,
            sales_mode=tour.sales_mode,
            policy=policy,
        )
