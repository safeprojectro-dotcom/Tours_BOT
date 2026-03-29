from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.orm import Session

from app.models.enums import TourStatus
from app.schemas.prepared import CatalogBrowseFiltersRead, CatalogTourCardRead
from app.services.catalog import CatalogLookupService
from app.services.language_aware_tour import LanguageAwareTourReadService


class CatalogPreparationService:
    def __init__(
        self,
        catalog_lookup_service: CatalogLookupService | None = None,
        language_aware_tour_service: LanguageAwareTourReadService | None = None,
    ) -> None:
        self.catalog_lookup_service = catalog_lookup_service or CatalogLookupService()
        self.language_aware_tour_service = language_aware_tour_service or LanguageAwareTourReadService()

    def list_catalog_cards(
        self,
        session: Session,
        *,
        language_code: str | None = None,
        status: TourStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CatalogTourCardRead]:
        tours = self.catalog_lookup_service.list_tours(
            session,
            status=status,
            limit=limit,
            offset=offset,
        )
        cards: list[CatalogTourCardRead] = []

        for tour in tours:
            prepared_detail = self.language_aware_tour_service.get_localized_tour_detail(
                session,
                tour_id=tour.id,
                language_code=language_code,
            )
            if prepared_detail is None:
                continue

            localized_content = prepared_detail.localized_content
            cards.append(
                CatalogTourCardRead(
                    id=tour.id,
                    code=tour.code,
                    title=localized_content.title,
                    short_description=localized_content.short_description,
                    departure_datetime=tour.departure_datetime,
                    return_datetime=tour.return_datetime,
                    duration_days=tour.duration_days,
                    base_price=tour.base_price,
                    currency=tour.currency,
                    seats_total=tour.seats_total,
                    seats_available=tour.seats_available,
                    status=tour.status,
                    guaranteed_flag=tour.guaranteed_flag,
                    is_available=tour.seats_available > 0,
                    localized_content=localized_content,
                )
            )

        return cards

    def list_catalog_cards_filtered(
        self,
        session: Session,
        *,
        filters: CatalogBrowseFiltersRead | None = None,
        language_code: str | None = None,
        status: TourStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CatalogTourCardRead]:
        cards = self.list_catalog_cards(
            session,
            language_code=language_code,
            status=status,
            limit=max(limit + offset, 100),
            offset=0,
        )
        filtered_cards = self.apply_catalog_filters(cards, filters=filters)
        return filtered_cards[offset : offset + limit]

    def apply_catalog_filters(
        self,
        cards: Iterable[CatalogTourCardRead],
        *,
        filters: CatalogBrowseFiltersRead | None = None,
    ) -> list[CatalogTourCardRead]:
        if filters is None:
            return list(cards)

        destination_query = self._normalize_query(filters.destination_query)
        filtered: list[CatalogTourCardRead] = []

        for card in cards:
            if filters.departure_from is not None and card.departure_datetime < filters.departure_from:
                continue
            if filters.departure_to is not None and card.departure_datetime > filters.departure_to:
                continue
            if filters.max_price is not None and card.base_price > filters.max_price:
                continue
            if destination_query is not None and destination_query not in self._build_destination_haystack(card):
                continue
            filtered.append(card)

        return filtered

    @staticmethod
    def _normalize_query(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.casefold().split())
        return normalized or None

    def _build_destination_haystack(self, card: CatalogTourCardRead) -> str:
        fields = [
            card.code,
            card.title,
            card.short_description,
            card.localized_content.title,
            card.localized_content.short_description,
        ]
        return " ".join(
            normalized for normalized in (self._normalize_query(field) for field in fields) if normalized is not None
        )
