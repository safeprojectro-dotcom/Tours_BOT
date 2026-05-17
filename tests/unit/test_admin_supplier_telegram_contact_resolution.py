"""S1B: admin read-only supplier Telegram contact resolution (no send)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import SupplierOfferTourBridgeKind, SupplierOfferTourBridgeStatus
from app.models.supplier import SupplierOfferExecutionLink
from app.models.supplier_offer_tour_bridge import SupplierOfferTourBridge
from tests.unit.base import FoundationDBTestCase


class AdminSupplierTelegramContactResolutionTests(FoundationDBTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.app = create_app()
        self._original_admin = get_settings().admin_api_token
        get_settings().admin_api_token = "test-admin-secret"

        def override_get_db():
            yield self.session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()
        self.app.dependency_overrides.clear()
        get_settings().admin_api_token = self._original_admin
        super().tearDown()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer test-admin-secret"}

    def test_supplier_with_primary_telegram(self) -> None:
        supplier = self.create_supplier()
        supplier.primary_telegram_user_id = 424242424
        self.session.flush()

        r = self.client.get(
            f"/admin/suppliers/{supplier.id}/supplier-telegram-contact-resolution",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["context_type"], "supplier")
        self.assertEqual(body["resolution_status"], "resolved_with_contact")
        self.assertTrue(body["telegram_contact_configured"])
        self.assertEqual(body["primary_telegram_user_id"], 424242424)
        self.assertEqual(body["supplier_id"], supplier.id)

    def test_supplier_missing_telegram(self) -> None:
        supplier = self.create_supplier()

        r = self.client.get(
            f"/admin/suppliers/{supplier.id}/supplier-telegram-contact-resolution",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["resolution_status"], "resolved_missing_contact")
        self.assertFalse(body["telegram_contact_configured"])
        self.assertIsNone(body["primary_telegram_user_id"])

    def test_supplier_inactive_warning(self) -> None:
        supplier = self.create_supplier(is_active=False)
        supplier.primary_telegram_user_id = 111
        self.session.flush()

        r = self.client.get(
            f"/admin/suppliers/{supplier.id}/supplier-telegram-contact-resolution",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertIn("s1b_supplier_not_active", r.json()["readiness_warnings"])

    def test_offer_owner_resolution(self) -> None:
        supplier = self.create_supplier()
        supplier.primary_telegram_user_id = 555
        offer = self.create_supplier_offer(supplier)
        self.session.flush()

        r = self.client.get(
            f"/admin/supplier-offers/{offer.id}/supplier-telegram-contact-resolution",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["context_type"], "supplier_offer")
        self.assertEqual(body["context_id"], offer.id)
        self.assertEqual(body["resolution_status"], "resolved_with_contact")
        self.assertEqual(body["primary_telegram_user_id"], 555)

    def test_tour_missing_relationship(self) -> None:
        tour = self.create_tour()
        r = self.client.get(
            f"/admin/tours/{tour.id}/supplier-telegram-contact-resolution",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["resolution_status"], "missing_relationship")
        self.assertFalse(body["telegram_contact_configured"])

    def test_tour_single_supplier_via_execution_link(self) -> None:
        supplier = self.create_supplier()
        supplier.primary_telegram_user_id = 9001
        offer = self.create_supplier_offer(supplier)
        tour = self.create_tour()
        self.session.add(SupplierOfferExecutionLink(supplier_offer_id=offer.id, tour_id=tour.id, link_status="active"))
        self.session.flush()

        r = self.client.get(
            f"/admin/tours/{tour.id}/supplier-telegram-contact-resolution",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["resolution_status"], "resolved_with_contact")
        self.assertEqual(body["supplier_id"], supplier.id)
        self.assertEqual(body["primary_telegram_user_id"], 9001)

    def test_tour_ambiguous_two_suppliers(self) -> None:
        s1 = self.create_supplier()
        s2 = self.create_supplier()
        o1 = self.create_supplier_offer(s1)
        o2 = self.create_supplier_offer(s2)
        tour = self.create_tour()
        self.session.add(SupplierOfferExecutionLink(supplier_offer_id=o1.id, tour_id=tour.id, link_status="active"))
        self.session.add(SupplierOfferExecutionLink(supplier_offer_id=o2.id, tour_id=tour.id, link_status="active"))
        self.session.flush()

        r = self.client.get(
            f"/admin/tours/{tour.id}/supplier-telegram-contact-resolution",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["resolution_status"], "ambiguous_suppliers")
        self.assertFalse(body["telegram_contact_configured"])
        self.assertIsNone(body["primary_telegram_user_id"])
        self.assertEqual(set(body["linked_supplier_ids"]), {s1.id, s2.id})
        self.assertIn("s1b_tour_maps_to_multiple_suppliers", body["readiness_warnings"])

    def test_order_delegates_to_tour(self) -> None:
        supplier = self.create_supplier()
        supplier.primary_telegram_user_id = 777
        offer = self.create_supplier_offer(supplier)
        tour = self.create_tour()
        bp = self.create_boarding_point(tour)
        user = self.create_user()
        order = self.create_order(user, tour, bp)
        self.session.add(
            SupplierOfferTourBridge(
                supplier_offer_id=offer.id,
                tour_id=tour.id,
                status=SupplierOfferTourBridgeStatus.ACTIVE.value,
                bridge_kind=SupplierOfferTourBridgeKind.LINKED_EXISTING_TOUR.value,
                created_by="test",
                source_packaging_status=offer.packaging_status.value,
                source_lifecycle_status=offer.lifecycle_status.value,
                packaging_snapshot_json={},
            ),
        )
        self.session.flush()

        r = self.client.get(
            f"/admin/orders/{order.id}/supplier-telegram-contact-resolution",
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["context_type"], "order")
        self.assertEqual(body["context_id"], order.id)
        self.assertEqual(body["primary_telegram_user_id"], 777)
        self.assertIn("order_tour", body["resolution_path_codes"])

    def test_order_not_found(self) -> None:
        r = self.client.get("/admin/orders/999999/supplier-telegram-contact-resolution", headers=self._headers())
        self.assertEqual(r.status_code, 404)

    def test_supplier_not_found(self) -> None:
        r = self.client.get("/admin/suppliers/999999/supplier-telegram-contact-resolution", headers=self._headers())
        self.assertEqual(r.status_code, 404)
