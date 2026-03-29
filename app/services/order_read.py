from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import BookingStatus
from app.repositories.order import OrderRepository
from app.schemas.order import OrderRead


class OrderReadService:
    def __init__(self, order_repository: OrderRepository | None = None) -> None:
        self.order_repository = order_repository or OrderRepository()

    def get_order(self, session: Session, *, order_id: int) -> OrderRead | None:
        order = self.order_repository.get(session, order_id)
        if order is None:
            return None
        return OrderRead.model_validate(order)

    def list_by_user(self, session: Session, *, user_id: int, limit: int = 100, offset: int = 0) -> list[OrderRead]:
        orders = self.order_repository.list_by_user(session, user_id=user_id, limit=limit, offset=offset)
        return [OrderRead.model_validate(order) for order in orders]

    def list_by_tour(self, session: Session, *, tour_id: int, limit: int = 100, offset: int = 0) -> list[OrderRead]:
        orders = self.order_repository.list_by_tour(session, tour_id=tour_id, limit=limit, offset=offset)
        return [OrderRead.model_validate(order) for order in orders]

    def list_by_booking_status(
        self,
        session: Session,
        *,
        booking_status: BookingStatus,
        limit: int = 100,
        offset: int = 0,
    ) -> list[OrderRead]:
        orders = self.order_repository.list_by_booking_status(
            session,
            booking_status=booking_status,
            limit=limit,
            offset=offset,
        )
        return [OrderRead.model_validate(order) for order in orders]
