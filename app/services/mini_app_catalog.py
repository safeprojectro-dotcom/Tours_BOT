from __future__ import annotations

from datetime import UTC, date, datetime, time

from sqlalchemy.orm import Session

from app.models.enums import TourStatus
from app.schemas.mini_app import MiniAppCatalogFiltersRead, MiniAppCatalogRead
from app.schemas.prepared import CatalogBrowseFiltersRead
from app.services.catalog_preparation import CatalogPreparationService


class MiniAppCatalogService:
    DEFAULT_LIMIT = 24
    MAX_LIMIT = 100
    STATUS_SCOPE: tuple[TourStatus, ...] = (TourStatus.OPEN_FOR_SALE,)

    def __init__(
        self,
        catalog_preparation_service: CatalogPreparationService | None = None,
    ) -> None:
        self.catalog_preparation_service = catalog_preparation_service or CatalogPreparationService()

    def list_catalog(
        self,
        session: Session,
        *,
        language_code: str | None = None,
        filters: MiniAppCatalogFiltersRead | None = None,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> MiniAppCatalogRead:
        applied_filters = filters or MiniAppCatalogFiltersRead()
        prepared_filters = self._build_catalog_filters(applied_filters)
        cards = self.catalog_preparation_service.list_catalog_cards_filtered(
            session,
            filters=prepared_filters,
            language_code=language_code,
            status=TourStatus.OPEN_FOR_SALE,
            limit=self._sanitize_limit(limit),
            offset=max(offset, 0),
        )
        return MiniAppCatalogRead(
            items=cards,
            applied_filters=applied_filters,
            limit=self._sanitize_limit(limit),
            offset=max(offset, 0),
            status_scope=list(self.STATUS_SCOPE),
        )

    def _build_catalog_filters(
        self,
        filters: MiniAppCatalogFiltersRead,
    ) -> CatalogBrowseFiltersRead:
        if (
            filters.departure_date_from is not None
            and filters.departure_date_to is not None
            and filters.departure_date_from > filters.departure_date_to
        ):
            raise ValueError("departure date range is invalid")

        destination_query = self._normalize_query(filters.destination_query)
        return CatalogBrowseFiltersRead(
            departure_from=self._start_of_day(filters.departure_date_from),
            departure_to=self._end_of_day(filters.departure_date_to),
            destination_query=destination_query,
            max_price=filters.max_price,
        )

    @staticmethod
    def _sanitize_limit(limit: int) -> int:
        return max(1, min(limit, MiniAppCatalogService.MAX_LIMIT))

    @staticmethod
    def _normalize_query(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        return normalized or None

    @staticmethod
    def _start_of_day(value: date | None) -> datetime | None:
        if value is None:
            return None
        return datetime.combine(value, time.min, tzinfo=UTC)

    @staticmethod
    def _end_of_day(value: date | None) -> datetime | None:
        if value is None:
            return None
        return datetime.combine(value, time.max, tzinfo=UTC)
