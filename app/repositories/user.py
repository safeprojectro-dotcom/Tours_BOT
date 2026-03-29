from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import SQLAlchemyRepository


class UserRepository(SQLAlchemyRepository[User]):
    def __init__(self) -> None:
        super().__init__(User)

    def get_by_telegram_user_id(self, session: Session, *, telegram_user_id: int) -> User | None:
        stmt = select(User).where(User.telegram_user_id == telegram_user_id)
        return session.scalar(stmt)

    def get_by_username(self, session: Session, *, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return session.scalar(stmt)
