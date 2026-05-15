"""B16D2B: prepare_conversion_chain execution service (no HTTP route)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from sqlalchemy import func, select

from app.models.admin_guarded_action import AdminGuardedActionAttempt, AdminGuardedActionStep
from app.models.enums import (
    AdminGuardedActionAttemptStatus,
    SupplierOfferLifecycle,
    SupplierOfferPackagingStatus,
    SupplierOfferPaymentMode,
    TourSalesMode,
    TourStatus,
)
from app.models.supplier import SupplierOfferExecutionLink
from app.models.tour import Tour
from app.services.admin_tour_write import AdminTourCatalogActivationStateError, AdminTourWriteService
from app.services.prepare_conversion_chain_execution_service import PrepareConversionChainExecutionService
from tests.unit.base import FoundationDBTestCase


class PrepareConversionChainExecutionServiceTests(FoundationDBTestCase):
    def _approved_offer(self, **overrides):
        s = self.create_supplier()
        dep = datetime.now(UTC) + timedelta(days=30)
        ret = dep + timedelta(days=2)
        base_kwargs = {
            "title": "Chain Offer",
            "description": "Long description for the offer.",
            "marketing_summary": "Short marketing blurb",
            "program_text": "Day 1: walk; day 2: rest",
            "included_text": "Meals, guide",
            "excluded_text": "Flights, tips",
            "departure_datetime": dep,
            "return_datetime": ret,
            "seats_total": 40,
            "base_price": Decimal("199.00"),
            "currency": "EUR",
            "sales_mode": TourSalesMode.PER_SEAT,
            "payment_mode": SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
            "lifecycle_status": SupplierOfferLifecycle.APPROVED,
            "packaging_status": SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH,
        }
        base_kwargs.update(overrides)
        return self.create_supplier_offer(s, **base_kwargs)

    def test_confirm_required_for_live_execution(self) -> None:
        o = self._approved_offer()
        self.session.flush()
        svc = PrepareConversionChainExecutionService()
        with self.assertRaises(ValueError) as ctx:
            svc.execute(
                self.session,
                supplier_offer_id=o.id,
                idempotency_key="live-needs-confirm",
                confirm=False,
                dry_run=False,
            )
        self.assertIn("confirm", str(ctx.exception).lower())

    def test_dry_run_does_not_create_audit_attempt(self) -> None:
        o = self._approved_offer()
        self.session.flush()
        before = self.session.scalar(select(func.count()).select_from(AdminGuardedActionAttempt))
        svc = PrepareConversionChainExecutionService()
        res = svc.execute(
            self.session,
            supplier_offer_id=o.id,
            idempotency_key="dry-no-audit",
            confirm=False,
            dry_run=True,
        )
        after = self.session.scalar(select(func.count()).select_from(AdminGuardedActionAttempt))
        self.assertEqual(before, after)
        self.assertEqual(res.dry_run, True)
        self.assertEqual(res.overall_status, "dry_run_preview")
        self.assertIsNone(res.attempt_id)
        self.assertEqual(len(res.steps), 3)

    def test_ineligible_returns_blocked_attempt(self) -> None:
        o = self._approved_offer(lifecycle_status=SupplierOfferLifecycle.DRAFT)
        self.session.flush()
        svc = PrepareConversionChainExecutionService()
        res = svc.execute(
            self.session,
            supplier_offer_id=o.id,
            idempotency_key="ineligible",
            confirm=True,
            dry_run=False,
        )
        self.assertEqual(res.overall_status, "blocked")
        self.assertIsNotNone(res.attempt_id)
        self.assertEqual(res.attempt_status, AdminGuardedActionAttemptStatus.FAILED.value)

    def test_precheck_replays_failed_without_new_attempt_or_steps(self) -> None:
        o = self._approved_offer(lifecycle_status=SupplierOfferLifecycle.DRAFT)
        self.session.flush()
        svc = PrepareConversionChainExecutionService()
        r1 = svc.execute(
            self.session,
            supplier_offer_id=o.id,
            idempotency_key="precheck-replay",
            confirm=True,
            dry_run=False,
        )
        self.assertEqual(r1.overall_status, "blocked")
        attempt_id = r1.attempt_id
        assert attempt_id is not None
        attempt_count_before = self.session.scalar(select(func.count()).select_from(AdminGuardedActionAttempt))
        step_count_before = self.session.scalar(
            select(func.count()).select_from(AdminGuardedActionStep).where(
                AdminGuardedActionStep.attempt_id == attempt_id,
            ),
        )

        r2 = svc.execute(
            self.session,
            supplier_offer_id=o.id,
            idempotency_key="precheck-replay",
            confirm=True,
            dry_run=False,
        )
        self.assertEqual(r2.attempt_id, attempt_id)
        self.assertEqual(r2.overall_status, "failed")
        self.assertIn("replay", (r2.message or "").lower())
        self.assertIn("idempotency", (r2.message or "").lower())
        attempt_count_after = self.session.scalar(select(func.count()).select_from(AdminGuardedActionAttempt))
        step_count_after = self.session.scalar(
            select(func.count()).select_from(AdminGuardedActionStep).where(
                AdminGuardedActionStep.attempt_id == attempt_id,
            ),
        )
        self.assertEqual(attempt_count_before, attempt_count_after)
        self.assertEqual(step_count_before, step_count_after)

    def test_happy_path_runs_bridge_catalog_execution_link(self) -> None:
        o = self._approved_offer()
        o.quality_warnings_json = {"items": ["low_res_cover"]}
        self.session.flush()
        svc = PrepareConversionChainExecutionService()
        res = svc.execute(
            self.session,
            supplier_offer_id=o.id,
            idempotency_key="happy-1",
            confirm=True,
            requested_by="unit:test",
            dry_run=False,
        )
        self.assertEqual(res.overall_status, "succeeded", (res.message, res.blockers))
        self.assertIsNotNone(res.tour_id)
        self.assertIsNotNone(res.execution_link_id)
        tour = self.session.get(Tour, res.tour_id)
        self.assertIsNotNone(tour)
        self.assertEqual(tour.status, TourStatus.OPEN_FOR_SALE)
        codes = [s.step_code for s in res.steps]
        self.assertEqual(
            codes,
            ["ensure_tour_bridge", "activate_tour_for_catalog", "ensure_active_execution_link"],
        )
        self.assertEqual({s.status for s in res.steps}, {"succeeded"})

    def test_idempotent_replay_after_success(self) -> None:
        o = self._approved_offer()
        self.session.flush()
        svc = PrepareConversionChainExecutionService()
        r1 = svc.execute(
            self.session,
            supplier_offer_id=o.id,
            idempotency_key="idem-1",
            confirm=True,
            dry_run=False,
        )
        self.assertEqual(r1.overall_status, "succeeded")
        tcount_before = self.session.scalar(select(func.count()).select_from(Tour))
        r2 = svc.execute(
            self.session,
            supplier_offer_id=o.id,
            idempotency_key="idem-1",
            confirm=True,
            dry_run=False,
        )
        self.assertEqual(r2.overall_status, "succeeded")
        self.assertEqual(r2.attempt_id, r1.attempt_id)
        self.assertIn("replay", (r2.message or "").lower())
        tcount_after = self.session.scalar(select(func.count()).select_from(Tour))
        self.assertEqual(tcount_before, tcount_after)

    def test_partial_failure_records_three_audit_steps_and_replays_without_extra_rows(self) -> None:
        o = self._approved_offer()
        self.session.flush()
        svc = PrepareConversionChainExecutionService()
        with patch.object(
            AdminTourWriteService,
            "activate_tour_for_catalog",
            side_effect=AdminTourCatalogActivationStateError("catalog boom"),
        ):
            r1 = svc.execute(
                self.session,
                supplier_offer_id=o.id,
                idempotency_key="partial-1",
                confirm=True,
                dry_run=False,
            )
        self.assertEqual(r1.overall_status, "partial_success")
        self.assertEqual(len(r1.steps), 3)
        self.assertEqual(r1.steps[0].step_code, "ensure_tour_bridge")
        self.assertEqual(r1.steps[0].status, "succeeded")
        self.assertEqual(r1.steps[1].step_code, "activate_tour_for_catalog")
        self.assertEqual(r1.steps[1].status, "failed")
        self.assertEqual(r1.steps[2].step_code, "ensure_active_execution_link")
        self.assertEqual(r1.steps[2].status, "skipped")
        self.assertEqual(r1.steps[2].detail.get("reason"), "previous_step_failed")

        attempt_id = r1.attempt_id
        assert attempt_id is not None
        step_count_before = self.session.scalar(
            select(func.count()).select_from(AdminGuardedActionStep).where(
                AdminGuardedActionStep.attempt_id == attempt_id,
            ),
        )
        tours_before = self.session.scalar(select(func.count()).select_from(Tour))
        links_before = self.session.scalar(select(func.count()).select_from(SupplierOfferExecutionLink))

        r2 = svc.execute(
            self.session,
            supplier_offer_id=o.id,
            idempotency_key="partial-1",
            confirm=True,
            dry_run=False,
        )
        self.assertEqual(r2.overall_status, "partial_success")
        self.assertEqual(r2.attempt_id, r1.attempt_id)
        self.assertIn("replay", (r2.message or "").lower())
        self.assertIn("idempotency", (r2.message or "").lower())
        self.assertEqual(len(r2.steps), 3)

        step_count_after = self.session.scalar(
            select(func.count()).select_from(AdminGuardedActionStep).where(
                AdminGuardedActionStep.attempt_id == attempt_id,
            ),
        )
        self.assertEqual(step_count_before, step_count_after)
        self.assertEqual(tours_before, self.session.scalar(select(func.count()).select_from(Tour)))
        self.assertEqual(links_before, self.session.scalar(select(func.count()).select_from(SupplierOfferExecutionLink)))

    def test_new_idempotency_key_after_partial_can_complete_chain(self) -> None:
        o = self._approved_offer()
        self.session.flush()
        svc = PrepareConversionChainExecutionService()
        with patch.object(
            AdminTourWriteService,
            "activate_tour_for_catalog",
            side_effect=AdminTourCatalogActivationStateError("catalog boom"),
        ):
            svc.execute(
                self.session,
                supplier_offer_id=o.id,
                idempotency_key="partial-1b",
                confirm=True,
                dry_run=False,
            )

        r2 = svc.execute(
            self.session,
            supplier_offer_id=o.id,
            idempotency_key="partial-2b",
            confirm=True,
            dry_run=False,
        )
        self.assertEqual(r2.overall_status, "succeeded")
        skipped_bridge = [s for s in r2.steps if s.step_code == "ensure_tour_bridge"][0]
        self.assertEqual(skipped_bridge.status, "skipped")
