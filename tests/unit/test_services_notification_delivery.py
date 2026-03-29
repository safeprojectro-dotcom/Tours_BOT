from __future__ import annotations

import asyncio
import unittest

from app.schemas.notification import (
    NotificationChannel,
    NotificationDeliveryStatus,
    NotificationDispatchRead,
    NotificationDispatchStatus,
    NotificationEventType,
    NotificationPayloadRead,
)
from app.services.notification_delivery import NotificationDeliveryService


class _FakeTelegramPrivateAdapter:
    def __init__(self, *, message_id: str | None = "123", error: Exception | None = None) -> None:
        self.message_id = message_id
        self.error = error
        self.calls: list[tuple[int, str]] = []
        self.closed = False

    async def send_message(self, *, telegram_user_id: int, text: str) -> str | None:
        self.calls.append((telegram_user_id, text))
        if self.error is not None:
            raise self.error
        return self.message_id

    async def close(self) -> None:
        self.closed = True


def _build_dispatch() -> NotificationDispatchRead:
    return NotificationDispatchRead(
        dispatch_key="telegram_private:payment_pending:101:en",
        channel=NotificationChannel.TELEGRAM_PRIVATE,
        status=NotificationDispatchStatus.PREPARED,
        payload=NotificationPayloadRead(
            event_type=NotificationEventType.PAYMENT_PENDING,
            order_id=101,
            user_id=11,
            telegram_user_id=900001,
            language_code="en",
            title="Payment pending",
            message="Your reservation expires soon.",
            metadata={"reservation_expires_at": "2026-04-05 12:00"},
        ),
    )


class NotificationDeliveryServiceTests(unittest.TestCase):
    def test_deliver_dispatch_sends_telegram_private_message(self) -> None:
        adapter = _FakeTelegramPrivateAdapter(message_id="456")
        service = NotificationDeliveryService(telegram_private_adapter=adapter)

        result = asyncio.run(service.deliver_dispatch(_build_dispatch()))

        self.assertEqual(result.status, NotificationDeliveryStatus.DELIVERED)
        self.assertEqual(result.provider_message_id, "456")
        self.assertIsNone(result.error_message)
        self.assertEqual(len(adapter.calls), 1)
        telegram_user_id, text = adapter.calls[0]
        self.assertEqual(telegram_user_id, 900001)
        self.assertIn("Payment pending", text)
        self.assertIn("Your reservation expires soon.", text)

    def test_deliver_dispatch_returns_failed_result_when_adapter_raises(self) -> None:
        adapter = _FakeTelegramPrivateAdapter(error=RuntimeError("telegram send failed"))
        service = NotificationDeliveryService(telegram_private_adapter=adapter)

        result = asyncio.run(service.deliver_dispatch(_build_dispatch()))

        self.assertEqual(result.status, NotificationDeliveryStatus.FAILED)
        self.assertIsNone(result.provider_message_id)
        self.assertEqual(result.error_message, "telegram send failed")
        self.assertEqual(len(adapter.calls), 1)
