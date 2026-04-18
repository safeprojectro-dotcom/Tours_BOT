"""Track 5g.1: derive read-side commercial journey classification from authoritative Layer A / RFQ truth."""

from __future__ import annotations

from app.models.enums import CustomerCommercialMode, TourSalesMode


def commercial_mode_for_catalog_tour_sales_mode(sales_mode: TourSalesMode) -> CustomerCommercialMode:
    """Map Layer A catalog tour sales mode to Track 5g commercial mode (Modes 1–2)."""
    if sales_mode is TourSalesMode.PER_SEAT:
        return CustomerCommercialMode.SUPPLIER_ROUTE_PER_SEAT
    if sales_mode is TourSalesMode.FULL_BUS:
        return CustomerCommercialMode.SUPPLIER_ROUTE_FULL_BUS
    raise ValueError(f"unsupported tour sales mode for commercial classification: {sales_mode!r}")
