from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.user import UserRepository
from app.schemas.user import UserRead


class UserProfileService:
    def __init__(self, user_repository: UserRepository | None = None) -> None:
        self.user_repository = user_repository or UserRepository()

    def get_user(self, session: Session, *, user_id: int) -> UserRead | None:
        user = self.user_repository.get(session, user_id)
        if user is None:
            return None
        return UserRead.model_validate(user)

    def get_by_telegram_user_id(self, session: Session, *, telegram_user_id: int) -> UserRead | None:
        user = self.user_repository.get_by_telegram_user_id(session, telegram_user_id=telegram_user_id)
        if user is None:
            return None
        return UserRead.model_validate(user)

    def get_by_username(self, session: Session, *, username: str) -> UserRead | None:
        user = self.user_repository.get_by_username(session, username=username)
        if user is None:
            return None
        return UserRead.model_validate(user)
