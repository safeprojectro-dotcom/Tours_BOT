from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository
from app.schemas.order import OrderRead
from app.schemas.payment import PaymentProviderResult, PaymentRead, PaymentReconciliationRead


class PaymentReconciliationService:
    NON_REFUNDABLE_STATUSES = {
        PaymentStatus.UNPAID,
        PaymentStatus.AWAITING_PAYMENT,
        PaymentStatus.PAID,
    }

    def __init__(
        self,
        *,
        order_repository: OrderRepository | None = None,
        payment_repository: PaymentRepository | None = None,
    ) -> None:
        self.order_repository = order_repository or OrderRepository()
        self.payment_repository = payment_repository or PaymentRepository()

    def reconcile_provider_result(
        self,
        session: Session,
        *,
        provider_result: PaymentProviderResult,
    ) -> PaymentReconciliationRead | None:
        if not provider_result.verified:
            return None
        if provider_result.normalized_status not in self.NON_REFUNDABLE_STATUSES:
            return None

        payment = self.payment_repository.get_by_provider_external_id_for_update(
            session,
            provider=provider_result.provider,
            external_payment_id=provider_result.external_payment_id,
        )
        if payment is None:
            return None

        if not self._matches_expected_amount(payment.amount, provider_result.amount):
            return None
        if not self._matches_expected_currency(payment.currency, provider_result.currency):
            return None

        order = self.order_repository.get_for_update(session, order_id=payment.order_id)
        if order is None:
            return None

        if payment.status == PaymentStatus.PAID or order.payment_status == PaymentStatus.PAID:
            return PaymentReconciliationRead(
                payment=PaymentRead.model_validate(payment),
                order=OrderRead.model_validate(order),
                reconciliation_applied=False,
                payment_confirmed=True,
            )

        target_payment_status = provider_result.normalized_status
        payment_changed = payment.status != target_payment_status
        if payment_changed or provider_result.raw_payload is not None:
            payment = self.payment_repository.update(
                session,
                instance=payment,
                data={
                    "status": target_payment_status,
                    "raw_payload": self._merged_raw_payload(payment.raw_payload, provider_result),
                },
            )

        order_changed = False
        payment_confirmed = target_payment_status == PaymentStatus.PAID
        if payment_confirmed:
            order_updates: dict[str, object] = {}
            if order.payment_status != PaymentStatus.PAID:
                order_updates["payment_status"] = PaymentStatus.PAID
            if (
                order.booking_status == BookingStatus.RESERVED
                and order.cancellation_status == CancellationStatus.ACTIVE
            ):
                order_updates["booking_status"] = BookingStatus.CONFIRMED
            if order.reservation_expires_at is not None:
                order_updates["reservation_expires_at"] = None
            if order_updates:
                order = self.order_repository.update(session, instance=order, data=order_updates)
                order_changed = True
        elif payment_changed and order.payment_status == PaymentStatus.UNPAID:
            order = self.order_repository.update(
                session,
                instance=order,
                data={"payment_status": PaymentStatus.AWAITING_PAYMENT},
            )
            order_changed = True

        return PaymentReconciliationRead(
            payment=PaymentRead.model_validate(payment),
            order=OrderRead.model_validate(order),
            reconciliation_applied=payment_changed or order_changed,
            payment_confirmed=payment_confirmed,
        )

    @staticmethod
    def _matches_expected_amount(expected: Decimal, incoming: Decimal | None) -> bool:
        return incoming is None or incoming == expected

    @staticmethod
    def _matches_expected_currency(expected: str, incoming: str | None) -> bool:
        return incoming is None or incoming == expected

    @staticmethod
    def _merged_raw_payload(current_payload: dict | None, provider_result: PaymentProviderResult) -> dict:
        merged = dict(current_payload or {})
        merged["reconciliation"] = {
            "provider_status": provider_result.provider_status,
            "normalized_status": provider_result.normalized_status.value,
            "verified": provider_result.verified,
            "raw_payload": provider_result.raw_payload,
        }
        return merged
