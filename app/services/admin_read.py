"""Read-only admin visibility (lists + overview)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import TourStatus
from app.models.handoff import Handoff
from app.models.order import Order
from app.models.tour import Tour
from app.models.waitlist import WaitlistEntry
from app.repositories.handoff import HandoffRepository
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository
from app.repositories.tour import TourRepository
from app.schemas.admin import (
    AdminBoardingPointSummary,
    AdminBoardingPointTranslationItem,
    AdminHandoffListRead,
    AdminHandoffRead,
    AdminHandoffSummaryItem,
    AdminOrderDetailRead,
    AdminOrderListItem,
    AdminOrderListRead,
    AdminOrderPersistenceSnapshot,
    AdminOverviewRead,
    AdminPaymentSummaryItem,
    AdminTourDetailRead,
    AdminTourListItem,
    AdminTourListRead,
    AdminTourSummary,
    AdminTranslationSummaryItem,
)
from app.services.admin_order_lifecycle import (
    AdminOrderLifecycleKind,
    describe_order_admin_lifecycle,
    sql_predicate_for_lifecycle_kind,
)
from app.services.admin_handoff_queue import (
    compute_group_followup_assignment_visibility,
    compute_group_followup_queue_state,
    compute_group_followup_resolution_label,
    compute_group_followup_visibility,
    compute_handoff_queue_fields,
)
from app.services.admin_order_action_preview import compute_admin_action_preview
from app.services.admin_order_move_inspection import compute_move_placement_snapshot
from app.services.admin_order_move_readiness import compute_move_readiness
from app.services.admin_order_payment_visibility import compute_payment_correction_visibility


class AdminReadService:
    def __init__(
        self,
        *,
        tour_repository: TourRepository | None = None,
        order_repository: OrderRepository | None = None,
        payment_repository: PaymentRepository | None = None,
        handoff_repository: HandoffRepository | None = None,
    ) -> None:
        self._tours = tour_repository or TourRepository()
        self._orders = order_repository or OrderRepository()
        self._payments = payment_repository or PaymentRepository()
        self._handoffs = handoff_repository or HandoffRepository()

    _MAX_PAYMENT_ROWS = 10

    def get_tour_detail(self, session: Session, *, tour_id: int) -> AdminTourDetailRead | None:
        tour = self._tours.get_by_id_for_admin_detail(session, tour_id=tour_id)
        if tour is None:
            return None

        orders_count = (
            session.scalar(select(func.count()).select_from(Order).where(Order.tour_id == tour.id)) or 0
        )

        translations_sorted = sorted(
            tour.translations,
            key=lambda tr: (tr.language_code, tr.id),
        )
        translations = [
            AdminTranslationSummaryItem(language_code=tr.language_code, title=tr.title)
            for tr in translations_sorted
        ]

        boarding_sorted = sorted(
            tour.boarding_points,
            key=lambda bp: (bp.time, bp.id),
        )
        boarding_points: list[AdminBoardingPointSummary] = []
        for bp in boarding_sorted:
            tr_sorted = sorted(
                bp.translations,
                key=lambda t: (t.language_code, t.id),
            )
            bp_tr = [
                AdminBoardingPointTranslationItem(
                    language_code=t.language_code,
                    city=t.city,
                    address=t.address,
                    notes=t.notes,
                )
                for t in tr_sorted
            ]
            boarding_points.append(
                AdminBoardingPointSummary(
                    id=bp.id,
                    city=bp.city,
                    address=bp.address,
                    time=bp.time,
                    notes=bp.notes,
                    translations=bp_tr,
                )
            )

        return AdminTourDetailRead(
            id=tour.id,
            code=tour.code,
            title_default=tour.title_default,
            short_description_default=tour.short_description_default,
            full_description_default=tour.full_description_default,
            duration_days=tour.duration_days,
            departure_datetime=tour.departure_datetime,
            return_datetime=tour.return_datetime,
            base_price=tour.base_price,
            currency=tour.currency,
            seats_total=tour.seats_total,
            seats_available=tour.seats_available,
            sales_deadline=tour.sales_deadline,
            sales_mode=tour.sales_mode,
            status=tour.status,
            guaranteed_flag=tour.guaranteed_flag,
            cover_media_reference=tour.cover_media_reference,
            created_at=tour.created_at,
            updated_at=tour.updated_at,
            translations=translations,
            boarding_points=boarding_points,
            orders_count=int(orders_count),
        )

    def get_order_detail(self, session: Session, *, order_id: int) -> AdminOrderDetailRead | None:
        order = self._orders.get_by_id_for_admin_detail(session, order_id=order_id)
        if order is None:
            return None
        if order.tour is None or order.boarding_point is None:
            return None

        kind, summary = describe_order_admin_lifecycle(order)
        all_payments = self._payments.list_by_order(session, order_id=order.id)
        correction = compute_payment_correction_visibility(order, all_payments)
        open_handoff_count = sum(1 for h in order.handoffs if h.status == "open")
        action_preview = compute_admin_action_preview(
            lifecycle_kind=kind,
            correction=correction,
            open_handoff_count=open_handoff_count,
        )
        move_readiness = compute_move_readiness(
            order=order,
            lifecycle_kind=kind,
            correction=correction,
            open_handoff_count=open_handoff_count,
        )
        move_placement_snapshot = compute_move_placement_snapshot(order=order)
        pay_rows = all_payments[: self._MAX_PAYMENT_ROWS]
        payments = [
            AdminPaymentSummaryItem(
                id=p.id,
                provider=p.provider,
                external_payment_id=p.external_payment_id,
                amount=p.amount,
                currency=p.currency,
                status=p.status,
                created_at=p.created_at,
            )
            for p in pay_rows
        ]
        handoffs_sorted = sorted(
            order.handoffs,
            key=lambda h: (h.updated_at, h.id),
            reverse=True,
        )
        handoffs = []
        for h in handoffs_sorted:
            is_gf, src_lbl = compute_group_followup_visibility(reason=h.reason)
            is_agf, work_lbl = compute_group_followup_assignment_visibility(
                reason=h.reason,
                assigned_operator_id=h.assigned_operator_id,
                status=h.status,
            )
            res_lbl = compute_group_followup_resolution_label(reason=h.reason, status=h.status)
            q_state = compute_group_followup_queue_state(
                reason=h.reason,
                status=h.status,
                assigned_operator_id=h.assigned_operator_id,
            )
            handoffs.append(
                AdminHandoffSummaryItem(
                    id=h.id,
                    status=h.status,
                    reason=h.reason,
                    priority=h.priority,
                    created_at=h.created_at,
                    updated_at=h.updated_at,
                    is_group_followup=is_gf,
                    source_label=src_lbl,
                    is_assigned_group_followup=is_agf,
                    group_followup_work_label=work_lbl,
                    group_followup_resolution_label=res_lbl,
                    group_followup_queue_state=q_state,
                )
            )
        t = order.tour
        bp = order.boarding_point
        return AdminOrderDetailRead(
            id=order.id,
            user_id=order.user_id,
            lifecycle_kind=kind,
            lifecycle_summary=summary,
            persistence_snapshot=AdminOrderPersistenceSnapshot(
                booking_status=order.booking_status,
                payment_status=order.payment_status,
                cancellation_status=order.cancellation_status,
            ),
            tour=AdminTourSummary(
                id=t.id,
                code=t.code,
                title_default=t.title_default,
                departure_datetime=t.departure_datetime,
                status=t.status,
            ),
            boarding_point=AdminBoardingPointSummary(
                id=bp.id,
                city=bp.city,
                address=bp.address,
                time=bp.time,
                notes=bp.notes,
            ),
            seats_count=order.seats_count,
            total_amount=order.total_amount,
            currency=order.currency,
            source_channel=order.source_channel,
            assigned_operator_id=order.assigned_operator_id,
            reservation_expires_at=order.reservation_expires_at,
            created_at=order.created_at,
            updated_at=order.updated_at,
            payment_correction_hint=correction.payment_correction_hint,
            needs_manual_review=correction.needs_manual_review,
            payment_records_count=correction.payment_records_count,
            latest_payment_status=correction.latest_payment_status,
            latest_payment_provider=correction.latest_payment_provider,
            latest_payment_created_at=correction.latest_payment_created_at,
            has_multiple_payment_entries=correction.has_multiple_payment_entries,
            has_paid_entry=correction.has_paid_entry,
            has_awaiting_payment_entry=correction.has_awaiting_payment_entry,
            suggested_admin_action=action_preview.suggested_admin_action.value,
            allowed_admin_actions=list(action_preview.allowed_admin_actions),
            payment_action_preview=action_preview.payment_action_preview,
            payments=payments,
            handoffs=handoffs,
            can_consider_move=move_readiness.can_consider_move,
            move_blockers=list(move_readiness.move_blockers),
            move_readiness_hint=move_readiness.move_readiness_hint,
            move_placement_snapshot=move_placement_snapshot,
        )

    def _handoff_to_read(self, h: Handoff) -> AdminHandoffRead:
        tour_id = tour_code = tour_title = None
        if h.order_id is not None and h.order is not None and h.order.tour is not None:
            t = h.order.tour
            tour_id, tour_code, tour_title = t.id, t.code, t.title_default
        is_open, needs_attention, age_bucket = compute_handoff_queue_fields(
            status=h.status,
            created_at=h.created_at,
        )
        is_gf, src_lbl = compute_group_followup_visibility(reason=h.reason)
        is_agf, work_lbl = compute_group_followup_assignment_visibility(
            reason=h.reason,
            assigned_operator_id=h.assigned_operator_id,
            status=h.status,
        )
        res_lbl = compute_group_followup_resolution_label(reason=h.reason, status=h.status)
        q_state = compute_group_followup_queue_state(
            reason=h.reason,
            status=h.status,
            assigned_operator_id=h.assigned_operator_id,
        )
        return AdminHandoffRead(
            id=h.id,
            status=h.status,
            reason=h.reason,
            priority=h.priority,
            created_at=h.created_at,
            updated_at=h.updated_at,
            user_id=h.user_id,
            order_id=h.order_id,
            assigned_operator_id=h.assigned_operator_id,
            tour_id=tour_id,
            tour_code=tour_code,
            tour_title_default=tour_title,
            is_open=is_open,
            needs_attention=needs_attention,
            age_bucket=age_bucket,
            is_group_followup=is_gf,
            source_label=src_lbl,
            is_assigned_group_followup=is_agf,
            group_followup_work_label=work_lbl,
            group_followup_resolution_label=res_lbl,
            group_followup_queue_state=q_state,
        )

    def list_handoffs(
        self,
        session: Session,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
        group_followup_queue: str | None = None,
    ) -> AdminHandoffListRead:
        rows = self._handoffs.list_for_admin(
            session,
            limit=limit,
            offset=offset,
            status=status,
            group_followup_queue=group_followup_queue,
        )
        items = [self._handoff_to_read(h) for h in rows]
        return AdminHandoffListRead(items=items, total_returned=len(items))

    def get_handoff_detail(self, session: Session, *, handoff_id: int) -> AdminHandoffRead | None:
        h = self._handoffs.get_by_id_for_admin_detail(session, handoff_id=handoff_id)
        if h is None:
            return None
        return self._handoff_to_read(h)

    def overview(self, session: Session) -> AdminOverviewRead:
        settings = get_settings()
        tours_n = session.scalar(select(func.count()).select_from(Tour)) or 0
        orders_n = session.scalar(select(func.count()).select_from(Order)) or 0
        handoffs_n = session.scalar(
            select(func.count()).select_from(Handoff).where(Handoff.status == "open")
        ) or 0
        waitlist_n = session.scalar(
            select(func.count()).select_from(WaitlistEntry).where(WaitlistEntry.status == "active")
        ) or 0
        return AdminOverviewRead(
            app_env=settings.app_env,
            tours_total_approx=int(tours_n),
            orders_total_approx=int(orders_n),
            open_handoffs_count=int(handoffs_n),
            active_waitlist_entries_count=int(waitlist_n),
        )

    def list_tours(
        self,
        session: Session,
        *,
        limit: int,
        offset: int,
        status: TourStatus | None = None,
        guaranteed_only: bool = False,
    ) -> AdminTourListRead:
        rows = self._tours.list_by_departure_desc(
            session,
            limit=limit,
            offset=offset,
            status=status,
            guaranteed_only=guaranteed_only,
        )
        items = [
            AdminTourListItem(
                id=t.id,
                code=t.code,
                title_default=t.title_default,
                departure_datetime=t.departure_datetime,
                status=t.status,
                sales_mode=t.sales_mode,
                seats_total=t.seats_total,
                seats_available=t.seats_available,
                currency=t.currency,
                base_price=t.base_price,
            )
            for t in rows
        ]
        return AdminTourListRead(items=items, total_returned=len(items))

    def list_orders(
        self,
        session: Session,
        *,
        limit: int,
        offset: int,
        lifecycle_kind: AdminOrderLifecycleKind | None = None,
        tour_id: int | None = None,
    ) -> AdminOrderListRead:
        lifecycle_where = (
            sql_predicate_for_lifecycle_kind(lifecycle_kind) if lifecycle_kind is not None else None
        )
        rows = self._orders.list_recent_for_admin(
            session,
            limit=limit,
            offset=offset,
            tour_id=tour_id,
            lifecycle_where=lifecycle_where,
        )
        items: list[AdminOrderListItem] = []
        for o in rows:
            kind, summary = describe_order_admin_lifecycle(o)
            tour_code = o.tour.code if o.tour is not None else ""
            items.append(
                AdminOrderListItem(
                    id=o.id,
                    user_id=o.user_id,
                    tour_id=o.tour_id,
                    tour_code=tour_code,
                    seats_count=o.seats_count,
                    total_amount=o.total_amount,
                    currency=o.currency,
                    created_at=o.created_at,
                    lifecycle_kind=kind,
                    lifecycle_summary=summary,
                )
            )
        return AdminOrderListRead(items=items, total_returned=len(items))
