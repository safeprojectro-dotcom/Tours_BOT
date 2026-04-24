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
        self.assertFalse(row.execution_activation_available)
        self.assertIsNone(row.execution_target_tour_code)

    def test_runtime_identity_resolution_uses_runtime_query_when_present(self) -> None:
        resolved = MiniAppShell.resolve_runtime_telegram_user_id(
            app_env="production",
            route="/bookings?telegram_user_id=4242",
            page_url=None,
            page_query=None,
            dev_telegram_user_id=100001,
        )
        self.assertEqual(resolved, 4242)

    def test_runtime_identity_resolution_disables_dev_fallback_outside_local(self) -> None:
        resolved = MiniAppShell.resolve_runtime_telegram_user_id(
            app_env="production",
            route="/bookings",
            page_url=None,
            page_query=None,
            dev_telegram_user_id=100001,
        )
        self.assertIsNone(resolved)

    def test_runtime_identity_resolution_keeps_dev_fallback_in_local(self) -> None:
        resolved = MiniAppShell.resolve_runtime_telegram_user_id(
            app_env="local",
            route="/bookings",
            page_url=None,
            page_query=None,
            dev_telegram_user_id=100001,
        )
        self.assertEqual(resolved, 100001)


if __name__ == "__main__":
    unittest.main()
