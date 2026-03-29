from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content_item import ContentItem
from app.repositories.base import SQLAlchemyRepository


class ContentItemRepository(SQLAlchemyRepository[ContentItem]):
    def __init__(self) -> None:
        super().__init__(ContentItem)

    def list_by_tour(self, session: Session, *, tour_id: int) -> list[ContentItem]:
        stmt = (
            select(ContentItem)
            .where(ContentItem.tour_id == tour_id)
            .order_by(ContentItem.created_at.desc(), ContentItem.id.desc())
        )
        return list(session.scalars(stmt).all())

    def list_by_status(self, session: Session, *, status: str) -> list[ContentItem]:
        stmt = (
            select(ContentItem)
            .where(ContentItem.status == status)
            .order_by(ContentItem.created_at.desc(), ContentItem.id.desc())
        )
        return list(session.scalars(stmt).all())
