"""B15C: exact Mini App tour target for supplier-offer channel publish and pre-publish execution links."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferLifecycle, SupplierOfferPackagingStatus, TourStatus
from app.models.supplier import SupplierOffer, SupplierOfferExecutionLink
from app.models.tour import Tour
from app.repositories.supplier import SupplierOfferRepository
from app.services.admin_tour_write import AdminTourWriteService
from app.services.supplier_offer_tour_bridge_service import SupplierOfferTourBridgeService

EXECUTION_LINK_REQUIRED_FOR_PUBLISH_EN = (
    "Execution link is required before channel publish because Rezervă must open the exact Mini App tour."
)
EXECUTION_LINK_REQUIRED_FOR_PUBLISH_RO = (
    "Este necesar un execution link înainte de publicarea pe canal: Rezervă trebuie să deschidă "
    "turul exact din Mini App."
)


def validate_execution_link_target_before_publish(
    session: Session,
    *,
    offer_id: int,
    tour_id: int,
) -> None:
    """Gate for creating/replacing an execution link before channel publish (B15C).

    Raises SupplierOfferExecutionLinkValidationError on failure.
    """
    from app.services.supplier_offer_execution_link_service import (
        SupplierOfferExecutionLinkNotFoundError,
        SupplierOfferExecutionLinkValidationError,
    )

    offers = SupplierOfferRepository()
    offer = offers.get_any(session, offer_id=offer_id)
    if offer is None:
        raise SupplierOfferExecutionLinkNotFoundError
    if offer.lifecycle_status == SupplierOfferLifecycle.REJECTED:
        raise SupplierOfferExecutionLinkValidationError("Cannot link execution tour for a rejected offer.")
    if offer.packaging_status is not SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH:
        raise SupplierOfferExecutionLinkValidationError("Packaging must be approved for publish before execution link.")
    if offer.lifecycle_status not in (
        SupplierOfferLifecycle.APPROVED,
        SupplierOfferLifecycle.PUBLISHED,
    ):
        raise SupplierOfferExecutionLinkValidationError(
            "Execution link requires a moderation-approved or published supplier offer.",
        )

    bridge = SupplierOfferTourBridgeService().get_active_bridge(session, supplier_offer_id=offer_id)
    if bridge is None or bridge.tour_id != tour_id:
        raise SupplierOfferExecutionLinkValidationError(
            "Execution link tour must match the active supplier-offer tour bridge.",
        )

    tour = session.get(Tour, tour_id)
    if tour is None:
        raise SupplierOfferExecutionLinkValidationError("Tour not found for execution linkage.")
    if tour.sales_mode != offer.sales_mode:
        raise SupplierOfferExecutionLinkValidationError("Tour sales_mode must match supplier offer sales_mode.")
    if tour.status in (TourStatus.CANCELLED, TourStatus.COMPLETED):
        raise SupplierOfferExecutionLinkValidationError("Tour status is not valid for operational linkage.")
    if tour.departure_datetime <= datetime.now(UTC):
        raise SupplierOfferExecutionLinkValidationError("Only future-departure tours can be linked.")
    if tour.status is not TourStatus.OPEN_FOR_SALE:
        raise SupplierOfferExecutionLinkValidationError("Linked tour must be open_for_sale before execution link.")

    preview = AdminTourWriteService().preview_catalog_activation_for_tour(session, tour_id=tour_id)
    if preview is None:
        raise SupplierOfferExecutionLinkValidationError("Cannot evaluate catalog state for linked tour.")
    if not preview.catalog_listed_for_mini_app:
        raise SupplierOfferExecutionLinkValidationError(
            "Tour must be catalog-listed for Mini App (customer visibility window) before execution link.",
        )


def tour_code_for_active_execution_link(session: Session, *, offer_id: int) -> str | None:
    """Return stripped tour code from the active execution link target, or None."""
    from app.repositories.supplier_offer_execution_link import SupplierOfferExecutionLinkRepository

    active = SupplierOfferExecutionLinkRepository().get_active_for_offer(
        session,
        supplier_offer_id=offer_id,
        for_update=False,
    )
    if active is None:
        return None
    tour = session.get(Tour, active.tour_id)
    if tour is None:
        return None
    code = (tour.code or "").strip()
    return code or None


def channel_publish_exact_tour_ready(session: Session, *, offer_id: int) -> tuple[bool, list[str]]:
    """True when an active execution link points at the bridged tour and catalog semantics allow channel Rezervă."""
    reasons: list[str] = []

    from app.repositories.supplier_offer_execution_link import SupplierOfferExecutionLinkRepository

    links = SupplierOfferExecutionLinkRepository()
    active: SupplierOfferExecutionLink | None = links.get_active_for_offer(
        session,
        supplier_offer_id=offer_id,
        for_update=False,
    )
    if active is None:
        reasons.append(EXECUTION_LINK_REQUIRED_FOR_PUBLISH_EN)
        reasons.append(EXECUTION_LINK_REQUIRED_FOR_PUBLISH_RO)
        return False, reasons

    bridge = SupplierOfferTourBridgeService().get_active_bridge(session, supplier_offer_id=offer_id)
    if bridge is None or bridge.tour_id != active.tour_id:
        reasons.append("Active execution link must match the active supplier-offer tour bridge.")
        return False, reasons

    tour = session.get(Tour, active.tour_id)
    if tour is None:
        reasons.append("Execution link references a missing tour.")
        return False, reasons
    if tour.status is not TourStatus.OPEN_FOR_SALE:
        reasons.append("Linked tour must be open_for_sale for channel publish.")
        return False, reasons
    if tour.departure_datetime <= datetime.now(UTC):
        reasons.append("Linked tour departure must be in the future.")
        return False, reasons

    preview = AdminTourWriteService().preview_catalog_activation_for_tour(session, tour_id=tour.id)
    if preview is None or not preview.catalog_listed_for_mini_app:
        reasons.append("Linked tour must be catalog-listed for Mini App before channel publish.")
        return False, reasons

    code = (tour.code or "").strip()
    if not code:
        reasons.append("Linked tour must have a tour_code for the Rezervă Mini App URL.")
        return False, reasons

    return True, []
