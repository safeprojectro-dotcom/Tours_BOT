"""Admin API: read surfaces + narrow writes (protected by ADMIN_API_TOKEN)."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.admin_auth import require_admin_api_token
from app.db.session import get_db
from app.models.enums import TourStatus
from app.schemas.admin import (
    AdminOrderDetailRead,
    AdminOrderListRead,
    AdminOverviewRead,
    AdminTourCreate,
    AdminTourDetailRead,
    AdminTourListRead,
)
from app.services.admin_order_lifecycle import AdminOrderLifecycleKind
from app.services.admin_read import AdminReadService
from app.services.admin_tour_write import (
    AdminTourCreateValidationError,
    AdminTourDuplicateCodeError,
    AdminTourWriteService,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_api_token)],
)


@router.get("/overview", response_model=AdminOverviewRead)
def get_admin_overview(
    db: Session = Depends(get_db),
) -> AdminOverviewRead:
    return AdminReadService().overview(db)


@router.post("/tours", response_model=AdminTourDetailRead, status_code=status.HTTP_201_CREATED)
def create_admin_tour(
    db: Session = Depends(get_db),
    payload: AdminTourCreate = Body(...),
) -> AdminTourDetailRead:
    try:
        detail = AdminTourWriteService().create_tour(db, payload=payload)
    except AdminTourDuplicateCodeError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tour code already exists.",
        ) from None
    except AdminTourCreateValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return detail


@router.get("/tours", response_model=AdminTourListRead)
def list_admin_tours(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0, le=100_000),
    status: TourStatus | None = Query(default=None),
    guaranteed_only: bool = Query(default=False),
) -> AdminTourListRead:
    return AdminReadService().list_tours(
        db,
        limit=limit,
        offset=offset,
        status=status,
        guaranteed_only=guaranteed_only,
    )


@router.get("/tours/{tour_id}", response_model=AdminTourDetailRead)
def get_admin_tour_detail(
    tour_id: int,
    db: Session = Depends(get_db),
) -> AdminTourDetailRead:
    detail = AdminReadService().get_tour_detail(db, tour_id=tour_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tour not found.")
    return detail


@router.get("/orders", response_model=AdminOrderListRead)
def list_admin_orders(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0, le=100_000),
    lifecycle_kind: AdminOrderLifecycleKind | None = Query(default=None),
    tour_id: int | None = Query(default=None, ge=1),
) -> AdminOrderListRead:
    return AdminReadService().list_orders(
        db,
        limit=limit,
        offset=offset,
        lifecycle_kind=lifecycle_kind,
        tour_id=tour_id,
    )


@router.get("/orders/{order_id}", response_model=AdminOrderDetailRead)
def get_admin_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
) -> AdminOrderDetailRead:
    detail = AdminReadService().get_order_detail(db, order_id=order_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    return detail
