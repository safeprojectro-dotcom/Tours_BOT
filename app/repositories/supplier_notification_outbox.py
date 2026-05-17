from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.supplier_notification_outbox import SupplierNotificationOutbox
from app.repositories.base import SQLAlchemyRepository


class SupplierNotificationOutboxRepository(SQLAlchemyRepository[SupplierNotificationOutbox]):
    def __init__(self) -> None:
        super().__init__(SupplierNotificationOutbox)

    def get_by_idempotency_key(self, session: Session, *, idempotency_key: str) -> SupplierNotificationOutbox | None:
        stmt = select(SupplierNotificationOutbox).where(SupplierNotificationOutbox.idempotency_key == idempotency_key)
        return session.scalar(stmt)

    def try_claim_pending_for_delivery(self, session: Session, *, outbox_id: int) -> bool:
        stmt = (
            update(SupplierNotificationOutbox)
            .where(
                SupplierNotificationOutbox.id == outbox_id,
                SupplierNotificationOutbox.dispatch_status == "pending_dispatch",
            )
            .values(dispatch_status="delivery_in_progress", updated_at=func.now())
        )
        return session.execute(stmt).rowcount == 1

    def finalize_delivered_from_in_progress(
        self,
        session: Session,
        *,
        outbox_id: int,
        telegram_message_id: str,
    ) -> bool:
        trimmed = telegram_message_id[:64]
        stmt = (
            update(SupplierNotificationOutbox)
            .where(
                SupplierNotificationOutbox.id == outbox_id,
                SupplierNotificationOutbox.dispatch_status == "delivery_in_progress",
            )
            .values(
                dispatch_status="delivered",
                telegram_message_id=trimmed,
                last_delivery_error=None,
                delivered_at=func.now(),
                updated_at=func.now(),
            )
        )
        return session.execute(stmt).rowcount == 1

    def finalize_send_failed_from_in_progress(
        self,
        session: Session,
        *,
        outbox_id: int,
        error_message: str,
    ) -> bool:
        truncated = error_message[:10_000] if len(error_message) > 10_000 else error_message
        stmt = (
            update(SupplierNotificationOutbox)
            .where(
                SupplierNotificationOutbox.id == outbox_id,
                SupplierNotificationOutbox.dispatch_status == "delivery_in_progress",
            )
            .values(
                dispatch_status="send_failed",
                last_delivery_error=truncated,
                updated_at=func.now(),
            )
        )
        return session.execute(stmt).rowcount == 1
