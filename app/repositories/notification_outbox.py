from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification_outbox import NotificationOutbox
from app.repositories.base import SQLAlchemyRepository


class NotificationOutboxRepository(SQLAlchemyRepository[NotificationOutbox]):
    def __init__(self) -> None:
        super().__init__(NotificationOutbox)

    def get_by_dispatch_key(self, session: Session, *, dispatch_key: str) -> NotificationOutbox | None:
        stmt = select(NotificationOutbox).where(NotificationOutbox.dispatch_key == dispatch_key)
        return session.scalar(stmt)

    def list_by_status(
        self,
        session: Session,
        *,
        status: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[NotificationOutbox]:
        stmt = (
            select(NotificationOutbox)
            .where(NotificationOutbox.status == status)
            .order_by(NotificationOutbox.created_at, NotificationOutbox.id)
            .offset(offset)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def get_for_update(self, session: Session, *, outbox_id: int) -> NotificationOutbox | None:
        stmt = select(NotificationOutbox).where(NotificationOutbox.id == outbox_id).with_for_update()
        return session.scalar(stmt)

    def list_pending_ids_for_pickup(self, session: Session, *, limit: int = 100) -> list[int]:
        stmt = (
            select(NotificationOutbox.id)
            .where(NotificationOutbox.status == "pending")
            .order_by(NotificationOutbox.created_at, NotificationOutbox.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(session.scalars(stmt).all())
