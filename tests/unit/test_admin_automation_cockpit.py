"""A1-Block 1/2: GET /admin/automation-cockpit read-only foundation + commercial lanes."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import (
    SupplierOfferLifecycle,
    SupplierOfferPackagingStatus,
    SupplierOfferPaymentMode,
    TourSalesMode,
)
from tests.unit.base import FoundationDBTestCase


class AdminAutomationCockpitTests(FoundationDBTestCase):
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
        get_settings().admin_api_token = "test-admin-secret"

        def override_get_db():
            yield self.session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    @contextmanager
    def _review_console_settings(self, cfg: SimpleNamespace):
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=cfg),
            patch("app.services.supplier_offer_review_package_service.get_settings", return_value=cfg),
            patch("app.services.admin_publishing_console_service.get_settings", return_value=cfg),
        ):
            yield

    def tearDown(self) -> None:
        self.client.close()
        self.app.dependency_overrides.clear()
        get_settings().admin_api_token = self._original_admin
        event.remove(self.session, "after_transaction_end", self._restart_savepoint)
        super().tearDown()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer test-admin-secret"}

    def _settings(self) -> SimpleNamespace:
        return SimpleNamespace(
            telegram_bot_username="cockpitbot",
            telegram_mini_app_url="https://cockpit.example/mini",
            telegram_mini_app_short_name="appshort",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_token="tok",
        )

    def test_automation_cockpit_401_without_token(self) -> None:
        r = self.client.get("/admin/automation-cockpit")
        self.assertEqual(r.status_code, 401)

    def test_automation_cockpit_422_bad_include_queues(self) -> None:
        r = self.client.get(
            "/admin/automation-cockpit",
            params={"include_queues": "not_a_real_queue"},
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 422)

    def test_automation_cockpit_200_shape_and_safety(self) -> None:
        supplier = self.create_supplier()
        dep = datetime(2026, 12, 10, 8, 0, tzinfo=UTC)
        ret = datetime(2026, 12, 12, 18, 0, tzinfo=UTC)
        self.create_supplier_offer(
            supplier,
            title="Cockpit Row",
            program_text="Program.",
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
        cfg = self._settings()
        with self._review_console_settings(cfg):
            r = self.client.get("/admin/automation-cockpit", headers=self._headers())
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertIn("generated_at", data)
        self.assertIn("summary", data)
        self.assertIn("queues", data)
        self.assertIn("safety_summary", data)
        self.assertIn("source_note", data)

        summary = data["summary"]
        for key in (
            "total_cards",
            "queue_counts",
            "urgent_count",
            "needs_attention_count",
            "ready_count",
            "blocked_count",
            "future_disabled_count",
        ):
            self.assertIn(key, summary)

        codes = {q["queue_code"] for q in data["queues"]}
        expected_q = {
            "supplier_intake",
            "missing_info",
            "offer_readiness",
            "risk_conflict",
            "marketing_review",
            "publishing_queue",
            "catalog_conversion",
        }
        self.assertEqual(codes, expected_q)
        qcounts = data["summary"]["queue_counts"]
        for k in expected_q:
            self.assertIn(k, qcounts)

        allowed_kinds = {"safe_read", "future_disabled"}
        commercial_lanes = {"marketing_review", "publishing_queue", "catalog_conversion"}
        for q in data["queues"]:
            self.assertIn("total_count", q)
            self.assertIsInstance(q["cards"], list)
            for card in q["cards"]:
                self.assertIn(card["next_best_action_kind"], allowed_kinds)
                if card["next_best_action_kind"] == "future_disabled":
                    self.assertFalse(card["next_best_action_enabled"])
                self.assertNotEqual(card["next_best_action_kind"], "public_side_effect")
                self.assertNotEqual(card["next_best_action_kind"], "guarded_live_action")
                if q["queue_code"] in commercial_lanes:
                    self.assertIsNotNone(card.get("commercial_context"))
                    ctx = card["commercial_context"]
                    self.assertIn("fact_lock_note", ctx)
                    self.assertGreater(len(ctx["fact_lock_note"]), 20)
                meta = card.get("metadata") or {}
                if meta.get("kind") == "supplier_offer_initial":
                    self.assertIn("intake_validation", card)
                    self.assertIsNotNone(card["intake_validation"])
                    iv = card["intake_validation"]
                    self.assertIn("supplier_offer_id", iv)
                    self.assertIn("headline", iv)
                    self.assertEqual(iv.get("validation_version"), "a2_v1")
                    self.assertIn("clarification_draft", card)
                    self.assertIsNotNone(card["clarification_draft"])
                    cd = card["clarification_draft"]
                    self.assertEqual(cd.get("draft_version"), "a3b_v1")
                    self.assertIn("supplier_facing_asks", cd)
                    self.assertIn("internal_admin_tasks", cd)
                    self.assertIn("catalog_conversion_readiness", card)
                    cr = card["catalog_conversion_readiness"]
                    self.assertIsNotNone(cr)
                    self.assertEqual(cr.get("version"), "a6a_v1")
                if meta.get("kind") == "tour_promotion":
                    self.assertIsNone(card.get("intake_validation"))
                    self.assertIsNone(card.get("clarification_draft"))
                    self.assertIsNone(card.get("catalog_conversion_readiness"))

        safety = data["safety_summary"]
        for flag in (
            "read_only",
            "no_telegram_io",
            "no_publish_attempt",
            "no_scheduler",
            "no_auto_publish",
            "no_supplier_notification_send",
            "no_qr_token",
            "no_layer_a_mutation",
            "no_b11_change",
        ):
            self.assertTrue(safety[flag], flag)

    def test_automation_cockpit_include_queues_commercial_lane(self) -> None:
        cfg = self._settings()
        with self._review_console_settings(cfg):
            r = self.client.get(
                "/admin/automation-cockpit",
                headers=self._headers(),
                params={"include_queues": "marketing_review", "limit": 5},
            )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        for q in data["queues"]:
            if q["queue_code"] == "marketing_review":
                self.assertLessEqual(len(q["cards"]), 5)
            else:
                self.assertEqual(q["cards"], [])

    def test_automation_cockpit_include_queues_limits_cards_only(self) -> None:
        cfg = self._settings()
        with self._review_console_settings(cfg):
            r = self.client.get(
                "/admin/automation-cockpit",
                headers=self._headers(),
                params={"include_queues": "risk_conflict", "limit": 5},
            )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        for q in data["queues"]:
            if q["queue_code"] == "risk_conflict":
                self.assertLessEqual(len(q["cards"]), 5)
            else:
                self.assertEqual(q["cards"], [])
