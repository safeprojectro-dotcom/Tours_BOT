from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import Message
from app.repositories.base import SQLAlchemyRepository


class MessageRepository(SQLAlchemyRepository[Message]):
    def __init__(self) -> None:
        super().__init__(Message)

    def list_by_user(self, session: Session, *, user_id: int, limit: int = 100, offset: int = 0) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.user_id == user_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def list_by_chat(
        self,
        session: Session,
        *,
        telegram_chat_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.telegram_chat_id == telegram_chat_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())
