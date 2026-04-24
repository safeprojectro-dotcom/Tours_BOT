from __future__ import annotations

import unittest
from datetime import UTC, datetime
from types import SimpleNamespace

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
            allow_dev_fallback=False,
        )
        self.assertEqual(resolved, 4242)

    def test_runtime_identity_resolution_reads_telegram_init_data_user(self) -> None:
        resolved = MiniAppShell.resolve_runtime_telegram_user_id(
            app_env="production",
            route='/bookings?tgWebAppData=query_id%3DAQAA%26user%3D%257B%2522id%2522%253A777001%252C%2522first_name%2522%253A%2522A%2522%257D',
            page_url=None,
            page_query=None,
            dev_telegram_user_id=100001,
            allow_dev_fallback=False,
        )
        self.assertEqual(resolved, 777001)

    def test_runtime_identity_resolution_reads_direct_bridge_injected_query_key(self) -> None:
        resolved = MiniAppShell.resolve_runtime_telegram_user_id(
            app_env="production",
            route="/bookings?tg_bridge_user_id=777114",
            page_url=None,
            page_query=None,
            dev_telegram_user_id=100001,
            allow_dev_fallback=False,
        )
        self.assertEqual(resolved, 777114)

    def test_runtime_identity_resolution_reads_init_data_from_page_query_mapping(self) -> None:
        resolved = MiniAppShell.resolve_runtime_telegram_user_id(
            app_env="production",
            route="/bookings",
            page_url=None,
            page_query={
                "tgWebAppData": 'query_id=AAAB&user={"id":888002,"first_name":"B"}',
            },
            dev_telegram_user_id=100001,
            allow_dev_fallback=False,
        )
        self.assertEqual(resolved, 888002)

    def test_runtime_identity_resolution_reads_direct_bridge_key_from_page_query(self) -> None:
        resolved = MiniAppShell.resolve_runtime_telegram_user_id(
            app_env="production",
            route="/bookings",
            page_url=None,
            page_query={"tg_bridge_user_id": "990011"},
            dev_telegram_user_id=100001,
            allow_dev_fallback=False,
        )
        self.assertEqual(resolved, 990011)

    def test_query_string_has_key_detects_tg_bridge_key(self) -> None:
        self.assertTrue(
            MiniAppShell._query_string_has_key("foo=1&tg_bridge_user_id=777114", "tg_bridge_user_id")
        )
        self.assertFalse(
            MiniAppShell._query_string_has_key("foo=1&bar=2", "tg_bridge_user_id")
        )

    def test_runtime_identity_resolution_reads_querystring_object_to_dict(self) -> None:
        class _QueryStringLike:
            @property
            def to_dict(self) -> dict[str, str]:
                return {
                    "tgWebAppData": 'query_id=AAAB&user={"id":918273,"first_name":"Q"}',
                }

        resolved = MiniAppShell.resolve_runtime_telegram_user_id(
            app_env="production",
            route="/bookings",
            page_url=None,
            page_query=_QueryStringLike(),
            dev_telegram_user_id=100001,
            allow_dev_fallback=False,
        )
        self.assertEqual(resolved, 918273)

    def test_runtime_identity_resolution_reads_fragment_query_path(self) -> None:
        resolved = MiniAppShell.resolve_runtime_telegram_user_id(
            app_env="production",
            route="/",
            page_url="https://mini.example/#/?tgWebAppData=query_id%3DAAAB%26user%3D%257B%2522id%2522%253A999003%257D",
            page_query=None,
            dev_telegram_user_id=100001,
            allow_dev_fallback=False,
        )
        self.assertEqual(resolved, 999003)

    def test_runtime_identity_resolution_disables_dev_fallback_outside_local(self) -> None:
        resolved = MiniAppShell.resolve_runtime_telegram_user_id(
            app_env="production",
            route="/bookings",
            page_url=None,
            page_query=None,
            dev_telegram_user_id=100001,
            allow_dev_fallback=True,
        )
        self.assertIsNone(resolved)

    def test_runtime_identity_resolution_keeps_dev_fallback_in_local(self) -> None:
        resolved = MiniAppShell.resolve_runtime_telegram_user_id(
            app_env="local",
            route="/bookings",
            page_url=None,
            page_query=None,
            dev_telegram_user_id=100001,
            allow_dev_fallback=True,
        )
        self.assertEqual(resolved, 100001)

    def test_runtime_identity_resolution_requires_explicit_flag_for_dev_fallback(self) -> None:
        resolved = MiniAppShell.resolve_runtime_telegram_user_id(
            app_env="local",
            route="/bookings",
            page_url=None,
            page_query=None,
            dev_telegram_user_id=100001,
            allow_dev_fallback=False,
        )
        self.assertIsNone(resolved)

    def test_apply_resolved_identity_propagates_to_user_scoped_screens(self) -> None:
        shell = MiniAppShell.__new__(MiniAppShell)
        shell._resolved_telegram_user_id = 556677
        shell.my_bookings_screen = SimpleNamespace(telegram_user_id=None)
        shell.booking_detail_screen = SimpleNamespace(telegram_user_id=None)
        shell.my_requests_list_screen = SimpleNamespace(telegram_user_id=None)
        shell.my_request_detail_screen = SimpleNamespace(telegram_user_id=None)
        shell.settings_screen = SimpleNamespace(telegram_user_id=None)

        MiniAppShell._apply_resolved_identity_to_user_scoped_screens(shell)

        self.assertEqual(shell.my_bookings_screen.telegram_user_id, 556677)
        self.assertEqual(shell.booking_detail_screen.telegram_user_id, 556677)
        self.assertEqual(shell.my_requests_list_screen.telegram_user_id, 556677)
        self.assertEqual(shell.my_request_detail_screen.telegram_user_id, 556677)
        self.assertEqual(shell.settings_screen.telegram_user_id, 556677)

    def test_apply_resolved_identity_keeps_fail_closed_when_missing(self) -> None:
        shell = MiniAppShell.__new__(MiniAppShell)
        shell._resolved_telegram_user_id = None
        shell.my_bookings_screen = SimpleNamespace(telegram_user_id=100001)
        shell.booking_detail_screen = SimpleNamespace(telegram_user_id=100001)
        shell.my_requests_list_screen = SimpleNamespace(telegram_user_id=100001)
        shell.my_request_detail_screen = SimpleNamespace(telegram_user_id=100001)
        shell.settings_screen = SimpleNamespace(telegram_user_id=100001)

        MiniAppShell._apply_resolved_identity_to_user_scoped_screens(shell)

        self.assertIsNone(shell.my_bookings_screen.telegram_user_id)
        self.assertIsNone(shell.booking_detail_screen.telegram_user_id)
        self.assertIsNone(shell.my_requests_list_screen.telegram_user_id)
        self.assertIsNone(shell.my_request_detail_screen.telegram_user_id)
        self.assertIsNone(shell.settings_screen.telegram_user_id)


if __name__ == "__main__":
    unittest.main()
