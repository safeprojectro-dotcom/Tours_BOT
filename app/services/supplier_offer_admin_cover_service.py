"""C2B7.1: central-admin mutation of showcase hero reference only — no publish, no media_review changes."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.supplier import SupplierOfferRepository
from app.schemas.supplier_admin import AdminSupplierOfferRead


class SupplierOfferAdminCoverNotFoundError(Exception):
    pass


class SupplierOfferAdminCoverService:
    def __init__(self) -> None:
        self._repo = SupplierOfferRepository()

    def put_cover_media_reference(
        self,
        session: Session,
        *,
        offer_id: int,
        cover_media_reference: str | None,
    ) -> AdminSupplierOfferRead:
        row = self._repo.get_any(session, offer_id=offer_id)
        if row is None:
            raise SupplierOfferAdminCoverNotFoundError
        row.cover_media_reference = cover_media_reference
        session.flush()
        session.refresh(row)
        return AdminSupplierOfferRead.model_validate(row, from_attributes=True)
