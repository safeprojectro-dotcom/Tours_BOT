from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.payment import PaymentRepository
from app.schemas.payment import PaymentRead


class PaymentReadService:
    def __init__(self, payment_repository: PaymentRepository | None = None) -> None:
        self.payment_repository = payment_repository or PaymentRepository()

    def get_payment(self, session: Session, *, payment_id: int) -> PaymentRead | None:
        payment = self.payment_repository.get(session, payment_id)
        if payment is None:
            return None
        return PaymentRead.model_validate(payment)

    def list_by_order(self, session: Session, *, order_id: int) -> list[PaymentRead]:
        payments = self.payment_repository.list_by_order(session, order_id=order_id)
        return [PaymentRead.model_validate(payment) for payment in payments]

    def get_by_provider_external_id(
        self,
        session: Session,
        *,
        provider: str,
        external_payment_id: str,
    ) -> PaymentRead | None:
        payment = self.payment_repository.get_by_provider_external_id(
            session,
            provider=provider,
            external_payment_id=external_payment_id,
        )
        if payment is None:
            return None
        return PaymentRead.model_validate(payment)
