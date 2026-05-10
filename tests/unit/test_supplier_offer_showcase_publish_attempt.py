"""B13D: supplier_offer_showcase_publish_attempts repository and service (foundation only)."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.models.enums import (
    SupplierOfferShowcasePublishActorSurface,
    SupplierOfferShowcasePublishAttemptStatus,
)
from app.repositories.supplier_offer_showcase_publish_attempt import (
    SupplierOfferShowcasePublishAttemptRepository,
)
from app.services.showcase_channel_adapter import TELEGRAM_SHOWCASE_PROVIDER
from app.services.supplier_offer_showcase_publish_attempt_service import (
    SupplierOfferShowcasePublishAttemptService,
)
from tests.unit.base import FoundationDBTestCase


class SupplierOfferShowcasePublishAttemptTests(FoundationDBTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.service = SupplierOfferShowcasePublishAttemptService()

    def test_create_and_transition_happy_path(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        attempt = self.service.create_requested_attempt(
            self.session,
            supplier_offer_id=offer.id,
            provider=TELEGRAM_SHOWCASE_PROVIDER,
            actor_surface=SupplierOfferShowcasePublishActorSurface.HTTP_ADMIN,
            channel_ref="-100123",
            requested_by="admin:test",
            idempotency_key="idem-1",
            payload_fingerprint="sha256:abc",
        )
        self.assertEqual(attempt.status, SupplierOfferShowcasePublishAttemptStatus.REQUESTED)
        self.assertEqual(attempt.provider, TELEGRAM_SHOWCASE_PROVIDER)

        self.service.mark_provider_sent(self.session, attempt_id=attempt.id)
        self.session.refresh(attempt)
        self.assertEqual(attempt.status, SupplierOfferShowcasePublishAttemptStatus.PROVIDER_SENT)

        self.service.mark_persisted(
            self.session,
            attempt_id=attempt.id,
            showcase_chat_id="-100123",
            showcase_message_id=42,
        )
        self.session.refresh(attempt)
        self.assertEqual(attempt.status, SupplierOfferShowcasePublishAttemptStatus.PERSISTED)
        self.assertEqual(attempt.showcase_chat_id, "-100123")
        self.assertEqual(attempt.showcase_message_id, 42)

    def test_mark_failed_and_list_for_offer(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        a1 = self.service.create_requested_attempt(
            self.session,
            supplier_offer_id=offer.id,
            provider=TELEGRAM_SHOWCASE_PROVIDER,
            actor_surface=SupplierOfferShowcasePublishActorSurface.TELEGRAM_BOT,
            requested_by="telegram:999",
        )
        self.service.mark_failed(
            self.session,
            attempt_id=a1.id,
            error_code="tg_timeout",
            error_message="upstream timeout",
            retryable_failure=True,
        )
        self.session.refresh(a1)
        self.assertEqual(a1.status, SupplierOfferShowcasePublishAttemptStatus.FAILED)
        self.assertEqual(a1.error_code, "tg_timeout")
        self.assertTrue(a1.retryable_failure)

        a2 = self.service.create_requested_attempt(
            self.session,
            supplier_offer_id=offer.id,
            provider=TELEGRAM_SHOWCASE_PROVIDER,
            actor_surface=SupplierOfferShowcasePublishActorSurface.HTTP_ADMIN,
        )
        repo = SupplierOfferShowcasePublishAttemptRepository()
        rows = repo.list_for_offer(self.session, supplier_offer_id=offer.id, limit=10)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].id, a2.id)
        self.assertEqual(rows[1].id, a1.id)

    def test_list_attempts_review_read_maps_rows(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        a1 = self.service.create_requested_attempt(
            self.session,
            supplier_offer_id=offer.id,
            provider=TELEGRAM_SHOWCASE_PROVIDER,
            actor_surface=SupplierOfferShowcasePublishActorSurface.TELEGRAM_BOT,
            requested_by="telegram:42",
            channel_ref="-1001",
        )
        self.service.mark_failed(
            self.session,
            attempt_id=a1.id,
            error_code="e_code",
            error_message="oops",
            retryable_failure=False,
        )
        self.session.flush()
        read = self.service.list_attempts_review_read(self.session, supplier_offer_id=offer.id)
        self.assertEqual(read.total_returned, 1)
        self.assertEqual(len(read.items), 1)
        item = read.items[0]
        self.assertEqual(item.id, a1.id)
        self.assertEqual(item.status, "failed")
        self.assertEqual(item.actor_surface, "telegram_bot")
        self.assertEqual(item.requested_by, "telegram:42")
        self.assertEqual(item.error_code, "e_code")
        self.assertEqual(item.error_message, "oops")

    def test_mark_by_id_missing_returns_none(self) -> None:
        self.assertIsNone(self.service.mark_provider_sent(self.session, attempt_id=999_999_999))
        self.assertIsNone(
            self.service.mark_persisted(
                self.session,
                attempt_id=999_999_999,
                showcase_chat_id="x",
                showcase_message_id=1,
            ),
        )
        self.assertIsNone(
            self.service.mark_failed(self.session, attempt_id=999_999_999, error_code="x"),
        )

    def test_offer_delete_restricted_when_publish_attempts_exist(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        self.service.create_requested_attempt(
            self.session,
            supplier_offer_id=offer.id,
            provider=TELEGRAM_SHOWCASE_PROVIDER,
            actor_surface=SupplierOfferShowcasePublishActorSurface.HTTP_ADMIN,
        )
        savepoint = self.session.begin_nested()
        self.session.delete(offer)
        with self.assertRaises(IntegrityError):
            self.session.flush()
        savepoint.rollback()

    def test_offer_delete_succeeds_after_attempts_removed(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        attempt = self.service.create_requested_attempt(
            self.session,
            supplier_offer_id=offer.id,
            provider=TELEGRAM_SHOWCASE_PROVIDER,
            actor_surface=SupplierOfferShowcasePublishActorSurface.HTTP_ADMIN,
        )
        self.session.delete(attempt)
        self.session.flush()
        self.session.delete(offer)
        self.session.flush()
