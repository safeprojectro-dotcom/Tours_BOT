from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

from app.bot.constants import (
    BUDGET_OPTION_ANY,
    DATE_OPTION_ANY,
    DATE_OPTION_NEXT_30_DAYS,
    DATE_OPTION_WEEKEND,
    DEFAULT_PRIVATE_CATALOG_LIMIT,
    MAX_PRIVATE_PREPARATION_SEATS,
    PRIVATE_SOURCE_CHANNEL,
    START_TOUR_PREFIX,
)
from app.models.enums import TourStatus
from app.repositories.user import UserRepository
from app.schemas.prepared import (
    CatalogBrowseFiltersRead,
    CatalogTourCardRead,
    PreparedTourDetailRead,
    ReservationPreparationSummaryRead,
    ReservationPreparationTourRead,
)
from app.schemas.user import UserRead
from app.services.catalog import CatalogLookupService
from app.services.catalog_preparation import CatalogPreparationService
from app.services.customer_catalog_visibility import tour_is_customer_catalog_visible
from app.services.language_aware_tour import LanguageAwareTourReadService
from app.services.reservation_expiry import lazy_expire_due_reservations
from app.services.tour_sales_mode_policy import TourSalesModePolicyService
from sqlalchemy.orm import Session


class TelegramUserContextService:
    def __init__(
        self,
        *,
        user_repository: UserRepository | None = None,
        supported_language_codes: tuple[str, ...] = ("en",),
    ) -> None:
        self.user_repository = user_repository or UserRepository()
        self.supported_language_codes = supported_language_codes

    def sync_private_user(
        self,
        session: Session,
        *,
        telegram_user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        telegram_language_code: str | None = None,
    ) -> UserRead:
        user = self.user_repository.get_by_telegram_user_id(session, telegram_user_id=telegram_user_id)
        preferred_language = self.resolve_language(
            session,
            telegram_user_id=telegram_user_id,
            telegram_language_code=telegram_language_code,
        )
        payload = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "source_channel": PRIVATE_SOURCE_CHANNEL,
        }
        if preferred_language is not None:
            payload["preferred_language"] = preferred_language

        if user is None:
            created = self.user_repository.create(
                session,
                data={
                    "telegram_user_id": telegram_user_id,
                    **payload,
                },
            )
            return UserRead.model_validate(created)

        updated = self.user_repository.update(session, instance=user, data=payload)
        return UserRead.model_validate(updated)

    def resolve_language(
        self,
        session: Session,
        *,
        telegram_user_id: int,
        telegram_language_code: str | None = None,
    ) -> str | None:
        user = self.user_repository.get_by_telegram_user_id(session, telegram_user_id=telegram_user_id)
        if user is not None:
            stored_language = self.normalize_language_code(user.preferred_language)
            if stored_language is not None:
                return stored_language
        return self.normalize_language_code(telegram_language_code)

    def set_preferred_language(
        self,
        session: Session,
        *,
        telegram_user_id: int,
        language_code: str,
    ) -> UserRead | None:
        normalized = self.normalize_language_code(language_code)
        if normalized is None:
            return None

        user = self.user_repository.get_by_telegram_user_id(session, telegram_user_id=telegram_user_id)
        if user is None:
            return None

        updated = self.user_repository.update(
            session,
            instance=user,
            data={"preferred_language": normalized, "source_channel": PRIVATE_SOURCE_CHANNEL},
        )
        return UserRead.model_validate(updated)

    def normalize_language_code(self, language_code: str | None) -> str | None:
        if not language_code:
            return None

        normalized = language_code.strip().lower().replace("_", "-")
        short_code = normalized.split("-", maxsplit=1)[0]
        if short_code in self.supported_language_codes:
            return short_code
        return None


