"""B16D1.2: derive prepare-conversion-chain readiness from review-package shape only (read-only, no I/O)."""

from __future__ import annotations

from app.models.enums import SupplierOfferLifecycle, SupplierOfferPackagingStatus
from app.schemas.admin_prepare_conversion_chain_plan import (
    AdminPrepareConversionChainPlanStepRead,
    PrepareConversionChainPlanStepStatus,
    PrepareConversionChainPlanSummaryStatus,
)
from app.schemas.supplier_admin import AdminSupplierOfferReviewPackageRead

_STEP_BRIDGE = (
    "ensure_tour_bridge",
    "Ensure tour bridge",
    "Create or link a Tour for this supplier offer when prerequisites pass (future POST tour-bridge).",
)

_STEP_CATALOG = (
    "activate_tour_for_catalog",
    "Activate tour for catalog",
    "Open the linked tour for Mini App catalog listing when activation prechecks pass (future activate-for-catalog).",
)

_STEP_EXEC = (
    "ensure_active_execution_link",
    "Ensure active execution link",
    "Create an active supplier-offer execution link to the bridged tour when gates pass (future execution-link create).",
)


def eligibility_tuple(pkg: AdminSupplierOfferReviewPackageRead) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    offer = pkg.offer
    if offer.packaging_status is not SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH:
        blockers.append("Packaging must be approved_for_publish before an automated preparation chain.")
    if offer.lifecycle_status is SupplierOfferLifecycle.REJECTED:
        blockers.append("Offer lifecycle is rejected; resolve moderation before preparation.")
    if offer.lifecycle_status not in (SupplierOfferLifecycle.APPROVED, SupplierOfferLifecycle.PUBLISHED):
        if offer.lifecycle_status is not SupplierOfferLifecycle.REJECTED:
            blockers.append(
                "Offer lifecycle must be approved or published before execution-link-oriented preparation.",
            )
    return (len(blockers) == 0, blockers)


def build_steps(pkg: AdminSupplierOfferReviewPackageRead) -> tuple[list[AdminPrepareConversionChainPlanStepRead], list[str]]:
    plan_blockers: list[str] = []
    steps: list[AdminPrepareConversionChainPlanStepRead] = []

    br = pkg.bridge_readiness
    bridge_row = pkg.active_tour_bridge
    bridge_done = bridge_row is not None

    s1_blockers: list[str] = []
    if not bridge_done:
        s1_blockers.extend(br.missing_fields)
        s1_blockers.extend(br.blocking_codes)
        if not br.can_attempt_bridge:
            plan_blockers.extend(s1_blockers)

    s1_status: PrepareConversionChainPlanStepStatus
    if bridge_done:
        s1_status = "satisfied"
    elif br.can_attempt_bridge:
        s1_status = "pending"
    else:
        s1_status = "blocked"

    steps.append(
        AdminPrepareConversionChainPlanStepRead(
            code=_STEP_BRIDGE[0],
            title=_STEP_BRIDGE[1],
            summary=_STEP_BRIDGE[2],
            order_index=1,
            status=s1_status,
            already_satisfied=bridge_done,
            would_execute=(not bridge_done) and br.can_attempt_bridge,
            blockers=s1_blockers if not bridge_done else [],
            notes=[],
        )
    )

    lc = pkg.linked_tour_catalog
    s2_blockers: list[str] = []
    s2_notes: list[str] = []
    s2_status: PrepareConversionChainPlanStepStatus
    cat_done = False
    would_ex_cat = False

    if not bridge_done:
        s2_status = "not_applicable"
        s2_notes.append("Tour bridge is required before catalog activation.")
    elif lc is None:
        s2_status = "blocked"
        s2_blockers.append("Linked tour catalog readiness preview is unavailable.")
        plan_blockers.append("linked_tour_catalog_preview_unavailable")
    else:
        cat_done = bool(lc.catalog_listed_for_mini_app)
        if lc.b8_same_offer_date_conflict:
            s2_blockers.append("B8 same-offer date conflict blocks catalog activation.")
        s2_blockers.extend(lc.catalog_activation_missing_fields)
        if cat_done:
            s2_status = "satisfied"
        elif lc.can_activate_for_catalog and not s2_blockers:
            s2_status = "pending"
            would_ex_cat = True
        else:
            s2_status = "blocked"
            plan_blockers.extend(s2_blockers)

    steps.append(
        AdminPrepareConversionChainPlanStepRead(
            code=_STEP_CATALOG[0],
            title=_STEP_CATALOG[1],
            summary=_STEP_CATALOG[2],
            order_index=2,
            status=s2_status,
            already_satisfied=cat_done,
            would_execute=would_ex_cat,
            blockers=[b for b in s2_blockers if b],
            notes=s2_notes,
        )
    )

    ex = pkg.execution_links_review
    exec_done = ex.active_link is not None
    s3_blockers: list[str] = []
    s3_notes: list[str] = []
    s3_status: PrepareConversionChainPlanStepStatus
    would_ex_link = False
    if not bridge_done:
        s3_status = "not_applicable"
        s3_notes.append("Tour bridge is required before execution link creation.")
    elif exec_done:
        s3_status = "satisfied"
    elif ex.can_create_execution_link:
        s3_status = "pending"
        would_ex_link = True
    else:
        s3_status = "blocked"
        if ex.execution_link_precheck_note:
            s3_blockers.append(ex.execution_link_precheck_note)
            plan_blockers.append(ex.execution_link_precheck_note)

    steps.append(
        AdminPrepareConversionChainPlanStepRead(
            code=_STEP_EXEC[0],
            title=_STEP_EXEC[1],
            summary=_STEP_EXEC[2],
            order_index=3,
            status=s3_status,
            already_satisfied=exec_done,
            would_execute=would_ex_link,
            blockers=s3_blockers,
            notes=s3_notes,
        )
    )

    return steps, plan_blockers


