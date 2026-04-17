"""Persistence helpers for Layer C custom marketplace requests."""

from __future__ import annotations

from sqlalchemy import select, union
from sqlalchemy.orm import Session, selectinload

from app.models.custom_marketplace_request import CustomMarketplaceRequest, SupplierCustomRequestResponse
from app.models.enums import CustomMarketplaceRequestStatus, SupplierCustomRequestResponseKind
from app.models.supplier import Supplier


class CustomMarketplaceRequestRepository:
    def create(self, session: Session, *, row: CustomMarketplaceRequest) -> CustomMarketplaceRequest:
        session.add(row)
        session.flush()
        session.refresh(row)
        return row

    def get(self, session: Session, *, request_id: int) -> CustomMarketplaceRequest | None:
        return session.get(CustomMarketplaceRequest, request_id)

    def get_with_responses(self, session: Session, *, request_id: int) -> CustomMarketplaceRequest | None:
        stmt = (
            select(CustomMarketplaceRequest)
            .where(CustomMarketplaceRequest.id == request_id)
            .options(
                selectinload(CustomMarketplaceRequest.supplier_responses).selectinload(
                    SupplierCustomRequestResponse.supplier,
                ),
                selectinload(CustomMarketplaceRequest.selected_supplier_response),
                selectinload(CustomMarketplaceRequest.user),
            )
        )
        return session.scalars(stmt).first()

    def list_for_admin(
        self,
        session: Session,
        *,
        status: CustomMarketplaceRequestStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CustomMarketplaceRequest]:
        stmt = select(CustomMarketplaceRequest).order_by(
            CustomMarketplaceRequest.created_at.desc(),
            CustomMarketplaceRequest.id.desc(),
        )
        if status is not None:
            stmt = stmt.where(CustomMarketplaceRequest.status == status)
        stmt = stmt.offset(offset).limit(limit)
        return list(session.scalars(stmt).all())

    def list_open_for_suppliers(
        self,
        session: Session,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CustomMarketplaceRequest]:
        """Requests any supplier may see while the RFQ is still active (Track 5a)."""
        stmt = (
            select(CustomMarketplaceRequest)
            .where(
                CustomMarketplaceRequest.status.in_(
                    (
                        CustomMarketplaceRequestStatus.OPEN,
                        CustomMarketplaceRequestStatus.UNDER_REVIEW,
                    ),
                ),
            )
            .order_by(CustomMarketplaceRequest.created_at.desc(), CustomMarketplaceRequest.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def list_for_supplier_portal(
        self,
        session: Session,
        *,
        supplier_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CustomMarketplaceRequest]:
        open_ids = select(CustomMarketplaceRequest.id).where(
            CustomMarketplaceRequest.status.in_(
                (
                    CustomMarketplaceRequestStatus.OPEN,
                    CustomMarketplaceRequestStatus.UNDER_REVIEW,
                ),
            ),
        )
        won_ids = (
            select(CustomMarketplaceRequest.id)
            .join(
                SupplierCustomRequestResponse,
                CustomMarketplaceRequest.selected_supplier_response_id == SupplierCustomRequestResponse.id,
            )
            .where(
                SupplierCustomRequestResponse.supplier_id == supplier_id,
                CustomMarketplaceRequest.status.in_(
                    (
                        CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
                        CustomMarketplaceRequestStatus.CLOSED_ASSISTED,
                        CustomMarketplaceRequestStatus.CLOSED_EXTERNAL,
                    ),
                ),
            )
        )
        id_union = union(open_ids, won_ids).subquery()
        stmt = (
            select(CustomMarketplaceRequest)
            .where(CustomMarketplaceRequest.id.in_(select(id_union.c.id)))
            .order_by(CustomMarketplaceRequest.created_at.desc(), CustomMarketplaceRequest.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def get_for_supplier_view(
        self,
        session: Session,
        *,
        request_id: int,
        supplier_id: int,
    ) -> CustomMarketplaceRequest | None:
        req = session.get(CustomMarketplaceRequest, request_id)
        if req is None:
            return None
        if req.status == CustomMarketplaceRequestStatus.CANCELLED:
            return None
        if req.status in (
            CustomMarketplaceRequestStatus.OPEN,
            CustomMarketplaceRequestStatus.UNDER_REVIEW,
        ):
            stmt = (
                select(CustomMarketplaceRequest)
                .where(CustomMarketplaceRequest.id == request_id)
                .options(selectinload(CustomMarketplaceRequest.user))
            )
            return session.scalars(stmt).first()
        if req.selected_supplier_response_id is None:
            return None
        sel = session.get(SupplierCustomRequestResponse, req.selected_supplier_response_id)
        if sel is None or sel.supplier_id != supplier_id:
            return None
        stmt = (
            select(CustomMarketplaceRequest)
            .where(CustomMarketplaceRequest.id == request_id)
            .options(selectinload(CustomMarketplaceRequest.user))
        )
        return session.scalars(stmt).first()

    def list_for_customer_user(
        self,
        session: Session,
        *,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CustomMarketplaceRequest]:
        stmt = (
            select(CustomMarketplaceRequest)
            .where(CustomMarketplaceRequest.user_id == user_id)
            .order_by(CustomMarketplaceRequest.created_at.desc(), CustomMarketplaceRequest.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def get_for_customer_user(
        self,
        session: Session,
        *,
        request_id: int,
        user_id: int,
    ) -> CustomMarketplaceRequest | None:
        row = session.get(CustomMarketplaceRequest, request_id)
        if row is None or row.user_id != user_id:
            return None
        return row


class SupplierCustomRequestResponseRepository:
    def get_for_supplier(
        self,
        session: Session,
        *,
        request_id: int,
        supplier_id: int,
    ) -> SupplierCustomRequestResponse | None:
        stmt = select(SupplierCustomRequestResponse).where(
            SupplierCustomRequestResponse.request_id == request_id,
            SupplierCustomRequestResponse.supplier_id == supplier_id,
        )
        return session.scalars(stmt).first()

    def upsert(
        self,
        session: Session,
        *,
        request_id: int,
        supplier_id: int,
        response_kind: SupplierCustomRequestResponseKind,
        supplier_message: str | None,
        quoted_price,
        quoted_currency: str | None,
    ) -> SupplierCustomRequestResponse:
        row = self.get_for_supplier(session, request_id=request_id, supplier_id=supplier_id)
        if row is None:
            row = SupplierCustomRequestResponse(
                request_id=request_id,
                supplier_id=supplier_id,
                response_kind=response_kind,
                supplier_message=supplier_message,
                quoted_price=quoted_price,
                quoted_currency=quoted_currency,
            )
            session.add(row)
        else:
            row.response_kind = response_kind
            row.supplier_message = supplier_message
            row.quoted_price = quoted_price
            row.quoted_currency = quoted_currency
        session.flush()
        session.refresh(row)
        return row
