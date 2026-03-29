from __future__ import annotations

from decimal import Decimal

import httpx

from app.schemas.mini_app import MiniAppCatalogRead, MiniAppTourDetailRead


class MiniAppApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

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