class PrivateTourBrowseService:
    BUDGET_PRESETS: tuple[Decimal, ...] = (
        Decimal("100"),
        Decimal("150"),
        Decimal("200"),
    )

    def __init__(
        self,
        *,
        catalog_lookup_service: CatalogLookupService | None = None,
        catalog_preparation_service: CatalogPreparationService | None = None,
        language_aware_tour_service: LanguageAwareTourReadService | None = None,
    ) -> None:
        self.catalog_lookup_service = catalog_lookup_service or CatalogLookupService()
        self.catalog_preparation_service = catalog_preparation_service or CatalogPreparationService()
        self.language_aware_tour_service = language_aware_tour_service or LanguageAwareTourReadService()

    def list_entry_tours(
        self,
        session: Session,
        *,
        language_code: str | None,
        limit: int = DEFAULT_PRIVATE_CATALOG_LIMIT,
    ) -> list[CatalogTourCardRead]:
        return self.catalog_preparation_service.list_catalog_cards(
            session,
            language_code=language_code,
            status=TourStatus.OPEN_FOR_SALE,
            limit=limit,
        )

    def list_entry_tours_filtered(
        self,
        session: Session,
        *,
        language_code: str | None,
        filters: CatalogBrowseFiltersRead,
        limit: int = DEFAULT_PRIVATE_CATALOG_LIMIT,
    ) -> list[CatalogTourCardRead]:
        return self.catalog_preparation_service.list_catalog_cards_filtered(
            session,
            filters=filters,
            language_code=language_code,
            status=TourStatus.OPEN_FOR_SALE,
            limit=limit,
        )

    def get_tour_detail(
        self,
        session: Session,
        *,
        tour_id: int,
        language_code: str | None,
    ) -> PreparedTourDetailRead | None:
        detail = self.language_aware_tour_service.get_localized_tour_detail(
            session,
            tour_id=tour_id,
            language_code=language_code,
        )
        if detail is None:
            return None
        if not tour_is_customer_catalog_visible(
            departure_datetime=detail.tour.departure_datetime,
            sales_deadline=detail.tour.sales_deadline,
        ):
            return None
        return detail

    def get_tour_detail_from_start_arg(
        self,
        session: Session,
        *,
        start_arg: str | None,
        language_code: str | None,
    ) -> PreparedTourDetailRead | None:
        if start_arg is None or not start_arg.startswith(START_TOUR_PREFIX):
            return None

        tour_code = start_arg.removeprefix(START_TOUR_PREFIX).strip()
        if not tour_code:
            return None

        tour = self.catalog_lookup_service.get_tour_by_code(session, code=tour_code)
        if tour is None:
            return None
        if not tour_is_customer_catalog_visible(
            departure_datetime=tour.departure_datetime,
            sales_deadline=tour.sales_deadline,
        ):
            return None

        return self.get_tour_detail(session, tour_id=tour.id, language_code=language_code)

    def build_date_filters(
        self,
        option: str,
        *,
        now: datetime | None = None,
    ) -> CatalogBrowseFiltersRead | None:
        current = now or datetime.now(UTC)
        if option == DATE_OPTION_WEEKEND:
            weekend_start, weekend_end = self._current_or_next_weekend_window(current)
            return CatalogBrowseFiltersRead(
                departure_from=weekend_start,
                departure_to=weekend_end,
            )
        if option == DATE_OPTION_NEXT_30_DAYS:
            return CatalogBrowseFiltersRead(
                departure_from=current,
                departure_to=current + timedelta(days=30),
            )
        if option == DATE_OPTION_ANY:
            return CatalogBrowseFiltersRead()
        return None

    def build_destination_filters(self, query: str) -> CatalogBrowseFiltersRead | None:
        normalized_query = " ".join(query.split())
        if not normalized_query:
            return None
        return CatalogBrowseFiltersRead(destination_query=normalized_query)

    def build_budget_filters(self, option: str) -> CatalogBrowseFiltersRead | None:
        max_price = self.parse_budget_option(option)
        if max_price is None and option != BUDGET_OPTION_ANY:
            return None
        return CatalogBrowseFiltersRead(max_price=max_price)

    def parse_budget_option(self, option: str) -> Decimal | None:
        if option == BUDGET_OPTION_ANY:
            return None
        try:
            return Decimal(option)
        except Exception:
            return None

    def get_budget_filter_currency(
        self,
        session: Session,
        *,
        language_code: str | None,
    ) -> str | None:
        cards = self.catalog_preparation_service.list_catalog_cards(
            session,
            language_code=language_code,
            status=TourStatus.OPEN_FOR_SALE,
            limit=100,
        )
        currencies = {card.currency for card in cards}
        if len(currencies) != 1:
            return None
        return next(iter(currencies))

    def get_budget_presets(self) -> tuple[Decimal, ...]:
        return self.BUDGET_PRESETS

    @staticmethod
    def _current_or_next_weekend_window(current: datetime) -> tuple[datetime, datetime]:
        if current.weekday() == 5:
            saturday = current.date()
        elif current.weekday() == 6:
            saturday = current.date() - timedelta(days=1)
        else:
            saturday = current.date() + timedelta(days=5 - current.weekday())
        sunday = saturday + timedelta(days=1)
        tzinfo = current.tzinfo
        return (
            datetime.combine(saturday, time.min, tzinfo=tzinfo),
            datetime.combine(sunday, time.max, tzinfo=tzinfo),
        )


