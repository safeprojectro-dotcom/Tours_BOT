"""S1B: read-only mapping from supplier / offer / tour / order → supplier Telegram contact (no notifications)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.supplier import Supplier, SupplierOffer, SupplierOfferExecutionLink
from app.models.supplier_offer_tour_bridge import SupplierOfferTourBridge
from app.repositories.supplier import SupplierOfferRepository, SupplierRepository
from app.repositories.tour import TourRepository
from app.schemas.admin_supplier_telegram_contact_resolution import (
    AdminSupplierTelegramContactResolutionRead,
    AdminTelegramContactContext,
)


class AdminSupplierTelegramContactResolutionService:
    """Resolve supplier.primary_telegram_user_id for future outbound supplier DMs — read-only."""

    def __init__(
        self,
        *,
        supplier_repository: SupplierRepository | None = None,
        offer_repository: SupplierOfferRepository | None = None,
        tour_repository: TourRepository | None = None,
    ) -> None:
        self._suppliers = supplier_repository or SupplierRepository()
        self._offers = offer_repository or SupplierOfferRepository()
        self._tours = tour_repository or TourRepository()

    def resolve_for_supplier(self, session: Session, *, supplier_id: int) -> AdminSupplierTelegramContactResolutionRead | None:
        supplier = self._suppliers.get(session, supplier_id)
        if supplier is None:
            return None
        return self._from_supplier_row(
            supplier,
            context_type="supplier",
            context_id=supplier_id,
            path_codes=["supplier_row"],
        )

    def resolve_for_supplier_offer(self, session: Session, *, offer_id: int) -> AdminSupplierTelegramContactResolutionRead | None:
        offer = self._offers.get_any(session, offer_id=offer_id)
        if offer is None:
            return None
        supplier = self._suppliers.get(session, offer.supplier_id)
        if supplier is None:
            return AdminSupplierTelegramContactResolutionRead(
                context_type="supplier_offer",
                context_id=offer_id,
                resolution_status="missing_relationship",
                telegram_contact_configured=False,
                resolution_path_codes=["supplier_offer_orphan"],
                readiness_warnings=["s1b_supplier_row_missing_for_offer"],
            )
        return self._from_supplier_row(
            supplier,
            context_type="supplier_offer",
            context_id=offer_id,
            path_codes=["supplier_offer_owner"],
        )

    def resolve_for_tour(self, session: Session, *, tour_id: int) -> AdminSupplierTelegramContactResolutionRead | None:
        tour = self._tours.get(session, tour_id)
        if tour is None:
            return None
        supplier_ids = self._distinct_supplier_ids_for_tour(session, tour_id=tour_id)
        if not supplier_ids:
            return AdminSupplierTelegramContactResolutionRead(
                context_type="tour",
                context_id=tour_id,
                resolution_status="missing_relationship",
                telegram_contact_configured=False,
                resolution_path_codes=["tour_no_active_execution_link_or_bridge"],
                readiness_warnings=["s1b_tour_has_no_active_supplier_offer_link"],
            )
        if len(supplier_ids) > 1:
            return AdminSupplierTelegramContactResolutionRead(
                context_type="tour",
                context_id=tour_id,
                resolution_status="ambiguous_suppliers",
                telegram_contact_configured=False,
                linked_supplier_ids=sorted(supplier_ids),
                resolution_path_codes=["tour_active_execution_links", "tour_active_bridges"],
                readiness_warnings=["s1b_tour_maps_to_multiple_suppliers"],
            )
        sid = next(iter(supplier_ids))
        supplier = self._suppliers.get(session, sid)
        if supplier is None:
            return AdminSupplierTelegramContactResolutionRead(
                context_type="tour",
                context_id=tour_id,
                resolution_status="missing_relationship",
                telegram_contact_configured=False,
                linked_supplier_ids=[sid],
                resolution_path_codes=["tour_linked_supplier_row_missing"],
                readiness_warnings=["s1b_supplier_row_missing"],
            )
        base = self._from_supplier_row(
            supplier,
            context_type="tour",
            context_id=tour_id,
            path_codes=["tour_active_execution_links", "tour_active_bridges"],
        )
        # Single supplier: linked_supplier_ids empty in happy path (prompt: avoid noise); keep warnings from _from_supplier_row
        return base

    def resolve_for_order(self, session: Session, *, order_id: int) -> AdminSupplierTelegramContactResolutionRead | None:
        order = session.get(Order, order_id)
        if order is None:
            return None
        tour_read = self.resolve_for_tour(session, tour_id=order.tour_id)
        if tour_read is None:
            return None
        path = list(tour_read.resolution_path_codes)
        path.insert(0, "order_tour")
        return tour_read.model_copy(
            update={
                "context_type": "order",
                "context_id": order_id,
                "resolution_path_codes": path,
            },
        )

    def _distinct_supplier_ids_for_tour(self, session: Session, *, tour_id: int) -> set[int]:
        el_stmt = (
            select(SupplierOffer.supplier_id)
            .join(SupplierOfferExecutionLink, SupplierOfferExecutionLink.supplier_offer_id == SupplierOffer.id)
            .where(
                SupplierOfferExecutionLink.tour_id == tour_id,
                SupplierOfferExecutionLink.link_status == "active",
            )
        )
        br_stmt = (
            select(SupplierOffer.supplier_id)
            .join(SupplierOfferTourBridge, SupplierOfferTourBridge.supplier_offer_id == SupplierOffer.id)
            .where(
                SupplierOfferTourBridge.tour_id == tour_id,
                SupplierOfferTourBridge.status == "active",
            )
        )
        from_el = {int(x) for x in session.scalars(el_stmt).all()}
        from_br = {int(x) for x in session.scalars(br_stmt).all()}
        return from_el | from_br

    def _from_supplier_row(
        self,
        supplier: Supplier,
        *,
        context_type: AdminTelegramContactContext,
        context_id: int,
        path_codes: list[str],
    ) -> AdminSupplierTelegramContactResolutionRead:
        tg = supplier.primary_telegram_user_id
        configured = tg is not None
        status = "resolved_with_contact" if configured else "resolved_missing_contact"
        warnings: list[str] = []
        if not supplier.is_active:
            warnings.append("s1b_supplier_not_active")

        return AdminSupplierTelegramContactResolutionRead(
            context_type=context_type,
            context_id=context_id,
            resolution_status=status,
            supplier_id=supplier.id,
            supplier_code=supplier.code,
            supplier_display_name=supplier.display_name,
            supplier_is_active=supplier.is_active,
            primary_telegram_user_id=int(tg) if tg is not None else None,
            telegram_contact_configured=configured,
            resolution_path_codes=path_codes,
            linked_supplier_ids=[],
            readiness_warnings=warnings,
        )
