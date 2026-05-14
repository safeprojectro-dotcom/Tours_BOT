"""B16: read-only Admin OPS dashboard — aggregates tours, orders, handoffs, publications, execution links."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from collections.abc import Callable

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import (
    CancellationStatus,
    PaymentStatus,
    SupplierExecutionAttemptStatus,
    SupplierExecutionRequestStatus,
    SupplierExecutionSourceEntityType,
    SupplierOfferShowcasePublishAttemptStatus,
    TourStatus,
)
from app.models.handoff import Handoff
from app.models.notification_outbox import NotificationOutbox
from app.models.order import Order
from app.models.supplier import SupplierOfferExecutionLink
from app.models.supplier_execution import SupplierExecutionAttempt, SupplierExecutionRequest
from app.models.supplier_offer_showcase_publish_attempt import SupplierOfferShowcasePublishAttempt
from app.models.tour import Tour
from app.schemas.admin_ops_dashboard import (
    AdminOpsAttentionItemRead,
    AdminOpsAuditEventRead,
    AdminOpsConversionLinkRead,
    AdminOpsDashboardFiltersRead,
    AdminOpsDashboardRead,
    AdminOpsDashboardSummary,
    AdminOpsOrderListItem,
    AdminOpsRecentPublicationRead,
    AdminOpsUpcomingTourRead,
    OPS_DASHBOARD_SECTION_KEYS,
    OPS_DASHBOARD_SECTION_KEYS_SET,
)
from app.schemas.notification import NotificationOutboxStatus
from app.schemas.supplier_admin import AdminSupplierOfferReviewPackageRead
from app.services.admin_order_lifecycle import AdminOrderLifecycleKind, sql_predicate_for_lifecycle_kind
from app.services.admin_read import AdminReadService
from app.services.supplier_offer_review_package_service import SupplierOfferReviewPackageService

_RECENT_ORDERS_LIMIT = 20
_UPCOMING_TOURS_LIMIT = 15
_RECENT_PUBLICATIONS_LIMIT = 20
_CONVERSION_LINKS_LIMIT = 20
_MAX_ATTENTION_FROM_HOLDS = 8
_MAX_ATTENTION_FROM_EXPIRED = 5
_AUDIT_EVENTS_LIMIT_DEFAULT = 30

_TERMINAL_TOUR_STATUSES = (
    TourStatus.CANCELLED,
    TourStatus.COMPLETED,
)


def _ops_order_admin_path(order_id: int) -> str:
    return f"/admin/orders/{order_id}"


def _ops_tour_admin_path(tour_id: int) -> str:
    return f"/admin/tours/{tour_id}"


def _ops_supplier_offer_review_path(supplier_offer_id: int) -> str:
    return f"/admin/supplier-offers/{supplier_offer_id}/review-package"


def _ops_custom_request_admin_path(custom_request_id: int) -> str:
    return f"/admin/custom-requests/{custom_request_id}"


def _supplier_execution_request_admin_path(req: SupplierExecutionRequest) -> str:
    if req.source_entity_type == SupplierExecutionSourceEntityType.CUSTOM_MARKETPLACE_REQUEST:
        return _ops_custom_request_admin_path(req.source_entity_id)
    return "/admin/overview"


def _pred_closed_orders() -> Any:
    """Non-active cancellation states (excluding move transitions)."""
    return and_(
        Order.cancellation_status != CancellationStatus.ACTIVE,
        Order.cancellation_status.notin_(
            (
                CancellationStatus.MOVED_TO_ANOTHER_DATE,
                CancellationStatus.MOVED_TO_ANOTHER_TOUR,
            )
        ),
    )


class AdminOpsDashboardService:
    def __init__(
        self,
        *,
        admin_read: AdminReadService | None = None,
        review_pkg: SupplierOfferReviewPackageService | None = None,
    ) -> None:
        self._admin_read = admin_read or AdminReadService()
        self._review_pkg = review_pkg or SupplierOfferReviewPackageService()

    def read_dashboard(
        self,
        session: Session,
        *,
        now: datetime | None = None,
        days_ahead: int = 30,
        recent_days: int = 7,
        orders_limit: int = _RECENT_ORDERS_LIMIT,
        tours_limit: int = _UPCOMING_TOURS_LIMIT,
        publications_limit: int = _RECENT_PUBLICATIONS_LIMIT,
        conversion_links_limit: int = _CONVERSION_LINKS_LIMIT,
        attention_limit: int = 20,
        audit_events_limit: int = _AUDIT_EVENTS_LIMIT_DEFAULT,
        include_sections: frozenset[str] | None = None,
    ) -> AdminOpsDashboardRead:
        now_utc = now if now is not None else datetime.now(UTC)
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=UTC)

        active = OPS_DASHBOARD_SECTION_KEYS_SET if include_sections is None else include_sections
        window_end = now_utc + timedelta(days=days_ahead)
        recent_since = now_utc - timedelta(days=recent_days)

        prep_pkg_cache: dict[int, AdminSupplierOfferReviewPackageRead] = {}

        def prep_pkg(offer_id: int) -> AdminSupplierOfferReviewPackageRead:
            if offer_id not in prep_pkg_cache:
                prep_pkg_cache[offer_id] = self._review_pkg.review_package(session, offer_id=offer_id)
            return prep_pkg_cache[offer_id]

        upcoming_where = and_(
            Tour.departure_datetime >= now_utc,
            Tour.departure_datetime <= window_end,
            Tour.status.not_in(_TERMINAL_TOUR_STATUSES),
        )
        open_for_sale_where = Tour.status == TourStatus.OPEN_FOR_SALE

        upcoming_n = int(session.scalar(select(func.count()).select_from(Tour).where(upcoming_where)) or 0)
        ofs_n = int(session.scalar(select(func.count()).select_from(Tour).where(open_for_sale_where)) or 0)

        pred_hold = sql_predicate_for_lifecycle_kind(AdminOrderLifecycleKind.ACTIVE_TEMPORARY_HOLD)
        pred_expired = sql_predicate_for_lifecycle_kind(AdminOrderLifecycleKind.EXPIRED_UNPAID_HOLD)
        pred_confirmed = sql_predicate_for_lifecycle_kind(AdminOrderLifecycleKind.CONFIRMED_PAID)
        pred_rfd = sql_predicate_for_lifecycle_kind(AdminOrderLifecycleKind.READY_FOR_DEPARTURE_PAID)

        hold_n = int(session.scalar(select(func.count()).select_from(Order).where(pred_hold)) or 0)
        pending_pay_n = int(
            session.scalar(
                select(func.count()).select_from(Order).where(Order.payment_status == PaymentStatus.AWAITING_PAYMENT)
            )
            or 0
        )
        confirmed_n = int(
            session.scalar(select(func.count()).select_from(Order).where(or_(pred_confirmed, pred_rfd))) or 0
        )
        expired_or_closed_n = int(
            session.scalar(select(func.count()).select_from(Order).where(or_(pred_expired, _pred_closed_orders())))
            or 0
        )

        handoffs_n = int(
            session.scalar(select(func.count()).select_from(Handoff).where(Handoff.status == "open")) or 0
        )

        tour_offer_map = self._active_execution_offer_by_tour(session)

        attention_full = self._collect_attention_items(
            session,
            tour_offer_map=tour_offer_map,
            open_handoffs=handoffs_n,
            prep_pkg=prep_pkg,
        )

        orders_read_items: list[AdminOpsOrderListItem] = []
        if "recent_orders" in active:
            orders_read = self._admin_read.list_orders(
                session,
                limit=orders_limit,
                offset=0,
                created_since=recent_since,
            )
            orders_read_items = [
                AdminOpsOrderListItem.model_validate(
                    {**base.model_dump(), "admin_path": _ops_order_admin_path(base.id)},
                )
                for base in orders_read.items
            ]

        upcoming_read: list[AdminOpsUpcomingTourRead] = []
        if "upcoming_tours" in active:
            upcoming_rows = self._list_upcoming_tours(
                session,
                now_utc=now_utc,
                window_end=window_end,
                limit=tours_limit,
            )
            upcoming_read = [
                AdminOpsUpcomingTourRead(
                    tour_id=t.id,
                    code=t.code,
                    title_default=t.title_default,
                    departure_datetime=t.departure_datetime,
                    status=t.status,
                    seats_available=t.seats_available,
                    seats_total=t.seats_total,
                    admin_path=_ops_tour_admin_path(t.id),
                )
                for t in upcoming_rows
            ]

        publications_read: list[AdminOpsRecentPublicationRead] = []
        if "recent_publications" in active:
            pub_rows = self._list_recent_publications(
                session,
                limit=publications_limit,
                created_since=recent_since,
            )
            publications_read = []
            for p in pub_rows:
                pkg = prep_pkg(p.supplier_offer_id)
                publications_read.append(
                    AdminOpsRecentPublicationRead(
                        publish_attempt_id=p.id,
                        supplier_offer_id=p.supplier_offer_id,
                        status=p.status,
                        showcase_message_id=p.showcase_message_id,
                        channel_ref=p.channel_ref,
                        created_at=p.created_at,
                        admin_path=_ops_supplier_offer_review_path(p.supplier_offer_id),
                        prepare_conversion_chain_plan_path=pkg.prepare_conversion_chain_plan_path,
                        prepare_conversion_chain_plan_status=pkg.prepare_conversion_chain_plan_status,
                        prepare_conversion_chain_recommended_action=pkg.prepare_conversion_chain_recommended_action,
                        prepare_conversion_chain_blockers_count=pkg.prepare_conversion_chain_blockers_count,
                    )
                )

        conv_read: list[AdminOpsConversionLinkRead] = []
        if "conversion_links" in active:
            conv_read = self._list_conversion_link_reads(session, limit=conversion_links_limit, prep_pkg=prep_pkg)

        audit_read: list[AdminOpsAuditEventRead] = []
        if "audit_events" in active:
            audit_read = self._collect_audit_events(
                session,
                recent_since=recent_since,
                limit=audit_events_limit,
            )

        attention_out: list[AdminOpsAttentionItemRead] = (
            attention_full[:attention_limit] if "attention_items" in active else []
        )

        summary = AdminOpsDashboardSummary(
            upcoming_tours_count=upcoming_n,
            open_for_sale_tours_count=ofs_n,
            active_holds_count=hold_n,
            pending_payment_orders_count=pending_pay_n,
            confirmed_orders_count=confirmed_n,
            expired_or_closed_orders_count=expired_or_closed_n,
            open_handoffs_count=handoffs_n,
            attention_items_count=len(attention_full),
        )

        filters_echo = AdminOpsDashboardFiltersRead(
            days_ahead=days_ahead,
            recent_days=recent_days,
            orders_limit=orders_limit,
            tours_limit=tours_limit,
            publications_limit=publications_limit,
            conversion_links_limit=conversion_links_limit,
            attention_limit=attention_limit,
            audit_events_limit=audit_events_limit,
            include_sections=[k for k in OPS_DASHBOARD_SECTION_KEYS if k in active],
        )

        return AdminOpsDashboardRead(
            summary=summary,
            attention_items=attention_out,
            recent_orders=orders_read_items,
            upcoming_tours=upcoming_read,
            recent_publications=publications_read,
            conversion_links=conv_read,
            audit_events=audit_read,
            filters=filters_echo,
            generated_at=now_utc,
        )

    def _active_execution_offer_by_tour(self, session: Session) -> dict[int, int]:
        stmt = select(SupplierOfferExecutionLink).where(SupplierOfferExecutionLink.link_status == "active")
        rows = list(session.scalars(stmt).all())
        out: dict[int, int] = {}
        for row in rows:
            if row.tour_id not in out:
                out[row.tour_id] = row.supplier_offer_id
        return out

    def _list_upcoming_tours(
        self, session: Session, *, now_utc: datetime, window_end: datetime, limit: int
    ) -> list[Tour]:
        stmt = (
            select(Tour)
            .where(
                and_(
                    Tour.departure_datetime >= now_utc,
                    Tour.departure_datetime <= window_end,
                    Tour.status.not_in(_TERMINAL_TOUR_STATUSES),
                )
            )
            .order_by(Tour.departure_datetime.asc(), Tour.id.asc())
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def _list_recent_publications(
        self,
        session: Session,
        *,
        limit: int,
        created_since: datetime | None,
    ) -> list[SupplierOfferShowcasePublishAttempt]:
        stmt = select(SupplierOfferShowcasePublishAttempt)
        if created_since is not None:
            stmt = stmt.where(SupplierOfferShowcasePublishAttempt.created_at >= created_since)
        stmt = (
            stmt.order_by(
                SupplierOfferShowcasePublishAttempt.created_at.desc(),
                SupplierOfferShowcasePublishAttempt.id.desc(),
            ).limit(limit)
        )
        return list(session.scalars(stmt).all())

    def _collect_audit_events(
        self,
        session: Session,
        *,
        recent_since: datetime,
        limit: int,
    ) -> list[AdminOpsAuditEventRead]:
        """B16E: merge recent showcase/outbox/supplier-execution signals (read-only)."""
        per_source = min(100, max(limit, 20))
        events: list[AdminOpsAuditEventRead] = []

        pub_rows = self._list_recent_publications(
            session, limit=per_source, created_since=recent_since
        )
        for p in pub_rows:
            is_failed = p.status == SupplierOfferShowcasePublishAttemptStatus.FAILED
            err = (p.error_code or p.error_message or "").strip()
            summary = f"Offer #{p.supplier_offer_id} · {p.provider} · {p.status}"
            if is_failed and err:
                summary = f"{summary}: {err[:160]}"
            events.append(
                AdminOpsAuditEventRead(
                    kind="showcase_publish_failed" if is_failed else "showcase_publish_attempt",
                    severity="error" if is_failed else "info",
                    title="Showcase publish failed" if is_failed else "Showcase publish attempt",
                    summary=summary,
                    occurred_at=p.created_at,
                    admin_path=_ops_supplier_offer_review_path(p.supplier_offer_id),
                    related_supplier_offer_id=p.supplier_offer_id,
                    source_record_id=p.id,
                )
            )

        ob_stmt = (
            select(NotificationOutbox)
            .where(
                NotificationOutbox.status == NotificationOutboxStatus.FAILED.value,
                NotificationOutbox.updated_at >= recent_since,
            )
            .order_by(NotificationOutbox.updated_at.desc(), NotificationOutbox.id.desc())
            .limit(per_source)
        )
        for row in session.scalars(ob_stmt).all():
            tail = f" · {row.channel} · {row.event_type}"
            events.append(
                AdminOpsAuditEventRead(
                    kind="notification_outbox_failed",
                    severity="error",
                    title="Notification outbox delivery failed",
                    summary=(row.title[:200] + tail) if row.title else f"Order #{row.order_id}{tail}",
                    occurred_at=row.updated_at,
                    admin_path=_ops_order_admin_path(row.order_id),
                    related_order_id=row.order_id,
                    source_record_id=row.id,
                )
            )

        req_stmt = (
            select(SupplierExecutionRequest)
            .where(
                SupplierExecutionRequest.status.in_(
                    (
                        SupplierExecutionRequestStatus.FAILED,
                        SupplierExecutionRequestStatus.BLOCKED,
                    )
                ),
                SupplierExecutionRequest.updated_at >= recent_since,
            )
            .order_by(SupplierExecutionRequest.updated_at.desc(), SupplierExecutionRequest.id.desc())
            .limit(per_source)
        )
        for req in session.scalars(req_stmt).all():
            sev: Literal["error", "warning"] = (
                "error" if req.status == SupplierExecutionRequestStatus.FAILED else "warning"
            )
            note = (req.validation_error or req.audit_notes or "").strip()
            summary = f"Request #{req.id} · {req.status} · {req.source_entry_point}"
            if note:
                summary = f"{summary}: {note[:160]}"
            events.append(
                AdminOpsAuditEventRead(
                    kind="supplier_execution_request",
                    severity=sev,
                    title=f"Supplier execution request ({req.status})",
                    summary=summary,
                    occurred_at=req.updated_at,
                    admin_path=_supplier_execution_request_admin_path(req),
                    source_record_id=req.id,
                )
            )

        att_stmt = (
            select(SupplierExecutionAttempt, SupplierExecutionRequest)
            .join(
                SupplierExecutionRequest,
                SupplierExecutionRequest.id == SupplierExecutionAttempt.execution_request_id,
            )
            .where(
                SupplierExecutionAttempt.status == SupplierExecutionAttemptStatus.FAILED,
                SupplierExecutionAttempt.created_at >= recent_since,
            )
            .order_by(
                SupplierExecutionAttempt.created_at.desc(),
                SupplierExecutionAttempt.id.desc(),
            )
            .limit(per_source)
        )
        for att, req in session.execute(att_stmt).all():
            err = (att.error_code or att.error_message or "").strip()
            summary = f"Attempt #{att.attempt_number} · {att.channel_type}"
            if err:
                summary = f"{summary}: {err[:160]}"
            events.append(
                AdminOpsAuditEventRead(
                    kind="supplier_execution_attempt_failed",
                    severity="error",
                    title="Supplier execution attempt failed",
                    summary=summary,
                    occurred_at=att.created_at,
                    admin_path=_supplier_execution_request_admin_path(req),
                    source_record_id=att.id,
                )
            )

        events.sort(key=lambda e: (e.occurred_at, e.source_record_id or 0), reverse=True)
        return events[:limit]

    def _list_conversion_link_reads(
        self,
        session: Session,
        *,
        limit: int,
        prep_pkg: Callable[[int], AdminSupplierOfferReviewPackageRead],
    ) -> list[AdminOpsConversionLinkRead]:
        stmt = (
            select(SupplierOfferExecutionLink, Tour.code)
            .join(Tour, Tour.id == SupplierOfferExecutionLink.tour_id)
            .order_by(SupplierOfferExecutionLink.id.desc())
            .limit(limit)
        )
        reads: list[AdminOpsConversionLinkRead] = []
        for link, code in session.execute(stmt).all():
            pkg = prep_pkg(link.supplier_offer_id)
            so_path = _ops_supplier_offer_review_path(link.supplier_offer_id)
            tour_path = _ops_tour_admin_path(link.tour_id)
            reads.append(
                AdminOpsConversionLinkRead(
                    execution_link_id=link.id,
                    supplier_offer_id=link.supplier_offer_id,
                    tour_id=link.tour_id,
                    tour_code=code,
                    link_status=link.link_status,
                    supplier_offer_admin_path=so_path,
                    tour_admin_path=tour_path,
                    admin_path=so_path,
                    prepare_conversion_chain_plan_path=pkg.prepare_conversion_chain_plan_path,
                    prepare_conversion_chain_plan_status=pkg.prepare_conversion_chain_plan_status,
                    prepare_conversion_chain_recommended_action=pkg.prepare_conversion_chain_recommended_action,
                    prepare_conversion_chain_blockers_count=pkg.prepare_conversion_chain_blockers_count,
                )
            )
        return reads

    def _collect_attention_items(
        self,
        session: Session,
        *,
        tour_offer_map: dict[int, int],
        open_handoffs: int,
        prep_pkg: Callable[[int], AdminSupplierOfferReviewPackageRead],
    ) -> list[AdminOpsAttentionItemRead]:
        items: list[AdminOpsAttentionItemRead] = []

        hold_stmt = (
            select(Order)
            .options(selectinload(Order.tour))
            .where(sql_predicate_for_lifecycle_kind(AdminOrderLifecycleKind.ACTIVE_TEMPORARY_HOLD))
            .order_by(Order.reservation_expires_at.asc().nulls_last(), Order.id.asc())
            .limit(_MAX_ATTENTION_FROM_HOLDS)
        )
        for o in session.scalars(hold_stmt).all():
            offer_id = tour_offer_map.get(o.tour_id)
            if offer_id is not None:
                pkg = prep_pkg(offer_id)
                plan_path = pkg.prepare_conversion_chain_plan_path
                st = pkg.prepare_conversion_chain_plan_status
                rec = pkg.prepare_conversion_chain_recommended_action
                bc = pkg.prepare_conversion_chain_blockers_count
            else:
                plan_path = None
                st = None
                rec = None
                bc = None
            items.append(
                AdminOpsAttentionItemRead(
                    kind="payment_pending",
                    severity="info",
                    title=f"Order #{o.id} pending payment",
                    summary="Temporary hold active; payment not confirmed yet.",
                    admin_path=_ops_order_admin_path(o.id),
                    related_order_id=o.id,
                    related_tour_id=o.tour_id,
                    related_supplier_offer_id=offer_id,
                    prepare_conversion_chain_plan_path=plan_path,
                    prepare_conversion_chain_plan_status=st,
                    prepare_conversion_chain_recommended_action=rec,
                    prepare_conversion_chain_blockers_count=bc,
                )
            )

        ex_stmt = (
            select(Order)
            .options(selectinload(Order.tour))
            .where(sql_predicate_for_lifecycle_kind(AdminOrderLifecycleKind.EXPIRED_UNPAID_HOLD))
            .order_by(Order.updated_at.desc(), Order.id.desc())
            .limit(_MAX_ATTENTION_FROM_EXPIRED)
        )
        for o in session.scalars(ex_stmt).all():
            offer_id = tour_offer_map.get(o.tour_id)
            if offer_id is not None:
                pkg = prep_pkg(offer_id)
                plan_path = pkg.prepare_conversion_chain_plan_path
                st = pkg.prepare_conversion_chain_plan_status
                rec = pkg.prepare_conversion_chain_recommended_action
                bc = pkg.prepare_conversion_chain_blockers_count
            else:
                plan_path = None
                st = None
                rec = None
                bc = None
            items.append(
                AdminOpsAttentionItemRead(
                    kind="hold_expired_unpaid",
                    severity="warning",
                    title=f"Order #{o.id} expired unpaid hold",
                    summary="Reservation cancelled for non-payment; verify seats and customer comms if needed.",
                    admin_path=_ops_order_admin_path(o.id),
                    related_order_id=o.id,
                    related_tour_id=o.tour_id,
                    related_supplier_offer_id=offer_id,
                    prepare_conversion_chain_plan_path=plan_path,
                    prepare_conversion_chain_plan_status=st,
                    prepare_conversion_chain_recommended_action=rec,
                    prepare_conversion_chain_blockers_count=bc,
                )
            )

        if open_handoffs > 0:
            items.append(
                AdminOpsAttentionItemRead(
                    kind="open_handoffs",
                    severity="info",
                    title=f"{open_handoffs} open handoff(s)",
                    summary="Operator queue has open handoffs; review assignments and resolution.",
                    admin_path="/admin/handoffs",
                )
            )

        fail_stmt = (
            select(SupplierOfferShowcasePublishAttempt)
            .where(SupplierOfferShowcasePublishAttempt.status == SupplierOfferShowcasePublishAttemptStatus.FAILED)
            .order_by(SupplierOfferShowcasePublishAttempt.created_at.desc())
            .limit(5)
        )
        for a in session.scalars(fail_stmt).all():
            err = (a.error_code or a.error_message or "failed")[:120]
            pkg = prep_pkg(a.supplier_offer_id)
            items.append(
                AdminOpsAttentionItemRead(
                    kind="showcase_publish_failed",
                    severity="warning",
                    title=f"Showcase publish failed (offer #{a.supplier_offer_id})",
                    summary=f"Attempt #{a.id}: {err}",
                    admin_path=_ops_supplier_offer_review_path(a.supplier_offer_id),
                    related_supplier_offer_id=a.supplier_offer_id,
                    prepare_conversion_chain_plan_path=pkg.prepare_conversion_chain_plan_path,
                    prepare_conversion_chain_plan_status=pkg.prepare_conversion_chain_plan_status,
                    prepare_conversion_chain_recommended_action=pkg.prepare_conversion_chain_recommended_action,
                    prepare_conversion_chain_blockers_count=pkg.prepare_conversion_chain_blockers_count,
                )
            )

        return items
