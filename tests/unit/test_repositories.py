from __future__ import annotations

from app.models.enums import BookingStatus, PaymentStatus, TourStatus
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.repositories.notification_outbox import NotificationOutboxRepository
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository
from app.repositories.tour import BoardingPointRepository, TourRepository, TourTranslationRepository
from app.repositories.user import UserRepository
from tests.unit.base import FoundationDBTestCase


class RepositoryTests(FoundationDBTestCase):
    def test_user_repository_get_by_telegram_user_id(self) -> None:
        user = self.create_user(telegram_user_id=555001)

        result = UserRepository().get_by_telegram_user_id(
            self.session,
            telegram_user_id=555001,
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.id, user.id)

    def test_tour_repository_get_by_code_and_list_by_status(self) -> None:
        matching = self.create_tour(code="BELGRADE-1", status=TourStatus.OPEN_FOR_SALE)
        self.create_tour(code="BUDAPEST-1", status=TourStatus.DRAFT)

        by_code = TourRepository().get_by_code(self.session, code="BELGRADE-1")
        locked = TourRepository().get_for_update(self.session, tour_id=matching.id)
        by_status = TourRepository().list_by_status(
            self.session,
            status=TourStatus.OPEN_FOR_SALE,
        )

        self.assertIsNotNone(by_code)
        self.assertIsNotNone(locked)
        assert by_code is not None
        assert locked is not None
        self.assertEqual(by_code.id, matching.id)
        self.assertEqual(locked.id, matching.id)
        ours = [tour for tour in by_status if tour.code == "BELGRADE-1"]
        self.assertEqual([tour.id for tour in ours], [matching.id])

    def test_translation_and_boarding_point_repositories(self) -> None:
        tour = self.create_tour()
        translation = self.create_translation(tour, language_code="ro", title="Titlu RO")
        point_1 = self.create_boarding_point(tour, time=__import__("datetime").time(6, 30))
        point_2 = self.create_boarding_point(tour, time=__import__("datetime").time(7, 0))

        fetched_translation = TourTranslationRepository().get_by_tour_and_language(
            self.session,
            tour_id=tour.id,
            language_code="ro",
        )
        boarding_points = BoardingPointRepository().list_by_tour(self.session, tour_id=tour.id)

        self.assertIsNotNone(fetched_translation)
        assert fetched_translation is not None
        self.assertEqual(fetched_translation.id, translation.id)
        self.assertEqual([point.id for point in boarding_points], [point_1.id, point_2.id])

    def test_order_repository_helpers(self) -> None:
        user = self.create_user()
        tour = self.create_tour()
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point, booking_status=BookingStatus.CONFIRMED)

        by_user = OrderRepository().list_by_user(self.session, user_id=user.id)
        by_status = OrderRepository().list_by_booking_status(
            self.session,
            booking_status=BookingStatus.CONFIRMED,
        )

        self.assertEqual([item.id for item in by_user], [order.id])
        self.assertEqual([item.id for item in by_status], [order.id])

    def test_payment_repository_helpers(self) -> None:
        user = self.create_user()
        tour = self.create_tour()
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        payment = self.create_payment(
            order,
            provider="stripe",
            external_payment_id="pi_123",
            status=PaymentStatus.PAID,
        )

        by_order = PaymentRepository().list_by_order(self.session, order_id=order.id)
        by_external = PaymentRepository().get_by_provider_external_id(
            self.session,
            provider="stripe",
            external_payment_id="pi_123",
        )

        self.assertEqual([item.id for item in by_order], [payment.id])
        self.assertIsNotNone(by_external)
        assert by_external is not None
        self.assertEqual(by_external.id, payment.id)

    def test_knowledge_base_repository_helpers(self) -> None:
        active_entry = self.create_knowledge_base_entry(category="faq", language_code="en", is_active=True)
        self.create_knowledge_base_entry(category="faq", language_code="en", is_active=False)
        self.create_knowledge_base_entry(category="policy", language_code="ro", is_active=True)

        active = KnowledgeBaseRepository().list_active(self.session, language_code="en")
        by_category = KnowledgeBaseRepository().list_by_category(
            self.session,
            category="faq",
            language_code="en",
        )

        self.assertEqual([item.id for item in active], [active_entry.id])
        self.assertEqual(len(by_category), 2)

    def test_notification_outbox_repository_helpers(self) -> None:
        user = self.create_user()
        tour = self.create_tour()
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        outbox = NotificationOutboxRepository().create(
            self.session,
            data={
                "dispatch_key": "telegram_private:payment_pending:1:en",
                "channel": "telegram_private",
                "event_type": "payment_pending",
                "order_id": order.id,
                "user_id": user.id,
                "telegram_user_id": user.telegram_user_id,
                "language_code": "en",
                "title": "Payment pending",
                "message": "Reminder message",
                "payload_metadata": {"order_id": order.id},
                "status": "pending",
            },
        )

        by_key = NotificationOutboxRepository().get_by_dispatch_key(
            self.session,
            dispatch_key="telegram_private:payment_pending:1:en",
        )
        pending = NotificationOutboxRepository().list_by_status(
            self.session,
            status="pending",
        )

        self.assertIsNotNone(by_key)
        assert by_key is not None
        self.assertEqual(by_key.id, outbox.id)
        self.assertEqual([item.id for item in pending], [outbox.id])
