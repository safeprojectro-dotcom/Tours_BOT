from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import SupplierOfferLifecycle
from app.models.supplier import Supplier, SupplierApiCredential, SupplierOffer
from app.repositories.base import SQLAlchemyRepository


class SupplierRepository(SQLAlchemyRepository[Supplier]):
    def __init__(self) -> None:
        super().__init__(Supplier)

    def find_by_code(self, session: Session, *, code: str) -> Supplier | None:
        stmt = select(Supplier).where(Supplier.code == code).limit(1)
        return session.scalars(stmt).first()

    def find_by_primary_telegram_user_id(self, session: Session, *, telegram_user_id: int) -> Supplier | None:
        stmt = select(Supplier).where(Supplier.primary_telegram_user_id == telegram_user_id).limit(1)
        return session.scalars(stmt).first()


class SupplierApiCredentialRepository:
    def find_active_by_token_hash(
        self,
        session: Session,
        *,
        token_hash: str,
    ) -> SupplierApiCredential | None:
        stmt = (
            select(SupplierApiCredential)
            .join(Supplier, Supplier.id == SupplierApiCredential.supplier_id)
            .options(joinedload(SupplierApiCredential.supplier))
            .where(
                SupplierApiCredential.token_hash == token_hash,
                SupplierApiCredential.revoked_at.is_(None),
                Supplier.is_active.is_(True),
            )
            .limit(1)
        )
        return session.scalars(stmt).first()


class SupplierOfferRepository(SQLAlchemyRepository[SupplierOffer]):
    def __init__(self) -> None:
        super().__init__(SupplierOffer)

    def _scoped(self, supplier_id: int) -> Select[tuple[SupplierOffer]]:
        return select(SupplierOffer).where(SupplierOffer.supplier_id == supplier_id).order_by(
            SupplierOffer.created_at.desc(),
            SupplierOffer.id.desc(),
        )

    def list_for_supplier(
        self,
        session: Session,
        *,
        supplier_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SupplierOffer]:
        stmt = self._scoped(supplier_id).offset(offset).limit(limit)
        return list(session.scalars(stmt).all())

    def get_for_supplier(
        self,
        session: Session,
        *,
        supplier_id: int,
        offer_id: int,
    ) -> SupplierOffer | None:
        stmt = self._scoped(supplier_id).where(SupplierOffer.id == offer_id).limit(1)
        return session.scalars(stmt).first()

    def get_any(self, session: Session, *, offer_id: int) -> SupplierOffer | None:
        return session.get(SupplierOffer, offer_id)

    def list_for_admin(
        self,
        session: Session,
        *,
        lifecycle_status: SupplierOfferLifecycle | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SupplierOffer]:
        stmt = select(SupplierOffer).order_by(SupplierOffer.updated_at.desc(), SupplierOffer.id.desc())
        if lifecycle_status is not None:
            stmt = stmt.where(SupplierOffer.lifecycle_status == lifecycle_status)
        stmt = stmt.offset(offset).limit(limit)
        return list(session.scalars(stmt).all())
