"""S1C-2: Telegram delivery from supplier_notification_outbox (single-row, controlled)."""

from __future__ import annotations

import asyncio

from app.models.supplier_notification_outbox import SupplierNotificationOutbox
from app.repositories.supplier_notification_outbox import SupplierNotificationOutboxRepository
from app.services.supplier_notification_outbox_delivery_service import (
    SupplierNotificationOutboxDeliveryService,
    SupplierNotificationOutboxDeliveryStateConflictError,
    SupplierNotificationOutboxNotFoundError,
)
from app.services.supplier_notification_outbox_service import SupplierNotificationOutboxService
from tests.unit.base import FoundationDBTestCase


class _FakeTelegramDeliveryAdapter:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[int, str]] = []

    async def send_message(self, *, telegram_user_id: int, text: str) -> str | None:
        if self.fail:
            raise RuntimeError("telegram_upstream_failed")
        self.calls.append((telegram_user_id, text))
        return "4242"

    async def close(self) -> None:
        return None


async def _deliver_then_close(
    service: SupplierNotificationOutboxDeliveryService,
    session,
    *,
    outbox_id: int,
):
    try:
        return await service.deliver_one_by_id(session, outbox_id=outbox_id)
    finally:
        await service.close()


class SupplierNotificationOutboxS1C2ServiceTests(FoundationDBTestCase):
    def test_deliver_pending_success(self) -> None:
        fake = _FakeTelegramDeliveryAdapter()

        svc = SupplierNotificationOutboxDeliveryService(
            repository=SupplierNotificationOutboxRepository(),
            telegram_private_adapter=fake,
        )
        supplier = self.create_supplier()
        supplier.primary_telegram_user_id = 991_991991
        offer = self.create_supplier_offer(supplier)
        self.session.flush()

        enqueued = SupplierNotificationOutboxService().enqueue_supplier_offer_published(self.session, offer_id=offer.id)
        self.assertIsNotNone(enqueued)

        result = asyncio.run(_deliver_then_close(svc, self.session, outbox_id=enqueued.id))
        self.session.flush()

        row = self.session.get(SupplierNotificationOutbox, enqueued.id)

        assert row is not None

        self.assertEqual(result.outcome, "delivered")
        self.assertEqual(row.dispatch_status, "delivered")
        self.assertEqual(row.telegram_message_id, "4242")
        self.assertEqual(fake.calls[0][0], 991_991991)
        self.assertIn("Supplier showcase notification", fake.calls[0][1])
        self.assertIn(f"supplier_offer_id={offer.id}", fake.calls[0][1])

    def test_already_delivered_idempotent_without_second_send(self) -> None:
        fake = _FakeTelegramDeliveryAdapter()

        svc = SupplierNotificationOutboxDeliveryService(
            repository=SupplierNotificationOutboxRepository(),
            telegram_private_adapter=fake,
        )
        supplier = self.create_supplier()
        supplier.primary_telegram_user_id = 12
        offer = self.create_supplier_offer(supplier)
        self.session.flush()

        enqueued = SupplierNotificationOutboxService().enqueue_supplier_offer_published(self.session, offer_id=offer.id)
        self.assertIsNotNone(enqueued)

        assert enqueued is not None

        first = asyncio.run(_deliver_then_close(svc, self.session, outbox_id=enqueued.id))

        svc2 = SupplierNotificationOutboxDeliveryService(
            repository=SupplierNotificationOutboxRepository(),
            telegram_private_adapter=fake,
        )

        second = asyncio.run(_deliver_then_close(svc2, self.session, outbox_id=enqueued.id))

        self.assertEqual(first.outcome, "delivered")
        self.assertEqual(second.outcome, "already_delivered")
        self.assertEqual(len(fake.calls), 1)

    def test_telegram_error_marks_send_failed(self) -> None:
        fake = _FakeTelegramDeliveryAdapter(fail=True)
        svc = SupplierNotificationOutboxDeliveryService(
            repository=SupplierNotificationOutboxRepository(),
            telegram_private_adapter=fake,
        )
        supplier = self.create_supplier()
        supplier.primary_telegram_user_id = 77
        offer = self.create_supplier_offer(supplier)
        self.session.flush()

        enqueued = SupplierNotificationOutboxService().enqueue_supplier_offer_published(self.session, offer_id=offer.id)
        self.assertIsNotNone(enqueued)

        assert enqueued is not None

        result = asyncio.run(_deliver_then_close(svc, self.session, outbox_id=enqueued.id))

        row = self.session.get(SupplierNotificationOutbox, enqueued.id)

        assert row is not None

        self.assertEqual(result.outcome, "send_failed")
        self.assertEqual(row.dispatch_status, "send_failed")
        self.assertIn("telegram_upstream_failed", row.last_delivery_error or "")

    def test_contact_drift_blocks_send_without_telegram(self) -> None:
        fake = _FakeTelegramDeliveryAdapter()

        svc = SupplierNotificationOutboxDeliveryService(
            repository=SupplierNotificationOutboxRepository(),
            telegram_private_adapter=fake,
        )
        supplier = self.create_supplier()
        supplier.primary_telegram_user_id = 100
        offer = self.create_supplier_offer(supplier)
        self.session.flush()

        enqueued = SupplierNotificationOutboxService().enqueue_supplier_offer_published(self.session, offer_id=offer.id)
        self.assertIsNotNone(enqueued)

        assert enqueued is not None

        supplier.primary_telegram_user_id = 200
        self.session.flush()

        result = asyncio.run(_deliver_then_close(svc, self.session, outbox_id=enqueued.id))

        self.assertEqual(result.outcome, "send_failed")
        self.assertEqual(len(fake.calls), 0)

    def test_non_pending_raises_conflict(self) -> None:
        fake = _FakeTelegramDeliveryAdapter()
        svc = SupplierNotificationOutboxDeliveryService(
            repository=SupplierNotificationOutboxRepository(),
            telegram_private_adapter=fake,
        )
        supplier = self.create_supplier()
        supplier.primary_telegram_user_id = 1
        offer = self.create_supplier_offer(supplier)
        self.session.flush()

        row = SupplierNotificationOutbox(
            idempotency_key="manual:skipped",
            event_type="supplier_offer_published",
            channel="telegram_dm",
            supplier_id=supplier.id,
            supplier_offer_id=offer.id,
            telegram_user_id=None,
            contact_resolution_status="resolved_missing_contact",
            title="t",
            message="m",
            dispatch_status="skipped_no_target",
        )
        self.session.add(row)
        self.session.flush()

        with self.assertRaises(SupplierNotificationOutboxDeliveryStateConflictError):
            asyncio.run(_deliver_then_close(svc, self.session, outbox_id=row.id))

    def test_not_found_raises(self) -> None:
        svc = SupplierNotificationOutboxDeliveryService(
            telegram_private_adapter=_FakeTelegramDeliveryAdapter(),
        )

        with self.assertRaises(SupplierNotificationOutboxNotFoundError):
            asyncio.run(_deliver_then_close(svc, self.session, outbox_id=999_999999))
