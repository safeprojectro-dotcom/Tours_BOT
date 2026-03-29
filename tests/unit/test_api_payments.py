from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus
from tests.unit.base import FoundationDBTestCase


class PaymentWebhookRouteTests(FoundationDBTestCase):
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
        self.original_secret = get_settings().payment_webhook_secret
        get_settings().payment_webhook_secret = "test-payment-secret"

        def override_get_db():
            yield self.session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()
        self.app.dependency_overrides.clear()
        get_settings().payment_webhook_secret = self.original_secret
        event.remove(self.session, "after_transaction_end", self._restart_savepoint)
        super().tearDown()

    def test_payment_webhook_confirms_payment_via_reconciliation_service(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="API-PAY-1",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 4, 10, 8, 0, tzinfo=UTC),
            sales_deadline=datetime(2026, 4, 9, 8, 0, tzinfo=UTC),
        )
        point = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime(2026, 4, 2, 12, 0, tzinfo=UTC),
        )
        payment = self.create_payment(
            order,
            provider="mockpay",
            external_payment_id="mockpay-api-1",
            status=PaymentStatus.AWAITING_PAYMENT,
        )
        self.session.commit()

        response = self.client.post(
            "/payments/webhooks/mockpay",
            content=self._body(
                {
                    "external_payment_id": payment.external_payment_id,
                    "status": "succeeded",
                    "amount": str(payment.amount),
                    "currency": payment.currency,
                    "payload": {"event": "payment.succeeded"},
                }
            ),
            headers=self._headers(
                {
                    "external_payment_id": payment.external_payment_id,
                    "status": "succeeded",
                    "amount": str(payment.amount),
                    "currency": payment.currency,
                    "payload": {"event": "payment.succeeded"},
                }
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "processed")
        self.assertEqual(response.json()["payment_status"], "paid")
        self.assertTrue(response.json()["payment_confirmed"])

        refreshed_order = self.session.get(type(order), order.id)
        refreshed_payment = self.session.get(type(payment), payment.id)
        assert refreshed_order is not None
        assert refreshed_payment is not None
        self.assertEqual(refreshed_order.booking_status, BookingStatus.CONFIRMED)
        self.assertEqual(refreshed_order.payment_status, PaymentStatus.PAID)
        self.assertEqual(refreshed_payment.status, PaymentStatus.PAID)

    def test_payment_webhook_rejects_invalid_signature(self) -> None:
        response = self.client.post(
            "/payments/webhooks/mockpay",
            content=self._body(
                {
                    "external_payment_id": "missing",
                    "status": "succeeded",
                }
            ),
            headers={"X-Payment-Signature": "bad-signature", "content-type": "application/json"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "invalid payment signature")

    def test_payment_webhook_rejects_unsupported_status(self) -> None:
        response = self.client.post(
            "/payments/webhooks/mockpay",
            content=self._body(
                {
                    "external_payment_id": "missing",
                    "status": "refunded",
                }
            ),
            headers=self._headers(
                {
                    "external_payment_id": "missing",
                    "status": "refunded",
                }
            ),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "unsupported payment status")

    def test_payment_webhook_returns_not_found_for_unknown_session(self) -> None:
        response = self.client.post(
            "/payments/webhooks/mockpay",
            content=self._body(
                {
                    "external_payment_id": "unknown-session",
                    "status": "succeeded",
                }
            ),
            headers=self._headers(
                {
                    "external_payment_id": "unknown-session",
                    "status": "succeeded",
                }
            ),
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "payment session not found or payload mismatch")

    def _body(self, payload: dict) -> bytes:
        return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

    def _headers(self, payload: dict) -> dict[str, str]:
        body = self._body(payload)
        secret = get_settings().payment_webhook_secret or ""
        signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return {
            "X-Payment-Signature": signature,
            "content-type": "application/json",
        }
