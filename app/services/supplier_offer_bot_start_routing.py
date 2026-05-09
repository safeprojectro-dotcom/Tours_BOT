"""B11: `/start supoffer_<id>` — execution-link + Tour gates for Mini App deep links (read-only)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy.orm import Session

from app.models.enums import TourSalesMode, TourStatus
from app.models.supplier import SupplierOffer
from app.models.tour import Tour
from app.repositories.supplier_offer_execution_link import SupplierOfferExecutionLinkRepository
from app.services.customer_catalog_visibility import tour_is_customer_catalog_visible
from app.services.supplier_offer_deep_link import mini_app_tour_detail_url


class SupplierOfferStartCopyBucket(StrEnum):
    """Customer-facing copy bucket for `/start supoffer_<id>` (B10.6A). Does not change URL resolution."""

    EXACT_TOUR_MINI_APP = "exact_tour_mini_app"
    PUBLISHED_NO_EXECUTION_LINK = "published_no_execution_link"
    PUBLISHED_DEPARTURE_NOT_IN_CATALOG = "published_departure_not_in_catalog"
    PUBLISHED_DEPARTURE_NOT_VISIBLE = "published_departure_not_visible"
    PUBLISHED_LINK_BROKEN = "published_link_broken"
    PUBLISHED_MINI_APP_BASE_MISSING = "published_mini_app_base_missing"


@dataclass(frozen=True, slots=True)
class SupplierOfferStartMiniAppRouting:
    """Routing for published supplier-offer `/start`; no mutations."""

    #: Primary WebApp URL to `/tours/{code}` — only when safe for Mini App catalog detail (`OPEN_FOR_SALE` + visibility).
    exact_tour_mini_app_url: str | None
    #: Tour **code** for intro copy (`None` unless `exact_tour_mini_app_url` is set).
    linked_tour_code: str | None
    #: Whether linked Tour is **full_bus** (copy must not imply per-seat self-serve).
    linked_is_full_bus: bool
    #: Which customer message template to use (derived read-only; B10.6A).
    copy_bucket: SupplierOfferStartCopyBucket
    #: Tour code when link exists and tour row exists (for softer fallback copy); may be absent.
    context_tour_code: str | None


def _empty_nav(*, bucket: SupplierOfferStartCopyBucket) -> SupplierOfferStartMiniAppRouting:
    return SupplierOfferStartMiniAppRouting(
        exact_tour_mini_app_url=None,
        linked_tour_code=None,
        linked_is_full_bus=False,
        copy_bucket=bucket,
        context_tour_code=None,
    )


def resolve_sup_offer_start_mini_app_routing(
    session: Session,
    *,
    offer: SupplierOffer,
    mini_app_base_url: str,
    now_utc: datetime | None = None,
) -> SupplierOfferStartMiniAppRouting:
    """Pick safe Mini App target from active `supplier_offer_execution_links` only (B11).

    **copy_bucket** classifies published-offer state for customer copy (B10.6A) without changing gates.
    """
    repos = SupplierOfferExecutionLinkRepository()
    active = repos.get_active_for_offer(session, supplier_offer_id=offer.id, for_update=False)
    if active is None:
        return _empty_nav(bucket=SupplierOfferStartCopyBucket.PUBLISHED_NO_EXECUTION_LINK)

    tour = session.get(Tour, active.tour_id)
    if tour is None:
        return _empty_nav(bucket=SupplierOfferStartCopyBucket.PUBLISHED_LINK_BROKEN)

    code = (tour.code or "").strip()
    ctx_code = code or None
    if not code:
        return SupplierOfferStartMiniAppRouting(
            exact_tour_mini_app_url=None,
            linked_tour_code=None,
            linked_is_full_bus=False,
            copy_bucket=SupplierOfferStartCopyBucket.PUBLISHED_LINK_BROKEN,
            context_tour_code=None,
        )

    now = now_utc or datetime.now(UTC)
    if tour.status != TourStatus.OPEN_FOR_SALE:
        return SupplierOfferStartMiniAppRouting(
            exact_tour_mini_app_url=None,
            linked_tour_code=None,
            linked_is_full_bus=False,
            copy_bucket=SupplierOfferStartCopyBucket.PUBLISHED_DEPARTURE_NOT_IN_CATALOG,
            context_tour_code=ctx_code,
        )

    if not tour_is_customer_catalog_visible(
        departure_datetime=tour.departure_datetime,
        sales_deadline=tour.sales_deadline,
        now=now,
    ):
        return SupplierOfferStartMiniAppRouting(
            exact_tour_mini_app_url=None,
            linked_tour_code=None,
            linked_is_full_bus=False,
            copy_bucket=SupplierOfferStartCopyBucket.PUBLISHED_DEPARTURE_NOT_VISIBLE,
            context_tour_code=ctx_code,
        )

    base = (mini_app_base_url or "").strip()
    if not base:
        return SupplierOfferStartMiniAppRouting(
            exact_tour_mini_app_url=None,
            linked_tour_code=None,
            linked_is_full_bus=tour.sales_mode == TourSalesMode.FULL_BUS,
            copy_bucket=SupplierOfferStartCopyBucket.PUBLISHED_MINI_APP_BASE_MISSING,
            context_tour_code=ctx_code,
        )

    is_fb = tour.sales_mode == TourSalesMode.FULL_BUS
    url = mini_app_tour_detail_url(mini_app_url=mini_app_base_url, tour_code=code)
    return SupplierOfferStartMiniAppRouting(
        exact_tour_mini_app_url=url,
        linked_tour_code=code,
        linked_is_full_bus=is_fb,
        copy_bucket=SupplierOfferStartCopyBucket.EXACT_TOUR_MINI_APP,
        context_tour_code=ctx_code,
    )
