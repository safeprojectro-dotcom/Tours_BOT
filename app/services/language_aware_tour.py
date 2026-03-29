from __future__ import annotations

from app.schemas.prepared import LocalizedTourContentRead, PreparedTourDetailRead
from app.schemas.tour import TourDetailRead
from app.services.tour_detail import TourDetailService
from sqlalchemy.orm import Session


class LanguageAwareTourReadService:
    def __init__(self, tour_detail_service: TourDetailService | None = None) -> None:
        self.tour_detail_service = tour_detail_service or TourDetailService()

    def get_localized_tour_detail(
        self,
        session: Session,
        *,
        tour_id: int,
        language_code: str | None = None,
    ) -> PreparedTourDetailRead | None:
        detail = self.tour_detail_service.get_tour_detail(session, tour_id=tour_id)
        if detail is None:
            return None

        localized_content = self.build_localized_content(detail, language_code=language_code)
        return PreparedTourDetailRead(
            tour=detail.tour,
            localized_content=localized_content,
            boarding_points=detail.boarding_points,
        )

    def build_localized_content(
        self,
        detail: TourDetailRead,
        *,
        language_code: str | None = None,
    ) -> LocalizedTourContentRead:
        translation = None
        if language_code is not None:
            translation = next(
                (item for item in detail.translations if item.language_code == language_code),
                None,
            )

        used_fallback = language_code is not None and translation is None

        return LocalizedTourContentRead(
            requested_language=language_code,
            resolved_language=translation.language_code if translation is not None else None,
            used_fallback=used_fallback,
            title=translation.title if translation is not None else detail.tour.title_default,
            short_description=(
                translation.short_description
                if translation is not None and translation.short_description is not None
                else detail.tour.short_description_default
            ),
            full_description=(
                translation.full_description
                if translation is not None and translation.full_description is not None
                else detail.tour.full_description_default
            ),
            program_text=translation.program_text if translation is not None else None,
            included_text=translation.included_text if translation is not None else None,
            excluded_text=translation.excluded_text if translation is not None else None,
        )
