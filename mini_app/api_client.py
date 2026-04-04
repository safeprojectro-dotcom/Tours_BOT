from __future__ import annotations

from decimal import Decimal

import httpx

from app.schemas.mini_app import (
    MiniAppBookingDetailRead,
    MiniAppBookingsListRead,
    MiniAppCatalogRead,
    MiniAppHelpRead,
    MiniAppLanguagePreferenceResponse,
    MiniAppReservationPreparationRead,
    MiniAppSettingsRead,
    MiniAppSupportRequestResponse,
    MiniAppTourDetailRead,
)
from app.schemas.payment import PaymentReconciliationRead
from app.schemas.prepared import OrderSummaryRead, PaymentEntryRead, ReservationPreparationSummaryRead


class MiniAppApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def get_help(self, *, language_code: str | None = None) -> MiniAppHelpRead:
        params: dict[str, str] = {}
        if language_code:
            params["language_code"] = language_code
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.get("/mini-app/help", params=params or None)
            response.raise_for_status()
            return MiniAppHelpRead.model_validate(response.json())

    async def post_support_request(
        self,
        *,
        telegram_user_id: int,
        order_id: int | None,
        screen_hint: str,
    ) -> MiniAppSupportRequestResponse:
        body = {
            "telegram_user_id": telegram_user_id,
            "order_id": order_id,
            "screen_hint": screen_hint,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
            response = await client.post("/mini-app/support-request", json=body)
            response.raise_for_status()
            return MiniAppSupportRequestResponse.model_validate(response.json())

    async def get_mini_app_settings(self, *, telegram_user_id: int | None = None) -> MiniAppSettingsRead:
        params: dict[str, object] = {}
        if telegram_user_id is not None:
            params["telegram_user_id"] = telegram_user_id
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.get("/mini-app/settings", params=params or None)
            response.raise_for_status()
            return MiniAppSettingsRead.model_validate(response.json())

    async def post_language_preference(self, *, telegram_user_id: int, language_code: str) -> str:
        body = {"telegram_user_id": telegram_user_id, "language_code": language_code}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.post("/mini-app/language-preference", json=body)
            response.raise_for_status()
            data = MiniAppLanguagePreferenceResponse.model_validate(response.json())
            return data.language_code

    async def list_my_bookings(
        self,
        *,
        telegram_user_id: int,
        language_code: str | None = None,
    ) -> MiniAppBookingsListRead:
        params = {"telegram_user_id": telegram_user_id, "language_code": language_code}
        filtered_params = {key: value for key, value in params.items() if value not in (None, "")}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
            response = await client.get("/mini-app/bookings", params=filtered_params)
            response.raise_for_status()
            return MiniAppBookingsListRead.model_validate(response.json())

    async def get_booking_status(
        self,
        *,
        order_id: int,
        telegram_user_id: int,
        language_code: str | None = None,
    ) -> MiniAppBookingDetailRead:
        params = {"telegram_user_id": telegram_user_id, "language_code": language_code}
        filtered_params = {key: value for key, value in params.items() if value not in (None, "")}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
            response = await client.get(f"/mini-app/orders/{order_id}/booking-status", params=filtered_params)
            response.raise_for_status()
            return MiniAppBookingDetailRead.model_validate(response.json())

    async def list_catalog(
        self,
        *,
        language_code: str | None = None,
        destination_query: str | None = None,
        departure_date_from: str | None = None,
        departure_date_to: str | None = None,
        max_price: Decimal | None = None,
        limit: int = 24,
        offset: int = 0,
    ) -> MiniAppCatalogRead:
        params = {
            "language_code": language_code,
            "destination_query": destination_query,
            "departure_date_from": departure_date_from,
            "departure_date_to": departure_date_to,
            "max_price": str(max_price) if max_price is not None else None,
            "limit": limit,
            "offset": offset,
        }
        filtered_params = {key: value for key, value in params.items() if value not in (None, "")}

        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.get("/mini-app/catalog", params=filtered_params)
            response.raise_for_status()
            return MiniAppCatalogRead.model_validate(response.json())

    async def get_tour_detail(
        self,
        *,
        tour_code: str,
        language_code: str | None = None,
    ) -> MiniAppTourDetailRead:
        params = {"language_code": language_code}
        filtered_params = {key: value for key, value in params.items() if value not in (None, "")}

        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.get(f"/mini-app/tours/{tour_code}", params=filtered_params)
            response.raise_for_status()
            return MiniAppTourDetailRead.model_validate(response.json())

    async def get_tour_preparation(
        self,
        *,
        tour_code: str,
        language_code: str | None = None,
    ) -> MiniAppReservationPreparationRead:
        params = {"language_code": language_code}
        filtered_params = {key: value for key, value in params.items() if value not in (None, "")}

        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.get(f"/mini-app/tours/{tour_code}/preparation", params=filtered_params)
            response.raise_for_status()
            return MiniAppReservationPreparationRead.model_validate(response.json())

    async def get_preparation_summary(
        self,
        *,
        tour_code: str,
        seats_count: int,
        boarding_point_id: int,
        language_code: str | None = None,
    ) -> ReservationPreparationSummaryRead:
        params = {
            "seats_count": seats_count,
            "boarding_point_id": boarding_point_id,
            "language_code": language_code,
        }
        filtered_params = {key: value for key, value in params.items() if value not in (None, "")}

        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.get(
                f"/mini-app/tours/{tour_code}/preparation-summary",
                params=filtered_params,
            )
            response.raise_for_status()
            return ReservationPreparationSummaryRead.model_validate(response.json())

    async def create_temporary_reservation(
        self,
        *,
        tour_code: str,
        telegram_user_id: int,
        seats_count: int,
        boarding_point_id: int,
        language_code: str | None = None,
    ) -> OrderSummaryRead:
        params = {"language_code": language_code}
        filtered_params = {key: value for key, value in params.items() if value not in (None, "")}
        body = {
            "telegram_user_id": telegram_user_id,
            "seats_count": seats_count,
            "boarding_point_id": boarding_point_id,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
            response = await client.post(
                f"/mini-app/tours/{tour_code}/reservations",
                params=filtered_params,
                json=body,
            )
            response.raise_for_status()
            return OrderSummaryRead.model_validate(response.json())

    async def get_reservation_overview(
        self,
        *,
        order_id: int,
        telegram_user_id: int,
        language_code: str | None = None,
    ) -> OrderSummaryRead:
        params = {"telegram_user_id": telegram_user_id, "language_code": language_code}
        filtered_params = {key: value for key, value in params.items() if value not in (None, "")}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
            response = await client.get(
                f"/mini-app/orders/{order_id}/reservation-overview",
                params=filtered_params,
            )
            response.raise_for_status()
            return OrderSummaryRead.model_validate(response.json())

    async def start_payment_entry(
        self,
        *,
        order_id: int,
        telegram_user_id: int,
    ) -> PaymentEntryRead:
        body = {"telegram_user_id": telegram_user_id}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
            response = await client.post(f"/mini-app/orders/{order_id}/payment-entry", json=body)
            response.raise_for_status()
            return PaymentEntryRead.model_validate(response.json())

    async def complete_mock_payment(
        self,
        *,
        order_id: int,
        telegram_user_id: int,
    ) -> PaymentReconciliationRead:
        body = {"telegram_user_id": telegram_user_id}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
            response = await client.post(f"/mini-app/orders/{order_id}/mock-payment-complete", json=body)
            response.raise_for_status()
            return PaymentReconciliationRead.model_validate(response.json())
