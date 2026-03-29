from __future__ import annotations

from sqlalchemy.orm import Session

from app.schemas.prepared import PaymentSummaryRead
from app.services.order_read import OrderReadService
from app.services.payment_read import PaymentReadService


class PaymentSummaryService:
    def __init__(
        self,
        order_read_service: OrderReadService | None = None,
        payment_read_service: PaymentReadService | None = None,
    ) -> None:
        self.order_read_service = order_read_service or OrderReadService()
        self.payment_read_service = payment_read_service or PaymentReadService()

    def get_order_payment_summary(
        self,
        session: Session,
        *,
        order_id: int,
    ) -> PaymentSummaryRead | None:
        order = self.order_read_service.get_order(session, order_id=order_id)
        if order is None:
            return None

        payments = self.payment_read_service.list_by_order(session, order_id=order_id)
        latest_payment = payments[0] if payments else None

        return PaymentSummaryRead(
            order=order,
            payments=payments,
            latest_payment=latest_payment,
        )
