from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.mini_app import MiniAppCatalogFiltersRead, MiniAppCatalogRead, MiniAppTourDetailRead
from app.services.mini_app_catalog import MiniAppCatalogService
from app.services.mini_app_tour_detail import MiniAppTourDetailService

router = APIRouter(prefix="/mini-app", tags=["mini-app"])


@router.get("/catalog", response_model=MiniAppCatalogRead)
def get_catalog(
    language_code: str | None = Query(default=None),
    destination_query: str | None = Query(default=None, max_length=200),
    departure_date_from: date | None = Query(default=None),
    departure_date_to: date | None = Query(default=None),
    max_price: Decimal | None = Query(default=None, ge=0),
    limit: int = Query(default=MiniAppCatalogService.DEFAULT_LIMIT, ge=1, le=MiniAppCatalogService.MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db),
) -> MiniAppCatalogRead:
    service = MiniAppCatalogService()
    filters = MiniAppCatalogFiltersRead(
        departure_date_from=departure_date_from,
        departure_date_to=departure_date_to,
        destination_query=destination_query,
        max_price=max_price,
    )
    try:
        return service.list_catalog(
            session,
            language_code=language_code,
            filters=filters,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tours/{tour_code}", response_model=MiniAppTourDetailRead)
def get_tour_detail(
    tour_code: str,
    language_code: str | None = Query(default=None),
    session: Session = Depends(get_db),
) -> MiniAppTourDetailRead:
    detail = MiniAppTourDetailService().get_tour_detail(
        session,
        code=tour_code,
        language_code=language_code,
    )
    if detail is None:
        raise HTTPException(status_code=404, detail="tour not found")
    return detail
