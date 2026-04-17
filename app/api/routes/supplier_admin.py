"""Supplier-admin API (Layer B): own offers only."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.supplier_admin_auth import SupplierAuth
from app.db.session import get_db
from app.schemas.custom_marketplace import (
    CustomMarketplaceRequestDetailRead,
    CustomMarketplaceRequestListRead,
    SupplierCustomRequestResponseRead,
    SupplierCustomRequestResponseUpsert,
)
from app.schemas.supplier_admin import (
    SupplierOfferCreate,
    SupplierOfferListRead,
    SupplierOfferRead,
    SupplierOfferUpdate,
)
from app.services.custom_marketplace_request_service import (
    CustomMarketplaceRequestNotFoundError,
    CustomMarketplaceRequestNotOpenError,
    CustomMarketplaceRequestService,
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


@router.get("/custom-requests", response_model=CustomMarketplaceRequestListRead)
def list_supplier_custom_requests(
    supplier: SupplierAuth,
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> CustomMarketplaceRequestListRead:
    svc = CustomMarketplaceRequestService()
    items = svc.list_open_for_supplier(db, supplier_id=supplier.id, limit=limit, offset=offset)
    return CustomMarketplaceRequestListRead(items=items, total_returned=len(items))


@router.get("/custom-requests/{request_id}", response_model=CustomMarketplaceRequestDetailRead)
def get_supplier_custom_request(
    request_id: int,
    supplier: SupplierAuth,
    db: Session = Depends(get_db),
) -> CustomMarketplaceRequestDetailRead:
    try:
        return CustomMarketplaceRequestService().get_open_for_supplier(
            db,
            request_id=request_id,
            supplier_id=supplier.id,
        )
    except CustomMarketplaceRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.") from None


@router.put(
    "/custom-requests/{request_id}/response",
    response_model=SupplierCustomRequestResponseRead,
)
def put_supplier_custom_request_response(
    request_id: int,
    supplier: SupplierAuth,
    db: Session = Depends(get_db),
    payload: SupplierCustomRequestResponseUpsert = Body(...),
) -> SupplierCustomRequestResponseRead:
    try:
        row = CustomMarketplaceRequestService().upsert_supplier_response(
            db,
            request_id=request_id,
            supplier_id=supplier.id,
            payload=payload,
        )
    except CustomMarketplaceRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.") from None
    except CustomMarketplaceRequestNotOpenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from None
    db.commit()
    return row
