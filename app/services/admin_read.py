"""Read-only admin visibility (lists + overview)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.handoff import Handoff
from app.models.order import Order
from app.models.tour import Tour
from app.models.waitlist import WaitlistEntry
from app.repositories.order import OrderRepository
from app.repositories.tour import TourRepository
from app.schemas.admin import (
    AdminOrderListItem,
    AdminOrderListRead,
    AdminOverviewRead,
    AdminTourListItem,
    AdminTourListRead,
)
from app.services.admin_order_lifecycle import describe_order_admin_lifecycle


class AdminReadService:
    def __init__(
        self,
        *,
        tour_repository: TourRepository | None = None,
        order_repository: OrderRepository | None = None,
    ) -> None:
        self._tours = tour_repository or TourRepository()
        self._orders = order_repository or OrderRepository()

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

    def list_tours(self, session: Session, *, limit: int, offset: int) -> AdminTourListRead:
        rows = self._tours.list_by_departure_desc(session, limit=limit, offset=offset)
        items = [
            AdminTourListItem(
                id=t.id,
                code=t.code,
                title_default=t.title_default,
                departure_datetime=t.departure_datetime,
                status=t.status,
                seats_total=t.seats_total,
                seats_available=t.seats_available,
                currency=t.currency,
                base_price=t.base_price,
            )
            for t in rows
        ]
        return AdminTourListRead(items=items, total_returned=len(items))

    def list_orders(self, session: Session, *, limit: int, offset: int) -> AdminOrderListRead:
        rows = self._orders.list_recent_for_admin(session, limit=limit, offset=offset)
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
