"""B10: explicit admin API to bridge packaging-approved supplier offer → Layer A `Tour` (draft, idempotent)."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import (
    SupplierOfferLifecycle,
    SupplierOfferPackagingStatus,
    SupplierOfferTourBridgeKind,
    SupplierOfferTourBridgeStatus,
    TourStatus,
)
from app.models.supplier import SupplierOffer
from app.models.supplier_offer_tour_bridge import SupplierOfferTourBridge
from app.models.tour import Tour
from app.repositories.supplier_offer_tour_bridge import SupplierOfferTourBridgeRepository
from app.repositories.tour import TourRepository, TourTranslationRepository


class SupplierOfferTourBridgeNotFoundError(Exception):
    """No `SupplierOffer` for id."""


class SupplierOfferTourBridgeStateError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class SupplierOfferTourBridgeValidationError(Exception):
    def __init__(self, missing_fields: list[str]) -> None:
        self.missing_fields = list(missing_fields)
        super().__init__(f"Missing or invalid: {', '.join(missing_fields)}")


class SupplierOfferTourBridgeTourNotFoundError(Exception):
    """`existing_tour_id` not found."""


class SupplierOfferTourBridgeExistingTourError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class SupplierOfferTourBridgeResult:
    id: int
    supplier_offer_id: int
    tour_id: int
    bridge_status: str
    bridge_kind: str
    tour_status: str
    created_at: datetime
    idempotent_replay: bool
    warnings: list[str]
    notes: str | None
    source_packaging_status: str
    source_lifecycle_status: str


def _nonempty(s: str | None) -> bool:
    return bool(s and s.strip())


def _collect_missing(offer: SupplierOffer) -> list[str]:
    missing: list[str] = []
    if not _nonempty(offer.title):
        missing.append("title")
    if not _nonempty(offer.description) and not _nonempty(offer.marketing_summary):
        missing.append("description_or_marketing_summary")
    if not _nonempty(offer.program_text):
        missing.append("program_text")
    if not _nonempty(offer.included_text):
        missing.append("included_text")
    if not _nonempty(offer.excluded_text):
        missing.append("excluded_text")
    if offer.base_price is None:
        missing.append("base_price")
    if not _nonempty(offer.currency):
        missing.append("currency")
    if offer.seats_total is None or offer.seats_total <= 0:
        missing.append("seats_total")
    if offer.departure_datetime is None:
        missing.append("departure_datetime")
    if offer.return_datetime is None:
        missing.append("return_datetime")
    if offer.return_datetime is not None and offer.departure_datetime is not None:
        if offer.return_datetime <= offer.departure_datetime:
            missing.append("return_datetime_after_departure")
    if offer.sales_mode is None:  # pragma: no cover - column non-null
        missing.append("sales_mode")
    return missing


def _duration_days(departure: datetime, return_dt: datetime) -> int:
    days = (return_dt.date() - departure.date()).days
    if days < 0:
        return 1
    return max(1, days)


def _desc_pair(offer: SupplierOffer) -> tuple[str, str | None, str | None]:
    full = (offer.description or "").strip() or (offer.marketing_summary or "").strip()
    short_src = (offer.marketing_summary or "").strip() or (offer.description or "").split("\n\n", 1)[0].strip()
    short: str | None = short_src[:2000] if short_src else None
    full_desc: str | None = full if full else None
    title_default = (offer.title or "").strip()
    return title_default, short, full_desc


def _warnings_from_offer(offer: SupplierOffer) -> list[str]:
    w = offer.quality_warnings_json
    if w is None:
        return []
    if isinstance(w, list):
        return [str(x) for x in w]
    if isinstance(w, dict):
        items = w.get("items")
        if isinstance(items, list):
            return [str(x) for x in items]
    return [str(w)]


def _packaging_snapshot(offer: SupplierOffer) -> dict:
    keys: list[str] = []
    if isinstance(offer.packaging_draft_json, dict):
        keys = list(offer.packaging_draft_json.keys())[:200]
    return {
        "packaging_status": str(offer.packaging_status),
        "lifecycle_status": str(offer.lifecycle_status),
        "packaging_draft_json_keys": keys,
        "quality_warning_count": len(_warnings_from_offer(offer)),
    }


def _unique_tour_code(
    session: Session,
    tour_repo: TourRepository,
    offer_id: int,
    *,
    prefix: str = "B10",
) -> str:
    for _ in range(20):
        suffix = secrets.token_hex(3)
        code = f"{prefix}-SO{offer_id}-{suffix}"
        if len(code) > 64:
            code = code[:64]
        if tour_repo.get_by_code(session, code=code) is None:
            return code
    raise RuntimeError("Could not allocate unique tour code")  # pragma: no cover


def _tour_seats_available(offer: SupplierOffer) -> int:
    # Align with `AdminTourWriteService.create_tour`: pool starts full; `sales_mode` enforces self-serve policy.
    return int(offer.seats_total)


class SupplierOfferTourBridgeService:
    def __init__(
        self,
        *,
        bridge_repo: SupplierOfferTourBridgeRepository | None = None,
        tour_repo: TourRepository | None = None,
        trans_repo: TourTranslationRepository | None = None,
    ) -> None:
        self._bridges = bridge_repo or SupplierOfferTourBridgeRepository()
        self._tours = tour_repo or TourRepository()
        self._translations = trans_repo or TourTranslationRepository()

    def _assert_eligible_for_materialization(self, offer: SupplierOffer) -> None:
        if offer.packaging_status is not SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH:
            raise SupplierOfferTourBridgeStateError(
                "packaging_not_approved",
                "Supplier offer packaging_status must be approved_for_publish.",
            )
        if offer.lifecycle_status is SupplierOfferLifecycle.REJECTED:
            raise SupplierOfferTourBridgeStateError("lifecycle_rejected", "Supplier offer lifecycle_status must not be rejected.")
        missing = _collect_missing(offer)
        if missing:
            raise SupplierOfferTourBridgeValidationError(missing)

    def ensure_offer_eligible_for_tour_materialization(self, offer: SupplierOffer) -> None:
        """Public alias for B8 batch generation: same rules as bridge create (packaging, lifecycle, required fields)."""
        self._assert_eligible_for_materialization(offer)

    def _insert_draft_tour_from_offer_dates(
        self,
        session: Session,
        *,
        offer: SupplierOffer,
        departure_datetime: datetime,
        return_datetime: datetime,
        tour_code_prefix: str = "B10",
    ) -> Tour:
        title_default, short_d, full_d = _desc_pair(offer)
        duration_days = _duration_days(departure_datetime, return_datetime)
        seats_total = int(offer.seats_total)
        seats_av = _tour_seats_available(offer)
        assert offer.base_price is not None
        code = _unique_tour_code(
            session,
            self._tours,
            offer.id,
            prefix=tour_code_prefix,
        )
        data = {
            "code": code,
            "title_default": title_default[:255],
            "short_description_default": short_d,
            "full_description_default": full_d,
            "duration_days": duration_days,
            "departure_datetime": departure_datetime,
            "return_datetime": return_datetime,
            "base_price": offer.base_price,
            "currency": (offer.currency or "").strip(),
            "seats_total": seats_total,
            "seats_available": seats_av,
            "sales_deadline": None,
            "sales_mode": offer.sales_mode,
            "status": TourStatus.DRAFT,
            "guaranteed_flag": False,
            "cover_media_reference": (offer.cover_media_reference or "").strip() or None,
        }
        tour = self._tours.create(session, data=data)
        self._ensure_default_translation(session, tour_id=tour.id, offer=offer, title=title_default[:255])
        return tour

    def create_draft_tour_from_offer_dates(
        self,
        session: Session,
        *,
        offer: SupplierOffer,
        departure_datetime: datetime,
        return_datetime: datetime,
        tour_code_prefix: str = "B8R",
        skip_eligibility_check: bool = False,
    ) -> Tour:
        """
        B8: create a Layer A `Tour` (draft) + default translation from offer snapshot and explicit dates.

        Does **not** create `SupplierOfferTourBridge` or execution links — no catalog or Layer A booking without
        separate activation (B10.2) and linking per product rules.

        When ``skip_eligibility_check`` is True, caller must have already validated the offer (e.g. batch recurrence).
        """
        if return_datetime <= departure_datetime:
            raise SupplierOfferTourBridgeValidationError(["return_datetime_after_departure"])
        if not skip_eligibility_check:
            self._assert_eligible_for_materialization(offer)
        return self._insert_draft_tour_from_offer_dates(
            session,
            offer=offer,
            departure_datetime=departure_datetime,
            return_datetime=return_datetime,
            tour_code_prefix=tour_code_prefix,
        )

    def get_active_bridge(
        self,
        session: Session,
        *,
        supplier_offer_id: int,
    ) -> SupplierOfferTourBridgeResult | None:
        offer = session.get(SupplierOffer, supplier_offer_id)
        if offer is None:
            raise SupplierOfferTourBridgeNotFoundError()
        bridge = self._bridges.get_active_for_offer(session, supplier_offer_id=supplier_offer_id)
        if bridge is None:
            return None
        tour = session.get(Tour, bridge.tour_id)
        if tour is None:  # pragma: no cover
            return None
        return self._to_result(
            bridge=bridge,
            tour=tour,
            offer=offer,
            idempotent_replay=False,
        )

    def create_or_replay_bridge(
        self,
        session: Session,
        *,
        supplier_offer_id: int,
        created_by: str | None = None,
        notes: str | None = None,
        existing_tour_id: int | None = None,
    ) -> SupplierOfferTourBridgeResult:
        offer = session.get(SupplierOffer, supplier_offer_id)
        if offer is None:
            raise SupplierOfferTourBridgeNotFoundError()

        existing = self._bridges.get_active_for_offer(session, supplier_offer_id=supplier_offer_id)
        if existing is not None:
            tour = session.get(Tour, existing.tour_id)
            assert tour is not None
            return self._to_result(
                bridge=existing,
                tour=tour,
                offer=offer,
                idempotent_replay=True,
            )

        # Serialize concurrent admin POSTs per offer: prevents duplicate `Tour` / active bridge.
        self._lock_offer_for_update(session, supplier_offer_id=supplier_offer_id)
        offer = session.get(SupplierOffer, supplier_offer_id)
        assert offer is not None
        existing = self._bridges.get_active_for_offer(session, supplier_offer_id=supplier_offer_id)
        if existing is not None:
            tour = session.get(Tour, existing.tour_id)
            assert tour is not None
            return self._to_result(
                bridge=existing,
                tour=tour,
                offer=offer,
                idempotent_replay=True,
            )

        self._assert_eligible_for_materialization(offer)

        snapshot = _packaging_snapshot(offer)
        source_ps = str(offer.packaging_status)
        source_ls = str(offer.lifecycle_status)

        if existing_tour_id is not None:
            return self._link_existing(
                session,
                offer=offer,
                tour_id=existing_tour_id,
                created_by=created_by,
                notes=notes,
                source_packaging_status=source_ps,
                source_lifecycle_status=source_ls,
                packaging_snapshot_json=snapshot,
            )

        tour = self._insert_draft_tour_from_offer_dates(
            session,
            offer=offer,
            departure_datetime=offer.departure_datetime,
            return_datetime=offer.return_datetime,
            tour_code_prefix="B10",
        )
        kind = SupplierOfferTourBridgeKind.CREATED_NEW_TOUR.value
        return self._insert_bridge(
            session,
            offer=offer,
            tour_id=tour.id,
            kind=kind,
            created_by=created_by,
            notes=notes,
            source_packaging_status=source_ps,
            source_lifecycle_status=source_ls,
            packaging_snapshot_json=snapshot,
        )

    def _link_existing(
        self,
        session: Session,
        *,
        offer: SupplierOffer,
        tour_id: int,
        created_by: str | None,
        notes: str | None,
        source_packaging_status: str,
        source_lifecycle_status: str,
        packaging_snapshot_json: dict,
    ) -> SupplierOfferTourBridgeResult:
        tour = session.get(Tour, tour_id)
        if tour is None:
            raise SupplierOfferTourBridgeTourNotFoundError()
        if tour.sales_mode is not offer.sales_mode:
            raise SupplierOfferTourBridgeExistingTourError(
                "Existing tour sales_mode does not match supplier offer sales_mode; pick another tour or bridge without existing_tour_id.",
            )
        if tour.status is TourStatus.CANCELLED:
            raise SupplierOfferTourBridgeExistingTourError("Cannot link to a cancelled tour.")
        return self._insert_bridge(
            session,
            offer=offer,
            tour_id=tour.id,
            kind=SupplierOfferTourBridgeKind.LINKED_EXISTING_TOUR.value,
            created_by=created_by,
            notes=notes,
            source_packaging_status=source_packaging_status,
            source_lifecycle_status=source_lifecycle_status,
            packaging_snapshot_json=packaging_snapshot_json,
        )

    def _insert_bridge(
        self,
        session: Session,
        *,
        offer: SupplierOffer,
        tour_id: int,
        kind: str,
        created_by: str | None,
        notes: str | None,
        source_packaging_status: str,
        source_lifecycle_status: str,
        packaging_snapshot_json: dict,
    ) -> SupplierOfferTourBridgeResult:
        data = {
            "supplier_offer_id": offer.id,
            "tour_id": tour_id,
            "status": SupplierOfferTourBridgeStatus.ACTIVE.value,
            "bridge_kind": kind,
            "created_by": (created_by or "").strip() or None,
            "source_packaging_status": source_packaging_status,
            "source_lifecycle_status": source_lifecycle_status,
            "packaging_snapshot_json": packaging_snapshot_json,
            "notes": (notes or "").strip() or None,
        }
        bridge = self._bridges.create(session, data=data)
        tour = session.get(Tour, tour_id)
        assert tour is not None
        return self._to_result(bridge=bridge, tour=tour, offer=offer, idempotent_replay=False)

    @staticmethod
    def _lock_offer_for_update(session: Session, *, supplier_offer_id: int) -> None:
        stmt = select(SupplierOffer.id).where(SupplierOffer.id == supplier_offer_id).with_for_update()
        row = session.execute(stmt).one_or_none()
        if row is None:
            raise SupplierOfferTourBridgeNotFoundError()

    def _ensure_default_translation(
        self,
        session: Session,
        *,
        tour_id: int,
        offer: SupplierOffer,
        title: str,
    ) -> None:
        settings = get_settings()
        codes = list(settings.telegram_supported_language_codes) or ("en",)
        lang = codes[0]
        ttitle = (offer.title or title)[:255]
        ptext = (offer.program_text or "").strip() or None
        inc = (offer.included_text or "").strip() or None
        exc = (offer.excluded_text or "").strip() or None
        short = ((offer.marketing_summary or offer.description) or "")[:2000] or None
        full = (offer.description or offer.marketing_summary or "") or None
        self._translations.create(
            session,
            data={
                "tour_id": tour_id,
                "language_code": lang,
                "title": ttitle,
                "short_description": short,
                "full_description": full,
                "program_text": ptext,
                "included_text": inc,
                "excluded_text": exc,
            },
        )

    def _to_result(
        self,
        *,
        bridge: SupplierOfferTourBridge,
        tour: Tour,
        offer: SupplierOffer,
        idempotent_replay: bool,
    ) -> SupplierOfferTourBridgeResult:
        return SupplierOfferTourBridgeResult(
            id=bridge.id,
            supplier_offer_id=offer.id,
            tour_id=tour.id,
            bridge_status=bridge.status,
            bridge_kind=bridge.bridge_kind,
            tour_status=tour.status.value,
            created_at=bridge.created_at,
            idempotent_replay=idempotent_replay,
            warnings=_warnings_from_offer(offer),
            notes=bridge.notes,
            source_packaging_status=bridge.source_packaging_status,
            source_lifecycle_status=bridge.source_lifecycle_status,
        )


__all__ = [
    "SupplierOfferTourBridgeService",
    "SupplierOfferTourBridgeResult",
    "SupplierOfferTourBridgeNotFoundError",
    "SupplierOfferTourBridgeStateError",
    "SupplierOfferTourBridgeValidationError",
    "SupplierOfferTourBridgeTourNotFoundError",
    "SupplierOfferTourBridgeExistingTourError",
]
