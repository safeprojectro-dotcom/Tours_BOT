"""Y44: read-only admin API for supplier execution request/attempt rows (Y43)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.admin_auth import require_admin_api_token
from app.db.session import get_db
from app.models.enums import SupplierExecutionRequestStatus, SupplierExecutionSourceEntityType
from app.schemas.admin_supplier_execution import (
    AdminSupplierExecutionRequestDetailRead,
    AdminSupplierExecutionRequestListRead,
)
from app.services.admin_supplier_execution_read import AdminSupplierExecutionReadService

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_api_token)],
)


@router.get("/supplier-execution-requests", response_model=AdminSupplierExecutionRequestListRead)
def list_supplier_execution_requests(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0, le=100_000),
    status: SupplierExecutionRequestStatus | None = Query(default=None),
    source_entity_type: SupplierExecutionSourceEntityType | None = Query(default=None),
) -> AdminSupplierExecutionRequestListRead:
    return AdminSupplierExecutionReadService().list_requests(
        db,
        limit=limit,
        offset=offset,
        status=status,
        source_entity_type=source_entity_type,
    )


@router.get("/supplier-execution-requests/{request_id}", response_model=AdminSupplierExecutionRequestDetailRead)
def get_supplier_execution_request(
    request_id: int,
    db: Session = Depends(get_db),
) -> AdminSupplierExecutionRequestDetailRead:
    detail = AdminSupplierExecutionReadService().get_request_detail(db, request_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier execution request not found.")
    return detail
