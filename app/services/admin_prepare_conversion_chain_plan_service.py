"""B16D1: read-only plan preview for future ``prepare_conversion_chain`` (uses review-package read model only)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.schemas.admin_prepare_conversion_chain_plan import AdminPrepareConversionChainPlanRead
from app.services.admin_navigation_paths import supplier_offer_prepare_conversion_chain_plan_path
from app.services.prepare_conversion_chain_readiness import (
    build_steps,
    eligibility_tuple,
    recommend_next,
)
from app.services.supplier_offer_review_package_service import SupplierOfferReviewPackageService

_WILL_NOT_DO: tuple[str, ...] = (
    "Publish to Telegram or send Telegram messages",
    "Create supplier showcase publish attempts",
    "Mutate orders, payments, reservations, or seat inventory",
    "Invoke Layer A mutation services or change Mini App routing",
)


class AdminPrepareConversionChainPlanService:
    def __init__(self, *, review_pkg: SupplierOfferReviewPackageService | None = None) -> None:
        self._review = review_pkg or SupplierOfferReviewPackageService()

    def read_plan(self, session: Session, *, offer_id: int) -> AdminPrepareConversionChainPlanRead:
        pkg = self._review.review_package(session, offer_id=offer_id)
        now = datetime.now(UTC)
        elig, elig_blockers = eligibility_tuple(pkg)
        steps, plan_blockers = build_steps(pkg)
        rec = recommend_next(pkg, steps)
        st = pkg.prepare_conversion_chain_plan_status
        bc = pkg.prepare_conversion_chain_blockers_count

        closure_next = pkg.conversion_closure.next_missing_step

        return AdminPrepareConversionChainPlanRead(
            supplier_offer_id=offer_id,
            prepare_conversion_chain_plan_path=supplier_offer_prepare_conversion_chain_plan_path(offer_id),
            prepare_conversion_chain_eligible=elig,
            eligibility_blockers=elig_blockers,
            steps=steps,
            plan_blockers=sorted(set(plan_blockers)),
            warnings=list(pkg.warnings),
            will_not_do=list(_WILL_NOT_DO),
            recommended_next_action=rec,
            prepare_conversion_chain_plan_status=st,
            prepare_conversion_chain_recommended_action=rec,
            prepare_conversion_chain_blockers_count=bc,
            review_package_path=f"/admin/supplier-offers/{offer_id}/review-package",
            conversion_closure_next_missing_step=closure_next,
            generated_at=now,
        )


__all__ = ["AdminPrepareConversionChainPlanService"]
