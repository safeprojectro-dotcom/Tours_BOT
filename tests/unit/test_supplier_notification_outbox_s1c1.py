"""S1C-1: supplier notification outbox enqueue (no Telegram send)."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models.enums import SupplierOfferTourBridgeKind, SupplierOfferTourBridgeStatus
from app.models.supplier import SupplierOfferExecutionLink
from app.models.supplier_notification_outbox import SupplierNotificationOutbox
from app.models.supplier_offer_tour_bridge import SupplierOfferTourBridge
from app.services.supplier_notification_outbox_service import SupplierNotificationOutboxService
from tests.unit.base import FoundationDBTestCase


class SupplierNotificationOutboxS1C1Tests(FoundationDBTestCase):
    def _count_rows(self) -> int:
        return int(self.session.scalar(select(func.count()).select_from(SupplierNotificationOutbox)) or 0)

    def test_enqueue_offer_pending_when_contact_configured(self) -> None:
        supplier = self.create_supplier()
        supplier.primary_telegram_user_id = 424242424
        offer = self.create_supplier_offer(supplier)
        self.session.flush()

        svc = SupplierNotificationOutboxService()
        before = self._count_rows()
        read = svc.enqueue_supplier_offer_published(self.session, offer_id=offer.id)
        self.session.flush()

        self.assertIsNotNone(read)
        self.assertEqual(read.dispatch_status, "pending_dispatch")
        self.assertEqual(read.telegram_user_id, 424242424)
        self.assertEqual(read.contact_resolution_status, "resolved_with_contact")
        self.assertEqual(read.event_type, "supplier_offer_published")
        self.assertEqual(read.supplier_offer_id, offer.id)
        self.assertEqual(read.supplier_id, supplier.id)
        self.assertEqual(self._count_rows(), before + 1)

    def test_enqueue_offer_skipped_when_telegram_missing(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        self.session.flush()

        svc = SupplierNotificationOutboxService()
        read = svc.enqueue_supplier_offer_published(self.session, offer_id=offer.id)
        self.session.flush()

        self.assertIsNotNone(read)
        self.assertEqual(read.dispatch_status, "skipped_no_target")
        self.assertIsNone(read.telegram_user_id)
        self.assertEqual(read.contact_resolution_status, "resolved_missing_contact")

    def test_enqueue_offer_idempotent(self) -> None:
        supplier = self.create_supplier()
        supplier.primary_telegram_user_id = 1
        offer = self.create_supplier_offer(supplier)
        self.session.flush()

        svc = SupplierNotificationOutboxService()
        first = svc.enqueue_supplier_offer_published(self.session, offer_id=offer.id)
        second = svc.enqueue_supplier_offer_published(self.session, offer_id=offer.id)
        self.session.flush()

        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertEqual(first.id, second.id)
        self.assertEqual(self._count_rows(), 1)

    def test_enqueue_offer_not_found(self) -> None:
        svc = SupplierNotificationOutboxService()
        self.assertIsNone(svc.enqueue_supplier_offer_published(self.session, offer_id=999999))

    def test_enqueue_order_ambiguous_skipped(self) -> None:
        s1 = self.create_supplier()
        s1.primary_telegram_user_id = 111
        s2 = self.create_supplier()
        s2.primary_telegram_user_id = 222
        o1 = self.create_supplier_offer(s1)
        o2 = self.create_supplier_offer(s2)
        tour = self.create_tour()
        bp = self.create_boarding_point(tour)
        user = self.create_user()
        order = self.create_order(user, tour, bp)
        self.session.add(SupplierOfferExecutionLink(supplier_offer_id=o1.id, tour_id=tour.id, link_status="active"))
        self.session.add(SupplierOfferExecutionLink(supplier_offer_id=o2.id, tour_id=tour.id, link_status="active"))
        self.session.flush()

        svc = SupplierNotificationOutboxService()
        read = svc.enqueue_supplier_order_created(self.session, order_id=order.id)
        self.session.flush()

        self.assertIsNotNone(read)
        self.assertEqual(read.dispatch_status, "skipped_no_target")
        self.assertEqual(read.contact_resolution_status, "ambiguous_suppliers")
        self.assertIsNone(read.telegram_user_id)
        self.assertEqual(read.order_id, order.id)

    def test_enqueue_order_pending_via_single_bridge(self) -> None:
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

        svc = SupplierNotificationOutboxService()
        read = svc.enqueue_supplier_order_created(self.session, order_id=order.id)
        self.session.flush()

        self.assertIsNotNone(read)
        self.assertEqual(read.dispatch_status, "pending_dispatch")
        self.assertEqual(read.telegram_user_id, 777)
        meta = read.payload_metadata or {}
        self.assertEqual(set(meta.keys()), {"order_id", "tour_id", "seats_count", "booking_status", "payment_status"})
        self.assertNotIn("user_id", meta)

    def test_enqueue_order_not_found(self) -> None:
        svc = SupplierNotificationOutboxService()
        self.assertIsNone(svc.enqueue_supplier_order_created(self.session, order_id=999999))
