"""W1: Mode 3 custom request message preparation (no outbox / no Layer A coupling)."""

from __future__ import annotations

from app.models.enums import CustomMarketplaceRequestStatus
from app.schemas.custom_marketplace import MiniAppCustomRequestCreate
from app.schemas.custom_request_notification import CustomRequestNotificationEventType
from app.services.custom_marketplace_request_service import CustomMarketplaceRequestService
from app.services.custom_request_notification_preparation import (
    CustomRequestNotificationPreparationService,
)
from tests.unit.base import FoundationDBTestCase


class CustomRequestNotificationPreparationW1Tests(FoundationDBTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.svc = CustomMarketplaceRequestService()
        self.prep = CustomRequestNotificationPreparationService()

    def test_request_recorded_open_only(self) -> None:
        self.create_user(telegram_user_id=310_001, preferred_language="ro")
        self.session.commit()
        row = self.svc.create_from_mini_app(
            self.session,
            payload=MiniAppCustomRequestCreate(
                telegram_user_id=310_001,
                request_type="custom_route",
                travel_date_start="2026-11-01",
                route_notes="Test route notes for notification prep",
            ),
        )
        self.session.commit()
        payload = self.prep.prepare(
            self.session,
            request_id=row.id,
            event_type=CustomRequestNotificationEventType.REQUEST_RECORDED,
            language_code="ro",
        )
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload.preparation_scope, "message_preparation_only")
        self.assertEqual(payload.event_type, CustomRequestNotificationEventType.REQUEST_RECORDED)
        self.assertIn(str(row.id), payload.message)
        self.assertNotIn("plată confirmată", payload.message.lower())
        self.assertNotIn("operational_hints", payload.message.lower())

    def test_recorded_rejected_when_not_open(self) -> None:
        self.create_user(telegram_user_id=310_002)
        self.session.commit()
        row = self.svc.create_from_mini_app(
            self.session,
            payload=MiniAppCustomRequestCreate(
                telegram_user_id=310_002,
                request_type="other",
                travel_date_start="2026-11-02",
                route_notes="Notes here",
            ),
        )
        row.status = CustomMarketplaceRequestStatus.UNDER_REVIEW
        self.session.commit()
        payload = self.prep.prepare(
            self.session,
            request_id=row.id,
            event_type=CustomRequestNotificationEventType.REQUEST_RECORDED,
        )
        self.assertIsNone(payload)

    def test_under_review_when_status_matches(self) -> None:
        self.create_user(telegram_user_id=310_003)
        self.session.commit()
        row = self.svc.create_from_mini_app(
            self.session,
            payload=MiniAppCustomRequestCreate(
                telegram_user_id=310_003,
                request_type="group_trip",
                travel_date_start="2026-11-03",
                route_notes="Group trip",
            ),
        )
        row.status = CustomMarketplaceRequestStatus.UNDER_REVIEW
        self.session.commit()
        payload = self.prep.prepare(
            self.session,
            request_id=row.id,
            event_type=CustomRequestNotificationEventType.REQUEST_UNDER_REVIEW,
        )
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertIn("review", payload.message.lower())
        self.assertNotIn("payment is ready", payload.message.lower())

    def test_app_followup_requires_flag_and_supplier_selected(self) -> None:
        self.create_user(telegram_user_id=310_004)
        self.session.commit()
        row = self.svc.create_from_mini_app(
            self.session,
            payload=MiniAppCustomRequestCreate(
                telegram_user_id=310_004,
                request_type="custom_route",
                travel_date_start="2026-11-04",
                route_notes="Route",
            ),
        )
        self.session.commit()
        self.assertIsNone(
            self.prep.prepare(
                self.session,
                request_id=row.id,
                event_type=CustomRequestNotificationEventType.REQUEST_APP_FOLLOWUP_MAY_EXIST,
                app_next_step_maybe_available=False,
            )
        )
        self.assertIsNone(
            self.prep.prepare(
                self.session,
                request_id=row.id,
                event_type=CustomRequestNotificationEventType.REQUEST_APP_FOLLOWUP_MAY_EXIST,
                app_next_step_maybe_available=None,
            )
        )
        row.status = CustomMarketplaceRequestStatus.SUPPLIER_SELECTED
        self.session.commit()
        payload = self.prep.prepare(
            self.session,
            request_id=row.id,
            event_type=CustomRequestNotificationEventType.REQUEST_APP_FOLLOWUP_MAY_EXIST,
            app_next_step_maybe_available=True,
        )
        self.assertIsNotNone(payload)
        assert payload is not None
        low = payload.message.lower()
        self.assertIn("does not mean payment", low)
        self.assertIn("my requests", low)

    def test_selection_recorded_when_supplier_selected(self) -> None:
        self.create_user(telegram_user_id=310_006)
        self.session.commit()
        row = self.svc.create_from_mini_app(
            self.session,
            payload=MiniAppCustomRequestCreate(
                telegram_user_id=310_006,
                request_type="custom_route",
                travel_date_start="2026-11-06",
                route_notes="Selection recorded prep",
            ),
        )
        row.status = CustomMarketplaceRequestStatus.SUPPLIER_SELECTED
        self.session.commit()
        payload = self.prep.prepare(
            self.session,
            request_id=row.id,
            event_type=CustomRequestNotificationEventType.REQUEST_SELECTION_RECORDED,
            language_code="en",
        )
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload.event_type, CustomRequestNotificationEventType.REQUEST_SELECTION_RECORDED)
        low = payload.message.lower()
        self.assertIn("not a confirmed booking", low)
        self.assertNotIn("we sent you", low)
        self.assertNotIn("push", low)

    def test_selection_recorded_rejected_when_open(self) -> None:
        self.create_user(telegram_user_id=310_007)
        self.session.commit()
        row = self.svc.create_from_mini_app(
            self.session,
            payload=MiniAppCustomRequestCreate(
                telegram_user_id=310_007,
                request_type="other",
                travel_date_start="2026-11-07",
                route_notes="Open",
            ),
        )
        self.session.commit()
        self.assertIsNone(
            self.prep.prepare(
                self.session,
                request_id=row.id,
                event_type=CustomRequestNotificationEventType.REQUEST_SELECTION_RECORDED,
            )
        )

    def test_closed_terminal(self) -> None:
        self.create_user(telegram_user_id=310_005)
        self.session.commit()
        row = self.svc.create_from_mini_app(
            self.session,
            payload=MiniAppCustomRequestCreate(
                telegram_user_id=310_005,
                request_type="other",
                travel_date_start="2026-11-05",
                route_notes="Closed test notes",
            ),
        )
        row.status = CustomMarketplaceRequestStatus.CANCELLED
        self.session.commit()
        payload = self.prep.prepare(
            self.session,
            request_id=row.id,
            event_type=CustomRequestNotificationEventType.REQUEST_CLOSED,
        )
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertIn("closed", payload.message.lower())
        self.assertNotIn("confirmed booking", payload.message.lower())

