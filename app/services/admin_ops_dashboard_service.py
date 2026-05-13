"""B16: read-only Admin OPS dashboard — aggregates tours, orders, handoffs, publications, execution links."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import (
    CancellationStatus,
    PaymentStatus,
    SupplierOfferShowcasePublishAttemptStatus,
    TourStatus,
)
from app.models.handoff import Handoff
from app.models.order import Order
from app.models.supplier import SupplierOfferExecutionLink
from app.models.supplier_offer_showcase_publish_attempt import SupplierOfferShowcasePublishAttempt
from app.models.tour import Tour
from app.schemas.admin_ops_dashboard import (
    AdminOpsAttentionItemRead,
    AdminOpsConversionLinkRead,
    AdminOpsDashboardRead,
    AdminOpsDashboardSummary,
    AdminOpsRecentPublicationRead,
    AdminOpsUpcomingTourRead,
)
from app.services.admin_order_lifecycle import AdminOrderLifecycleKind, sql_predicate_for_lifecycle_kind
from app.services.admin_read import AdminReadService

_RECENT_ORDERS_LIMIT = 20
_UPCOMING_TOURS_LIMIT = 15
_RECENT_PUBLICATIONS_LIMIT = 15
_CONVERSION_LINKS_LIMIT = 20
_MAX_ATTENTION_FROM_HOLDS = 8
_MAX_ATTENTION_FROM_EXPIRED = 5

_TERMINAL_TOUR_STATUSES = (
    TourStatus.CANCELLED,
    TourStatus.COMPLETED,
)


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
    def __init__(self, *, admin_read: AdminReadService | None = None) -> None:
        self._admin_read = admin_read or AdminReadService()

    def read_dashboard(self, session: Session, *, now: datetime | None = None) -> AdminOpsDashboardRead:
        now_utc = now if now is not None else datetime.now(UTC)
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=UTC)

        upcoming_where = and_(
            Tour.departure_datetime >= now_utc,
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

        attention = self._collect_attention_items(
            session,
            tour_offer_map=tour_offer_map,
            open_handoffs=handoffs_n,
        )

        orders_read = self._admin_read.list_orders(session, limit=_RECENT_ORDERS_LIMIT, offset=0)
        upcoming_rows = self._list_upcoming_tours(session, now_utc=now_utc)
        upcoming_read = [
            AdminOpsUpcomingTourRead(
                tour_id=t.id,
                code=t.code,
                title_default=t.title_default,
                departure_datetime=t.departure_datetime,
                status=t.status,
                seats_available=t.seats_available,
                seats_total=t.seats_total,
            )
            for t in upcoming_rows
        ]

        pub_rows = self._list_recent_publications(session, limit=_RECENT_PUBLICATIONS_LIMIT)
        publications_read = [
            AdminOpsRecentPublicationRead(
                publish_attempt_id=p.id,
                supplier_offer_id=p.supplier_offer_id,
                status=p.status,
                showcase_message_id=p.showcase_message_id,
                channel_ref=p.channel_ref,
                created_at=p.created_at,
            )
            for p in pub_rows
        ]

        conv_read = self._list_conversion_link_reads(session, limit=_CONVERSION_LINKS_LIMIT)

        summary = AdminOpsDashboardSummary(
            upcoming_tours_count=upcoming_n,
            open_for_sale_tours_count=ofs_n,
            active_holds_count=hold_n,
            pending_payment_orders_count=pending_pay_n,
            confirmed_orders_count=confirmed_n,
            expired_or_closed_orders_count=expired_or_closed_n,
            open_handoffs_count=handoffs_n,
            attention_items_count=len(attention),
        )

        return AdminOpsDashboardRead(
            summary=summary,
            attention_items=attention,
            recent_orders=orders_read.items,
            upcoming_tours=upcoming_read,
            recent_publications=publications_read,
            conversion_links=conv_read,
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

    def _list_upcoming_tours(self, session: Session, *, now_utc: datetime, limit: int = _UPCOMING_TOURS_LIMIT) -> list[Tour]:
        stmt = (
            select(Tour)
            .where(
                and_(
                    Tour.departure_datetime >= now_utc,
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
        limit: int = _RECENT_PUBLICATIONS_LIMIT,
    ) -> list[SupplierOfferShowcasePublishAttempt]:
        stmt = (
            select(SupplierOfferShowcasePublishAttempt)
            .order_by(
                SupplierOfferShowcasePublishAttempt.created_at.desc(),
                SupplierOfferShowcasePublishAttempt.id.desc(),
            )
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def _list_conversion_link_reads(self, session: Session, *, limit: int) -> list[AdminOpsConversionLinkRead]:
        stmt = (
            select(SupplierOfferExecutionLink, Tour.code)
            .join(Tour, Tour.id == SupplierOfferExecutionLink.tour_id)
            .order_by(SupplierOfferExecutionLink.id.desc())
            .limit(limit)
        )
        reads: list[AdminOpsConversionLinkRead] = []
        for link, code in session.execute(stmt).all():
            reads.append(
                AdminOpsConversionLinkRead(
                    execution_link_id=link.id,
                    supplier_offer_id=link.supplier_offer_id,
                    tour_id=link.tour_id,
                    tour_code=code,
                    link_status=link.link_status,
                )
            )
        return reads

    def _collect_attention_items(
        self,
        session: Session,
        *,
        tour_offer_map: dict[int, int],
        open_handoffs: int,
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
            items.append(
                AdminOpsAttentionItemRead(
                    kind="payment_pending",
                    severity="info",
                    title=f"Order #{o.id} pending payment",
                    summary="Temporary hold active; payment not confirmed yet.",
                    admin_path=f"/admin/orders/{o.id}",
                    related_order_id=o.id,
                    related_tour_id=o.tour_id,
                    related_supplier_offer_id=offer_id,
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
            items.append(
                AdminOpsAttentionItemRead(
                    kind="hold_expired_unpaid",
                    severity="warning",
                    title=f"Order #{o.id} expired unpaid hold",
                    summary="Reservation cancelled for non-payment; verify seats and customer comms if needed.",
                    admin_path=f"/admin/orders/{o.id}",
                    related_order_id=o.id,
                    related_tour_id=o.tour_id,
                    related_supplier_offer_id=offer_id,
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
            items.append(
                AdminOpsAttentionItemRead(
                    kind="showcase_publish_failed",
                    severity="warning",
                    title=f"Showcase publish failed (offer #{a.supplier_offer_id})",
                    summary=f"Attempt #{a.id}: {err}",
                    admin_path=f"/admin/supplier-offers/{a.supplier_offer_id}/review-package",
                    related_supplier_offer_id=a.supplier_offer_id,
                )
            )

        return items
