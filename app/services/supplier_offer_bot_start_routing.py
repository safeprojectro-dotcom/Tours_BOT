"""B11: `/start supoffer_<id>` — execution-link + Tour gates for Mini App deep links (read-only)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import TourSalesMode, TourStatus
from app.models.supplier import SupplierOffer
from app.models.tour import Tour
from app.repositories.supplier_offer_execution_link import SupplierOfferExecutionLinkRepository
from app.services.customer_catalog_visibility import tour_is_customer_catalog_visible
from app.services.supplier_offer_deep_link import mini_app_tour_detail_url


@dataclass(frozen=True, slots=True)
class SupplierOfferStartMiniAppRouting:
    """Routing for published supplier-offer `/start`; no mutations."""

    #: Primary WebApp URL to `/tours/{code}` — only when safe for Mini App catalog detail (`OPEN_FOR_SALE` + visibility).
    exact_tour_mini_app_url: str | None
    #: Tour **code** for intro copy (`None` unless `exact_tour_mini_app_url` is set).
    linked_tour_code: str | None
    #: Whether linked Tour is **full_bus** (copy must not imply per-seat self-serve).
    linked_is_full_bus: bool


def _empty_nav() -> SupplierOfferStartMiniAppRouting:
    return SupplierOfferStartMiniAppRouting(
        exact_tour_mini_app_url=None,
        linked_tour_code=None,
        linked_is_full_bus=False,
    )


def resolve_sup_offer_start_mini_app_routing(
    session: Session,
    *,
    offer: SupplierOffer,
    mini_app_base_url: str,
    now_utc: datetime | None = None,
) -> SupplierOfferStartMiniAppRouting:
    """Pick safe Mini App target from active `supplier_offer_execution_links` only (B11)."""
    repos = SupplierOfferExecutionLinkRepository()
    active = repos.get_active_for_offer(session, supplier_offer_id=offer.id, for_update=False)
    if active is None:
        return _empty_nav()

    tour = session.get(Tour, active.tour_id)
    if tour is None:
        return _empty_nav()

    code = (tour.code or "").strip()
    if not code:
        return _empty_nav()

    now = now_utc or datetime.now(UTC)
    if tour.status != TourStatus.OPEN_FOR_SALE:
        return _empty_nav()

    if not tour_is_customer_catalog_visible(
        departure_datetime=tour.departure_datetime,
        sales_deadline=tour.sales_deadline,
        now=now,
    ):
        return _empty_nav()

    if not mini_app_base_url.strip():
        return _empty_nav()

    is_fb = tour.sales_mode == TourSalesMode.FULL_BUS
    url = mini_app_tour_detail_url(mini_app_url=mini_app_base_url, tour_code=code)
    return SupplierOfferStartMiniAppRouting(
        exact_tour_mini_app_url=url,
        linked_tour_code=code,
        linked_is_full_bus=is_fb,
    )
