from __future__ import annotations

import unittest
from datetime import UTC, datetime

from app.models.enums import SupplierOfferLifecycle
from app.schemas.mini_app import (
    MiniAppSupplierOfferActionabilityState,
    MiniAppSupplierOfferLandingRead,
    MiniAppSupplierOfferPublicationContextRead,
)
from mini_app.app import MiniAppShell
from mini_app.ui_strings import shell


class MiniAppSupplierOfferLandingWiringTests(unittest.TestCase):
    def test_extract_supplier_offer_route_id(self) -> None:
        self.assertEqual(MiniAppShell._extract_supplier_offer_id("/supplier-offers/7"), 7)
        self.assertEqual(MiniAppShell._extract_supplier_offer_id("/supplier-offers/42/"), 42)

    def test_extract_supplier_offer_route_rejects_non_matching_routes(self) -> None:
        self.assertIsNone(MiniAppShell._extract_supplier_offer_id("/"))
        self.assertIsNone(MiniAppShell._extract_supplier_offer_id("/supplier-offers/abc"))
        self.assertIsNone(MiniAppShell._extract_supplier_offer_id("/tours/BELGRADE"))

    def test_supplier_offer_landing_schema_has_catalog_fallback_default(self) -> None:
        row = MiniAppSupplierOfferLandingRead(
            supplier_offer_id=9,
            title="Offer",
            description="Desc",
            departure_datetime=datetime(2027, 1, 1, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2027, 1, 2, 20, 0, tzinfo=UTC),
            seats_total=40,
            base_price=None,
            currency=None,
            publication=MiniAppSupplierOfferPublicationContextRead(
                lifecycle_status=SupplierOfferLifecycle.PUBLISHED,
            ),
        )
        self.assertEqual(row.catalog_fallback_route, "/")

    def test_supplier_offer_shell_has_catalog_cta_label(self) -> None:
        self.assertEqual(shell("en", "supplier_offer_btn_browse_catalog"), "Browse catalog")

    def test_supplier_offer_actionability_defaults_to_view_only(self) -> None:
        row = MiniAppSupplierOfferLandingRead(
            supplier_offer_id=10,
            title="Offer",
            description="Desc",
            departure_datetime=datetime(2027, 1, 1, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2027, 1, 2, 20, 0, tzinfo=UTC),
            seats_total=20,
            publication=MiniAppSupplierOfferPublicationContextRead(
                lifecycle_status=SupplierOfferLifecycle.PUBLISHED,
            ),
        )
        self.assertEqual(row.actionability_state, MiniAppSupplierOfferActionabilityState.VIEW_ONLY)
        self.assertEqual(row.actionability_state.value, "view_only")


if __name__ == "__main__":
    unittest.main()
