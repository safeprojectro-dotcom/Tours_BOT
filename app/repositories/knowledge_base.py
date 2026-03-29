from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBaseEntry
from app.repositories.base import SQLAlchemyRepository


class KnowledgeBaseRepository(SQLAlchemyRepository[KnowledgeBaseEntry]):
    def __init__(self) -> None:
        super().__init__(KnowledgeBaseEntry)

    def list_active(self, session: Session, *, language_code: str | None = None) -> list[KnowledgeBaseEntry]:
        stmt = select(KnowledgeBaseEntry).where(KnowledgeBaseEntry.is_active.is_(True))
        if language_code is not None:
            stmt = stmt.where(KnowledgeBaseEntry.language_code == language_code)
        stmt = stmt.order_by(KnowledgeBaseEntry.category, KnowledgeBaseEntry.id)
        return list(session.scalars(stmt).all())

    def list_by_category(
        self,
        session: Session,
        *,
        category: str,
        language_code: str | None = None,
    ) -> list[KnowledgeBaseEntry]:
        stmt = select(KnowledgeBaseEntry).where(KnowledgeBaseEntry.category == category)
        if language_code is not None:
            stmt = stmt.where(KnowledgeBaseEntry.language_code == language_code)
        stmt = stmt.order_by(KnowledgeBaseEntry.id)
        return list(session.scalars(stmt).all())
