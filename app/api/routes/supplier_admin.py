"""Supplier-admin API (Layer B): own offers only."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.supplier_admin_auth import SupplierAuth
from app.db.session import get_db
from app.schemas.supplier_admin import (
    SupplierOfferCreate,
    SupplierOfferListRead,
    SupplierOfferRead,
    SupplierOfferUpdate,
)
from app.services.supplier_offer_service import (
    SupplierOfferImmutableError,
    SupplierOfferLifecycleNotAllowedError,
    SupplierOfferNotFoundError,
    SupplierOfferReadinessError,
    SupplierOfferService,
)

router = APIRouter(prefix="/supplier-admin", tags=["supplier-admin"])


@router.get("/offers", response_model=SupplierOfferListRead)
def list_supplier_offers(
    supplier: SupplierAuth,
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> SupplierOfferListRead:
    svc = SupplierOfferService()
    items = svc.list_offers(db, supplier_id=supplier.id, limit=limit, offset=offset)
    return SupplierOfferListRead(items=items, total_returned=len(items))


@router.get("/offers/{offer_id}", response_model=SupplierOfferRead)
def get_supplier_offer(
    offer_id: int,
    supplier: SupplierAuth,
    db: Session = Depends(get_db),
) -> SupplierOfferRead:
    try:
        return SupplierOfferService().get_offer(db, supplier_id=supplier.id, offer_id=offer_id)
    except SupplierOfferNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.") from None


@router.post("/offers", response_model=SupplierOfferRead, status_code=status.HTTP_201_CREATED)
def create_supplier_offer(
    supplier: SupplierAuth,
    db: Session = Depends(get_db),
    payload: SupplierOfferCreate = Body(...),
) -> SupplierOfferRead:
    try:
        row = SupplierOfferService().create_offer(db, supplier_id=supplier.id, payload=payload)
    except SupplierOfferReadinessError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return row


@router.put("/offers/{offer_id}", response_model=SupplierOfferRead)
def update_supplier_offer(
    offer_id: int,
    supplier: SupplierAuth,
    db: Session = Depends(get_db),
    payload: SupplierOfferUpdate = Body(...),
) -> SupplierOfferRead:
    try:
        row = SupplierOfferService().update_offer(
            db,
            supplier_id=supplier.id,
            offer_id=offer_id,
            payload=payload,
        )
    except SupplierOfferNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.") from None
    except SupplierOfferReadinessError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    except SupplierOfferImmutableError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    except SupplierOfferLifecycleNotAllowedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return row
