from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.schemas.knowledge_base import KnowledgeBaseEntryRead


class KnowledgeBaseLookupService:
    def __init__(self, knowledge_base_repository: KnowledgeBaseRepository | None = None) -> None:
        self.knowledge_base_repository = knowledge_base_repository or KnowledgeBaseRepository()

    def list_active(
        self,
        session: Session,
        *,
        language_code: str | None = None,
    ) -> list[KnowledgeBaseEntryRead]:
        entries = self.knowledge_base_repository.list_active(session, language_code=language_code)
        return [KnowledgeBaseEntryRead.model_validate(entry) for entry in entries]

    def list_by_category(
        self,
        session: Session,
        *,
        category: str,
        language_code: str | None = None,
    ) -> list[KnowledgeBaseEntryRead]:
        entries = self.knowledge_base_repository.list_by_category(
            session,
            category=category,
            language_code=language_code,
        )
        return [KnowledgeBaseEntryRead.model_validate(entry) for entry in entries]
