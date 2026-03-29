from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.repositories.base import SQLAlchemyRepository


class PaymentRepository(SQLAlchemyRepository[Payment]):
    def __init__(self) -> None:
        super().__init__(Payment)

    def get_latest_by_order(self, session: Session, *, order_id: int) -> Payment | None:
        stmt = (
            select(Payment)
            .where(Payment.order_id == order_id)
            .order_by(Payment.created_at.desc(), Payment.id.desc())
            .limit(1)
        )
        return session.scalar(stmt)

    def list_by_order(self, session: Session, *, order_id: int) -> list[Payment]:
        stmt = (
            select(Payment)
            .where(Payment.order_id == order_id)
            .order_by(Payment.created_at.desc(), Payment.id.desc())
        )
        return list(session.scalars(stmt).all())

    def get_by_provider_external_id(
        self,
        session: Session,
        *,
        provider: str,
        external_payment_id: str,
    ) -> Payment | None:
        stmt = select(Payment).where(
            Payment.provider == provider,
            Payment.external_payment_id == external_payment_id,
        )
        return session.scalar(stmt)

    def get_by_provider_external_id_for_update(
        self,
        session: Session,
        *,
        provider: str,
        external_payment_id: str,
    ) -> Payment | None:
        stmt = (
            select(Payment)
            .where(
                Payment.provider == provider,
                Payment.external_payment_id == external_payment_id,
            )
            .with_for_update()
        )
        return session.scalar(stmt)
