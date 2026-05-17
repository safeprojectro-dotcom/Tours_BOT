from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.supplier_notification_outbox import SupplierNotificationOutbox
from app.repositories.base import SQLAlchemyRepository


class SupplierNotificationOutboxRepository(SQLAlchemyRepository[SupplierNotificationOutbox]):
    def __init__(self) -> None:
        super().__init__(SupplierNotificationOutbox)

    def get_by_idempotency_key(self, session: Session, *, idempotency_key: str) -> SupplierNotificationOutbox | None:
        stmt = select(SupplierNotificationOutbox).where(SupplierNotificationOutbox.idempotency_key == idempotency_key)
        return session.scalar(stmt)