def recommend_next(
    pkg: AdminSupplierOfferReviewPackageRead,
    steps: list[AdminPrepareConversionChainPlanStepRead],
) -> str | None:
    if pkg.operator_workflow.primary_next_action:
        return pkg.operator_workflow.primary_next_action
    for s in steps:
        if s.status == "pending":
            return s.title
        if s.status == "blocked" and s.blockers:
            return f"{s.title}: {s.blockers[0]}"
    if all(s.status == "satisfied" for s in steps):
        return "Internal preparation steps appear satisfied; use review-package for publish and wider funnel."
    return None


def plan_status(eligible: bool, steps: list[AdminPrepareConversionChainPlanStepRead]) -> PrepareConversionChainPlanSummaryStatus:
    if not eligible:
        return "ineligible"
    if all(s.status == "satisfied" for s in steps):
        return "already_prepared"
    if any(s.status == "blocked" for s in steps):
        return "blocked"
    if any(s.status == "pending" for s in steps):
        return "partial"
    return "blocked"


def blockers_count(eligibility_blockers: list[str], plan_blockers: list[str]) -> int:
    return len(set(eligibility_blockers) | set(plan_blockers))


def derive_prepare_conversion_chain_readiness(
    pkg: AdminSupplierOfferReviewPackageRead,
) -> tuple[PrepareConversionChainPlanSummaryStatus, str | None, int]:
    """Read-only snapshot: status label, recommended action string, distinct blocker count."""
    elig, elig_blockers = eligibility_tuple(pkg)
    steps, plan_blockers_list = build_steps(pkg)
    rec = recommend_next(pkg, steps)
    st = plan_status(elig, steps)
    bc = blockers_count(eligibility_blockers=elig_blockers, plan_blockers=plan_blockers_list)
    return st, rec, bc


__all__ = [
    "blockers_count",
    "build_steps",
    "derive_prepare_conversion_chain_readiness",
    "eligibility_tuple",
    "plan_status",
    "recommend_next",
]