class PrivateReservationPreparationService:
    def __init__(
        self,
        *,
        tour_browse_service: PrivateTourBrowseService | None = None,
    ) -> None:
        self.tour_browse_service = tour_browse_service or PrivateTourBrowseService()

    def get_preparable_tour(
        self,
        session: Session,
        *,
        tour_id: int,
        language_code: str | None,
    ) -> PreparedTourDetailRead | None:
        lazy_expire_due_reservations(session)
        detail = self.tour_browse_service.get_tour_detail(
            session,
            tour_id=tour_id,
            language_code=language_code,
        )
        if detail is None:
            return None
        if detail.tour.status != TourStatus.OPEN_FOR_SALE:
            return None
        if detail.tour.seats_available <= 0:
            return None
        if not detail.boarding_points:
            return None
        return detail

    def list_seat_count_options(self, detail: PreparedTourDetailRead) -> tuple[int, ...]:
        if not TourSalesModePolicyService.policy_for_sales_mode(detail.tour.sales_mode).per_seat_self_service_allowed:
            return ()
        available = min(detail.tour.seats_available, MAX_PRIVATE_PREPARATION_SEATS)
        if available <= 0:
            return ()
        return tuple(range(1, available + 1))

    def build_preparation_summary(
        self,
        session: Session,
        *,
        tour_id: int,
        seats_count: int,
        boarding_point_id: int,
        language_code: str | None,
    ) -> ReservationPreparationSummaryRead | None:
        detail = self.get_preparable_tour(
            session,
            tour_id=tour_id,
            language_code=language_code,
        )
        if detail is None:
            return None

        cat_policy = TourSalesModePolicyService.policy_for_catalog_tour(detail.tour)
        if cat_policy.per_seat_self_service_allowed:
            if seats_count not in self.list_seat_count_options(detail):
                return None
        elif cat_policy.mini_app_catalog_reservation_allowed:
            fixed = cat_policy.catalog_charter_fixed_seats_count
            if fixed is None or seats_count != fixed:
                return None
        else:
            return None

        boarding_point = next(
            (point for point in detail.boarding_points if point.id == boarding_point_id),
            None,
        )
        if boarding_point is None:
            return None

        return ReservationPreparationSummaryRead(
            tour=ReservationPreparationTourRead(
                id=detail.tour.id,
                code=detail.tour.code,
                departure_datetime=detail.tour.departure_datetime,
                return_datetime=detail.tour.return_datetime,
                base_price=detail.tour.base_price,
                currency=detail.tour.currency,
                seats_available_snapshot=detail.tour.seats_available,
                localized_content=detail.localized_content,
            ),
            seats_count=seats_count,
            boarding_point=boarding_point,
            estimated_total_amount=detail.tour.base_price * seats_count,
        )
