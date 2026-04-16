from __future__ import annotations

from app.models.enums import TourStatus
from app.schemas.payment import PaymentRead
from app.schemas.prepared import CatalogTourCardRead, LocalizedTourContentRead, PaymentSummaryRead
from app.services.catalog_preparation import CatalogPreparationService
from app.services.payment_summary import PaymentSummaryService
from tests.unit.base import FoundationDBTestCase


class SchemaSerializationTests(FoundationDBTestCase):
    def test_catalog_card_schema_serialization(self) -> None:
        tour = self.create_tour(title_default="Belgrade")
        self.create_translation(tour, language_code="ro", title="Belgrad")
        self.create_boarding_point(tour)

        cards = CatalogPreparationService().list_catalog_cards(
            self.session,
            language_code="ro",
            status=TourStatus.OPEN_FOR_SALE,
        )

        by_code = {c.code: c for c in cards}
        self.assertIn(tour.code, by_code)
        payload = by_code[tour.code].model_dump()
        self.assertEqual(payload["title"], "Belgrad")
        self.assertTrue(payload["localized_content"]["requested_language"] == "ro")
        self.assertEqual(payload["sales_mode_policy"]["effective_sales_mode"], "per_seat")

    def test_payment_summary_schema_serialization(self) -> None:
        user = self.create_user()
        tour = self.create_tour()
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        payment = self.create_payment(order, external_payment_id="schema-payment")

        summary = PaymentSummaryService().get_order_payment_summary(
            self.session,
            order_id=order.id,
        )

        self.assertIsNotNone(summary)
        assert summary is not None
        payload = summary.model_dump()
        self.assertEqual(payload["order"]["id"], order.id)
        self.assertEqual(payload["payments"][0]["id"], payment.id)
        self.assertEqual(payload["latest_payment"]["id"], payment.id)

    def test_payment_read_schema_from_orm(self) -> None:
        user = self.create_user()
        tour = self.create_tour()
        point = self.create_boarding_point(tour)
        order = self.create_order(user, tour, point)
        payment = self.create_payment(order, external_payment_id="orm-payment")

        schema = PaymentRead.model_validate(payment)

        self.assertEqual(schema.id, payment.id)
        self.assertEqual(schema.external_payment_id, "orm-payment")
