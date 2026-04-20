"""Narrow read-side operational alerts for supplier-owned offers (Y25)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.models.enums import SupplierOfferLifecycle
from app.schemas.supplier_admin import SupplierOfferRead


@dataclass(frozen=True)
class SupplierOfferOperationalAlert:
    code: str


class SupplierOfferOperationalAlertService:
    """
    Deterministic alert derivation from existing supplier-offer truth only.

    Intentionally does not derive sold/hold/payment alerts because the current model
    has no authoritative supplier_offer -> Layer A execution linkage.
    """

    _departing_window = timedelta(hours=24)

    def alerts_for_offer(
        self,
        *,
        offer: SupplierOfferRead,
        now_utc: datetime | None = None,
    ) -> list[SupplierOfferOperationalAlert]:
        now = now_utc or datetime.now(UTC)
        alerts: list[SupplierOfferOperationalAlert] = []

        # Retracted from publication: retains published_at history but status moved back to approved.
        if offer.lifecycle_status == SupplierOfferLifecycle.APPROVED and offer.published_at is not None:
            alerts.append(SupplierOfferOperationalAlert(code="publication_retracted"))
            return alerts

        if offer.lifecycle_status != SupplierOfferLifecycle.PUBLISHED:
            return alerts

        dep = offer.departure_datetime
        if dep <= now:
            alerts.append(SupplierOfferOperationalAlert(code="offer_departed"))
            return alerts

        if dep - now <= self._departing_window:
            alerts.append(SupplierOfferOperationalAlert(code="offer_departing_soon"))

        return alerts
