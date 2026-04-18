from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository
from app.schemas.order import OrderRead
from app.schemas.payment import PaymentRead
from app.schemas.prepared import PaymentEntryRead


class PaymentEntryService:
    DEFAULT_PROVIDER = "mockpay"

    def __init__(
        self,
        *,
        order_repository: OrderRepository | None = None,
        payment_repository: PaymentRepository | None = None,
    ) -> None:
        self.order_repository = order_repository or OrderRepository()
        self.payment_repository = payment_repository or PaymentRepository()

    def start_payment_entry(
        self,
        session: Session,
        *,
        order_id: int,
        user_id: int,
        now: datetime | None = None,
    ) -> PaymentEntryRead | None:
        current_time = now or datetime.now(UTC)
        order = self.order_repository.get_for_update(session, order_id=order_id)
        if order is None or not self._is_order_valid_for_payment_entry(order=order, user_id=user_id, now=current_time):
            return None

        latest_payment = self.payment_repository.get_latest_by_order(session, order_id=order.id)
        reused_existing_payment = latest_payment is not None and latest_payment.status in {
            PaymentStatus.UNPAID,
            PaymentStatus.AWAITING_PAYMENT,
        }

        if reused_existing_payment:
            session_reference = latest_payment.external_payment_id or self._build_payment_session_reference(order.id)
            update_payload = {
                "status": PaymentStatus.AWAITING_PAYMENT,
                "external_payment_id": session_reference,
                "raw_payload": self._build_raw_payload(order_id=order.id, session_reference=session_reference),
            }
            payment = self.payment_repository.update(session, instance=latest_payment, data=update_payload)
        else:
            session_reference = self._build_payment_session_reference(order.id)
            payment = self.payment_repository.create(
                session,
                data={
                    "order_id": order.id,
                    "provider": self.DEFAULT_PROVIDER,
                    "external_payment_id": session_reference,
                    "amount": order.total_amount,
                    "currency": order.currency,
                    "status": PaymentStatus.AWAITING_PAYMENT,
                    "raw_payload": self._build_raw_payload(order_id=order.id, session_reference=session_reference),
                },
            )

        if order.payment_status != PaymentStatus.AWAITING_PAYMENT:
            order = self.order_repository.update(
                session,
                instance=order,
                data={"payment_status": PaymentStatus.AWAITING_PAYMENT},
            )

        return PaymentEntryRead(
            order=OrderRead.model_validate(order),
            payment=PaymentRead.model_validate(payment),
            payment_session_reference=session_reference,
            payment_url=None,
            reused_existing_payment=reused_existing_payment,
        )

    def is_order_valid_for_payment_entry(
        self,
        session: Session,
        *,
        order_id: int,
        user_id: int,
        now: datetime | None = None,
    ) -> bool:
        """Read-only Layer A gate — same rules as ``start_payment_entry`` without creating payments."""
        current_time = now or datetime.now(UTC)
        order = self.order_repository.get(session, order_id)
        if order is None:
            return False
        return self._is_order_valid_for_payment_entry(order=order, user_id=user_id, now=current_time)

    def _is_order_valid_for_payment_entry(self, *, order, user_id: int, now: datetime) -> bool:
        if order.user_id != user_id:
            return False
        if order.booking_status != BookingStatus.RESERVED:
            return False
        if order.payment_status != PaymentStatus.AWAITING_PAYMENT:
            return False
        if order.cancellation_status != CancellationStatus.ACTIVE:
            return False
        if order.reservation_expires_at is None or order.reservation_expires_at <= now:
            return False
        return True

    def _build_payment_session_reference(self, order_id: int) -> str:
        return f"mockpay-order-{order_id}-{uuid4().hex[:12]}"

    @staticmethod
    def _build_raw_payload(*, order_id: int, session_reference: str) -> dict[str, str]:
        return {
            "kind": "payment_entry",
            "order_id": str(order_id),
            "session_reference": session_reference,
        }
