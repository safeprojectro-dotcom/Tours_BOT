from __future__ import annotations

import json
import time
from decimal import Decimal
from pathlib import Path

import httpx

from app.schemas.custom_marketplace import (
    MiniAppCustomRequestCreatedRead,
    MiniAppCustomRequestCustomerDetailRead,
    MiniAppCustomRequestCustomerListRead,
)
from app.schemas.mini_app import (
    MiniAppBookingDetailRead,
    MiniAppBookingsListRead,
    MiniAppBridgeExecutionPreparationResponse,
    MiniAppBridgePaymentEligibilityRead,
    MiniAppCatalogRead,
    MiniAppHelpRead,
    MiniAppLanguagePreferenceResponse,
    MiniAppReservationPreparationRead,
    MiniAppSupplierOfferLandingRead,
    MiniAppSettingsRead,
    MiniAppSupportRequestResponse,
    MiniAppTourDetailRead,
    MiniAppWaitlistJoinResponse,
    MiniAppWaitlistStatusRead,
)
from app.schemas.payment import PaymentReconciliationRead
from app.schemas.prepared import OrderSummaryRead, PaymentEntryRead, ReservationPreparationSummaryRead

DEBUG_LOG_PATH = Path("debug-7dffdf.log")


def _agent_debug_log(
    *,
    run_id: str,
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict[str, object],
) -> None:
    payload = {
        "sessionId": "7dffdf",
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        with DEBUG_LOG_PATH.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception:
        return


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

    async def post_custom_request(self, *, body: dict[str, object]) -> MiniAppCustomRequestCreatedRead:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=20.0) as client:
            response = await client.post("/mini-app/custom-requests", json=body)
            response.raise_for_status()
            return MiniAppCustomRequestCreatedRead.model_validate(response.json())

    async def list_custom_requests_for_customer(
        self,
        *,
        telegram_user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> MiniAppCustomRequestCustomerListRead:
        # region agent log
        _agent_debug_log(
            run_id="baseline",
            hypothesis_id="H4",
            location="mini_app/api_client.py:list_custom_requests_for_customer",
            message="outgoing identity on my-requests list",
            data={"telegram_user_id_present": telegram_user_id > 0},
        )
        # endregion
        params: dict[str, object] = {
            "telegram_user_id": telegram_user_id,
            "limit": limit,
            "offset": offset,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
            response = await client.get("/mini-app/custom-requests", params=params)
            response.raise_for_status()
            return MiniAppCustomRequestCustomerListRead.model_validate(response.json())

    async def get_custom_request_for_customer(
        self,
        *,
        request_id: int,
        telegram_user_id: int,
    ) -> MiniAppCustomRequestCustomerDetailRead:
        # region agent log
        _agent_debug_log(
            run_id="baseline",
            hypothesis_id="H4",
            location="mini_app/api_client.py:get_custom_request_for_customer",
            message="outgoing identity on my-request detail",
            data={"telegram_user_id_present": telegram_user_id > 0, "request_id": request_id},
        )
        # endregion
        params = {"telegram_user_id": telegram_user_id}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
            response = await client.get(f"/mini-app/custom-requests/{request_id}", params=params)
            response.raise_for_status()
            return MiniAppCustomRequestCustomerDetailRead.model_validate(response.json())

    async def get_booking_bridge_preparation(
        self,
        *,
        request_id: int,
        telegram_user_id: int,
        language_code: str | None = None,
    ) -> MiniAppBridgeExecutionPreparationResponse:
        params: dict[str, object] = {"telegram_user_id": telegram_user_id}
        if language_code:
            params["language_code"] = language_code
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
            response = await client.get(
                f"/mini-app/custom-requests/{request_id}/booking-bridge/preparation",
                params=params,
            )
            response.raise_for_status()
            return MiniAppBridgeExecutionPreparationResponse.model_validate(response.json())

    async def create_booking_bridge_reservation(
        self,
        *,
        request_id: int,
        telegram_user_id: int,
        seats_count: int,
        boarding_point_id: int,
        language_code: str | None = None,
    ) -> OrderSummaryRead:
        params: dict[str, object] = {}
        if language_code:
            params["language_code"] = language_code
        filtered_params = {k: v for k, v in params.items() if v not in (None, "")}
        body = {
            "telegram_user_id": telegram_user_id,
            "seats_count": seats_count,
            "boarding_point_id": boarding_point_id,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=20.0) as client:
            response = await client.post(
                f"/mini-app/custom-requests/{request_id}/booking-bridge/reservations",
                params=filtered_params or None,
                json=body,
            )
            response.raise_for_status()
            return OrderSummaryRead.model_validate(response.json())

    async def get_booking_bridge_payment_eligibility(
        self,
        *,
        request_id: int,
        telegram_user_id: int,
        order_id: int,
    ) -> MiniAppBridgePaymentEligibilityRead:
        params = {"telegram_user_id": telegram_user_id, "order_id": order_id}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
            response = await client.get(
                f"/mini-app/custom-requests/{request_id}/booking-bridge/payment-eligibility",
                params=params,
            )
            response.raise_for_status()
            return MiniAppBridgePaymentEligibilityRead.model_validate(response.json())

    async def post_support_request(
        self,
        *,
        telegram_user_id: int,
        order_id: int | None,
        screen_hint: str,
        tour_code: str | None = None,
    ) -> MiniAppSupportRequestResponse:
        body: dict[str, object] = {
            "telegram_user_id": telegram_user_id,
            "order_id": order_id,
            "screen_hint": screen_hint,
        }
        if tour_code is not None:
            body["tour_code"] = tour_code
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
            response = await client.post("/mini-app/support-request", json=body)
            response.raise_for_status()
            return MiniAppSupportRequestResponse.model_validate(response.json())

    async def get_mini_app_settings(self, *, telegram_user_id: int | None = None) -> MiniAppSettingsRead:
        # region agent log
        _agent_debug_log(
            run_id="baseline",
            hypothesis_id="H4",
            location="mini_app/api_client.py:get_mini_app_settings",
            message="outgoing identity on settings get",
            data={"telegram_user_id_present": telegram_user_id is not None and telegram_user_id > 0},
        )
        # endregion
        params: dict[str, object] = {}
        if telegram_user_id is not None:
            params["telegram_user_id"] = telegram_user_id
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.get("/mini-app/settings", params=params or None)
            response.raise_for_status()
            return MiniAppSettingsRead.model_validate(response.json())

    async def get_supplier_offer_landing(self, *, supplier_offer_id: int) -> MiniAppSupplierOfferLandingRead:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.get(f"/mini-app/supplier-offers/{supplier_offer_id}")
            response.raise_for_status()
            return MiniAppSupplierOfferLandingRead.model_validate(response.json())

    async def post_language_preference(self, *, telegram_user_id: int, language_code: str) -> str:
        # region agent log
        _agent_debug_log(
            run_id="baseline",
            hypothesis_id="H4",
            location="mini_app/api_client.py:post_language_preference",
            message="outgoing identity on settings save",
            data={"telegram_user_id_present": telegram_user_id > 0, "language_code_present": bool(language_code)},
        )
        # endregion
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
        # region agent log
        _agent_debug_log(
            run_id="baseline",
            hypothesis_id="H4",
            location="mini_app/api_client.py:list_my_bookings",
            message="outgoing identity on bookings list",
            data={"telegram_user_id_present": telegram_user_id > 0, "language_code_present": bool(language_code)},
        )
        # endregion
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

    async def get_waitlist_status(
        self,
        *,
        tour_code: str,
        telegram_user_id: int,
    ) -> MiniAppWaitlistStatusRead:
        params = {"telegram_user_id": telegram_user_id}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.get(f"/mini-app/tours/{tour_code}/waitlist-status", params=params)
            response.raise_for_status()
            return MiniAppWaitlistStatusRead.model_validate(response.json())

    async def post_waitlist(
        self,
        *,
        tour_code: str,
        telegram_user_id: int,
        seats_count: int = 1,
    ) -> MiniAppWaitlistJoinResponse:
        body = {"telegram_user_id": telegram_user_id, "seats_count": seats_count}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
            response = await client.post(f"/mini-app/tours/{tour_code}/waitlist", json=body)
            response.raise_for_status()
            return MiniAppWaitlistJoinResponse.model_validate(response.json())

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
