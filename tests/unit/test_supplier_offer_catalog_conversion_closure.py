"""E2E-style unit proof: supplier offer → bridge → catalog activation → publish → execution link → closure flags.

Does not invoke booking, payment, orders, or reservations — only admin/catalog/landing/routing read paths.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import event, func, select

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import (
    SupplierOfferLifecycle,
    SupplierOfferPackagingStatus,
    SupplierOfferPaymentMode,
    TourSalesMode,
    TourStatus,
)
from app.models.supplier import SupplierOffer
from app.models.supplier_offer_tour_bridge import SupplierOfferTourBridge
from app.models.tour import Tour
from app.services.mini_app_catalog import MiniAppCatalogService
from app.services.mini_app_supplier_offer_landing import MiniAppSupplierOfferLandingService
from app.services.supplier_offer_bot_start_routing import resolve_sup_offer_start_mini_app_routing
from app.services.supplier_offer_review_package_service import SupplierOfferReviewPackageService
from tests.unit.base import FoundationDBTestCase


class SupplierOfferCatalogConversionClosureE2ETests(FoundationDBTestCase):
    """Explicit admin chain (HTTP + same-session DB); deterministic dates in the future."""

    def setUp(self) -> None:
        super().setUp()
        self.nested = self.connection.begin_nested()

        @event.listens_for(self.session, "after_transaction_end")
        def restart_savepoint(session, transaction) -> None:
            parent = getattr(transaction, "_parent", None)
            if transaction.nested and not getattr(parent, "nested", False):
                self.nested = self.connection.begin_nested()

        self._restart_savepoint = restart_savepoint
        self.app = create_app()
        self._original_admin = get_settings().admin_api_token
        get_settings().admin_api_token = "test-admin-cc-closure"
        self.app.dependency_overrides[get_db] = self._db_override
        self.client = TestClient(self.app)

    def _db_override(self):
        yield self.session

    def tearDown(self) -> None:
        get_settings().admin_api_token = self._original_admin
        self.client.close()
        self.app.dependency_overrides.clear()
        event.remove(self.session, "after_transaction_end", self._restart_savepoint)
        super().tearDown()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer test-admin-cc-closure"}

    def _publish_mock_cfg(self) -> SimpleNamespace:
        return SimpleNamespace(
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://catalog-closure.example/mini/",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_token="tok",
        )

    def _review_pkg_settings_patch(self) -> SimpleNamespace:
        """Settings slice used by conversion_closure bot URL resolution."""
        return SimpleNamespace(
            telegram_mini_app_url="https://catalog-closure.example/mini/",
            telegram_bot_username="testbot",
            telegram_offer_showcase_channel_id="",
            telegram_bot_token="",
        )

    def test_explicit_admin_chain_closes_conversion_closure_per_seat(self) -> None:
        """Bridge → activate catalog → catalog lists Tour without execution link → publish → link → closure green."""
        supplier = self.create_supplier()
        dep = datetime(2026, 12, 10, 8, 0, tzinfo=UTC)
        ret = datetime(2026, 12, 12, 18, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(
            supplier,
            title="Closure Trip",
            description="Full description for bridge.",
            marketing_summary="Summary",
            program_text="Day one walk.",
            included_text="Meals",
            excluded_text="Tips",
            departure_datetime=dep,
            return_datetime=ret,
            seats_total=40,
            base_price=Decimal("199.00"),
            currency="EUR",
            sales_mode=TourSalesMode.PER_SEAT,
            payment_mode=SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
            lifecycle_status=SupplierOfferLifecycle.READY_FOR_MODERATION,
            packaging_status=SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH,
        )
        self.session.commit()
        oid = offer.id

        apr = self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=self._headers())
        self.assertEqual(apr.status_code, 200, apr.text)

        br = self.client.post(f"/admin/supplier-offers/{oid}/tour-bridge", headers=self._headers(), json={})
        self.assertEqual(br.status_code, 200, br.text)
        tour_id = br.json()["tour_id"]
        tour = self.session.get(Tour, tour_id)
        self.assertIsNotNone(tour)
        assert tour is not None
        tour_code = (tour.code or "").strip()

        act = self.client.post(f"/admin/tours/{tour_id}/activate-for-catalog", headers=self._headers(), json={})
        self.assertEqual(act.status_code, 200, act.text)
        self.assertEqual(act.json()["status"], "open_for_sale")
        self.session.expire_all()

        catalog = MiniAppCatalogService().list_catalog(self.session, language_code="en", limit=50, offset=0)
        codes = [it.code for it in catalog.items]
        self.assertIn(
            tour_code,
            codes,
            "Central Mini App catalog lists OPEN_FOR_SALE tours without requiring an execution link.",
        )

        review_patch = "app.services.supplier_offer_review_package_service.get_settings"
        with patch(review_patch, return_value=self._review_pkg_settings_patch()):
            rp_mid = self.client.get(f"/admin/supplier-offers/{oid}/review-package", headers=self._headers())
        self.assertEqual(rp_mid.status_code, 200, rp_mid.text)
        cc_mid = rp_mid.json()["conversion_closure"]
        self.assertTrue(cc_mid["has_tour_bridge"])
        self.assertTrue(cc_mid["central_catalog_contains_tour"])
        self.assertTrue(cc_mid["has_catalog_visible_tour"])
        self.assertFalse(cc_mid["has_active_execution_link"])
        self.assertIsNotNone(cc_mid["next_missing_step"])

        mock_cfg = self._publish_mock_cfg()
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
            patch("app.services.supplier_offer_moderation_service.send_showcase_publication", return_value=77),
        ):
            pub = self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=self._headers())
        self.assertEqual(pub.status_code, 200, pub.text)

        lk = self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link",
            headers=self._headers(),
            json={"tour_id": tour_id},
        )
        self.assertEqual(lk.status_code, 200, lk.text)

        landing = MiniAppSupplierOfferLandingService().get_published_offer_landing(self.session, supplier_offer_id=oid)
        self.assertIsNotNone(landing)
        assert landing is not None
        self.assertTrue(landing.has_execution_link)
        self.assertEqual(landing.linked_tour_id, tour_id)
        self.assertEqual((landing.linked_tour_code or "").strip(), tour_code)

        offer_row = self.session.get(SupplierOffer, oid)
        assert offer_row is not None
        nav = resolve_sup_offer_start_mini_app_routing(
            self.session,
            offer=offer_row,
            mini_app_base_url="https://catalog-closure.example/mini/",
        )
        self.assertEqual(nav.exact_tour_mini_app_url, f"https://catalog-closure.example/mini/tours/{tour_code}")
        self.assertFalse(nav.linked_is_full_bus)

        with patch(review_patch, return_value=self._review_pkg_settings_patch()):
            svc = SupplierOfferReviewPackageService()
            pkg = svc.review_package(self.session, offer_id=oid)
        cl = pkg.conversion_closure
        self.assertTrue(cl.has_tour_bridge)
        self.assertTrue(cl.has_catalog_visible_tour)
        self.assertTrue(cl.has_active_execution_link)
        self.assertTrue(cl.supplier_offer_landing_routes_to_tour)
        self.assertTrue(cl.bot_deeplink_routes_to_tour)
        self.assertTrue(cl.central_catalog_contains_tour)
        self.assertIsNone(cl.next_missing_step)

        with patch(review_patch, return_value=self._review_pkg_settings_patch()):
            http_pkg = self.client.get(f"/admin/supplier-offers/{oid}/review-package", headers=self._headers())
        self.assertEqual(http_pkg.status_code, 200)
        j = http_pkg.json()["conversion_closure"]
        self.assertTrue(all(j[k] for k in (
            "has_tour_bridge",
            "has_catalog_visible_tour",
            "has_active_execution_link",
            "supplier_offer_landing_routes_to_tour",
            "bot_deeplink_routes_to_tour",
            "central_catalog_contains_tour",
        )))
        self.assertIsNone(j["next_missing_step"])

    def test_moderation_approve_alone_does_not_materialize_bridge_or_tour(self) -> None:
        """Moderation approval without packaging approval does not create Tour/bridge (explicit gates)."""
        supplier = self.create_supplier()
        dep = datetime(2026, 12, 15, 8, 0, tzinfo=UTC)
        ret = datetime(2026, 12, 17, 18, 0, tzinfo=UTC)
        offer = self.create_supplier_offer(
            supplier,
            title="Neg Trip",
            description="Desc",
            marketing_summary="Sum",
            program_text="Prog",
            included_text="Inc",
            excluded_text="Exc",
            departure_datetime=dep,
            return_datetime=ret,
            seats_total=30,
            base_price=Decimal("99.00"),
            currency="EUR",
            sales_mode=TourSalesMode.PER_SEAT,
            lifecycle_status=SupplierOfferLifecycle.READY_FOR_MODERATION,
            packaging_status=SupplierOfferPackagingStatus.PACKAGING_GENERATED,
        )
        self.session.commit()
        oid = offer.id

        r = self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=self._headers())
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["lifecycle_status"], "approved")

        bridge_rows = self.session.scalar(
            select(func.count())
            .select_from(SupplierOfferTourBridge)
            .where(SupplierOfferTourBridge.supplier_offer_id == oid)
        )
        self.assertEqual(bridge_rows, 0)

        bad = self.client.post(f"/admin/supplier-offers/{oid}/tour-bridge", headers=self._headers(), json={})
        self.assertEqual(bad.status_code, 422, bad.text)

        review_patch = "app.services.supplier_offer_review_package_service.get_settings"
        with patch(review_patch, return_value=self._review_pkg_settings_patch()):
            rp = self.client.get(f"/admin/supplier-offers/{oid}/review-package", headers=self._headers())
        self.assertEqual(rp.status_code, 200, rp.text)
        cc = rp.json()["conversion_closure"]
        self.assertFalse(cc["has_tour_bridge"])
        self.assertEqual(cc["next_missing_step"], "approve_packaging")
