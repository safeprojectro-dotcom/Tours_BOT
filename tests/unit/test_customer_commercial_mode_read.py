"""Track 5g.1: commercial_mode derivation from Layer A sales_mode."""

from __future__ import annotations

import unittest

from app.models.enums import CustomerCommercialMode, TourSalesMode
from app.services.customer_commercial_mode_read import commercial_mode_for_catalog_tour_sales_mode


class CustomerCommercialModeReadTests(unittest.TestCase):
    def test_per_seat_maps_to_supplier_route_per_seat(self) -> None:
        self.assertEqual(
            commercial_mode_for_catalog_tour_sales_mode(TourSalesMode.PER_SEAT),
            CustomerCommercialMode.SUPPLIER_ROUTE_PER_SEAT,
        )

    def test_full_bus_maps_to_supplier_route_full_bus(self) -> None:
        self.assertEqual(
            commercial_mode_for_catalog_tour_sales_mode(TourSalesMode.FULL_BUS),
            CustomerCommercialMode.SUPPLIER_ROUTE_FULL_BUS,
        )
