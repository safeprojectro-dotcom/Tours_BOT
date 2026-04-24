"""Unit tests for Phase 7.1 / Step 2 — tour sales mode policy (service layer only)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from pydantic import ValidationError

from app.models.enums import TourSalesMode, TourStatus
from app.schemas.tour_sales_mode_policy import CatalogActionabilityState, TourSalesModePolicyRead
from app.services.tour_sales_mode_policy import TourSalesModePolicyService
from tests.unit.base import FoundationDBTestCase


class TourSalesModePolicyTests(FoundationDBTestCase):
    def test_per_seat_policy_output(self) -> None:
        p = TourSalesModePolicyService.policy_for_sales_mode(TourSalesMode.PER_SEAT)
        self.assertIsInstance(p, TourSalesModePolicyRead)
        self.assertEqual(p.effective_sales_mode, TourSalesMode.PER_SEAT)
        self.assertTrue(p.per_seat_self_service_allowed)
        self.assertFalse(p.direct_customer_booking_blocked_or_deferred)
        self.assertFalse(p.operator_path_required)
        self.assertTrue(p.mini_app_catalog_reservation_allowed)
        self.assertIsNone(p.catalog_charter_fixed_seats_count)
        self.assertEqual(p.catalog_actionability_state, CatalogActionabilityState.BOOKABLE)

    def test_full_bus_policy_output(self) -> None:
        p = TourSalesModePolicyService.policy_for_sales_mode(TourSalesMode.FULL_BUS)
        self.assertEqual(p.effective_sales_mode, TourSalesMode.FULL_BUS)
        self.assertFalse(p.per_seat_self_service_allowed)
        self.assertTrue(p.direct_customer_booking_blocked_or_deferred)
        self.assertTrue(p.operator_path_required)
        self.assertFalse(p.mini_app_catalog_reservation_allowed)
        self.assertIsNone(p.catalog_charter_fixed_seats_count)
        self.assertEqual(p.catalog_actionability_state, CatalogActionabilityState.ASSISTED_ONLY)

    def test_large_seat_count_does_not_imply_full_bus(self) -> None:
        """Policy follows `sales_mode` only — never seat totals."""
        tour = self.create_tour(
            code="POL-PER-SEAT-BIG",
            status=TourStatus.OPEN_FOR_SALE,
            seats_total=80,
            seats_available=80,
            sales_mode=TourSalesMode.PER_SEAT,
        )
        self.session.commit()
        p = TourSalesModePolicyService.policy_for_tour(tour)
        self.assertEqual(p.effective_sales_mode, TourSalesMode.PER_SEAT)
        self.assertTrue(p.per_seat_self_service_allowed)

    def test_small_seat_total_still_full_bus_when_mode_full_bus(self) -> None:
        tour = self.create_tour(
            code="POL-FULL-SMALL",
            status=TourStatus.OPEN_FOR_SALE,
            seats_total=1,
            seats_available=1,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        self.session.commit()
        p = TourSalesModePolicyService.policy_for_tour(tour)
        self.assertEqual(p.effective_sales_mode, TourSalesMode.FULL_BUS)
        self.assertFalse(p.per_seat_self_service_allowed)
        self.assertTrue(p.operator_path_required)

    def test_policy_for_catalog_tour_full_bus_virgin_allows_mini_app_hold(self) -> None:
        tour = self.create_tour(
            code="POL-CAT-VIRGIN",
            status=TourStatus.OPEN_FOR_SALE,
            seats_total=30,
            seats_available=30,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        self.session.commit()
        p = TourSalesModePolicyService.policy_for_catalog_tour(tour)
        self.assertTrue(p.mini_app_catalog_reservation_allowed)
        self.assertEqual(p.catalog_charter_fixed_seats_count, 30)
        self.assertEqual(p.catalog_actionability_state, CatalogActionabilityState.BOOKABLE)

    def test_policy_for_catalog_tour_full_bus_partial_blocks_mini_app_hold(self) -> None:
        tour = self.create_tour(
            code="POL-CAT-PARTIAL",
            status=TourStatus.OPEN_FOR_SALE,
            seats_total=30,
            seats_available=29,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        self.session.commit()
        p = TourSalesModePolicyService.policy_for_catalog_tour(tour)
        self.assertFalse(p.mini_app_catalog_reservation_allowed)
        self.assertIsNone(p.catalog_charter_fixed_seats_count)
        self.assertEqual(p.catalog_actionability_state, CatalogActionabilityState.ASSISTED_ONLY)

    def test_policy_for_catalog_tour_full_bus_zero_seats_is_blocked(self) -> None:
        tour = self.create_tour(
            code="POL-CAT-ZERO",
            status=TourStatus.OPEN_FOR_SALE,
            seats_total=0,
            seats_available=0,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        self.session.commit()
        p = TourSalesModePolicyService.policy_for_catalog_tour(tour)
        self.assertFalse(p.mini_app_catalog_reservation_allowed)
        self.assertIsNone(p.catalog_charter_fixed_seats_count)
        self.assertEqual(p.catalog_actionability_state, CatalogActionabilityState.BLOCKED)

    def test_policy_for_catalog_tour_full_bus_sold_out_is_view_only(self) -> None:
        tour = self.create_tour(
            code="POL-CAT-SOLDOUT",
            status=TourStatus.OPEN_FOR_SALE,
            seats_total=30,
            seats_available=0,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        self.session.commit()
        p = TourSalesModePolicyService.policy_for_catalog_tour(tour)
        self.assertFalse(p.mini_app_catalog_reservation_allowed)
        self.assertIsNone(p.catalog_charter_fixed_seats_count)
        self.assertEqual(p.catalog_actionability_state, CatalogActionabilityState.VIEW_ONLY)

    def test_policy_for_catalog_tour_full_bus_invalid_snapshot_is_blocked(self) -> None:
        invalid_snapshot = SimpleNamespace(
            sales_mode=TourSalesMode.FULL_BUS,
            seats_total=20,
            seats_available=25,
        )
        p = TourSalesModePolicyService.policy_for_catalog_tour(invalid_snapshot)
        self.assertFalse(p.mini_app_catalog_reservation_allowed)
        self.assertIsNone(p.catalog_charter_fixed_seats_count)
        self.assertEqual(p.catalog_actionability_state, CatalogActionabilityState.BLOCKED)

    def test_default_orm_tour_is_per_seat_policy(self) -> None:
        """Tours without explicit `sales_mode` in factory still get PER_SEAT policy (DB + ORM default)."""
        tour = self.create_tour(code="POL-DEFAULT-MODE")
        self.assertEqual(tour.sales_mode, TourSalesMode.PER_SEAT)
        p = TourSalesModePolicyService.policy_for_tour(tour)
        self.assertEqual(p.effective_sales_mode, TourSalesMode.PER_SEAT)
        self.assertTrue(p.per_seat_self_service_allowed)

    def test_policy_read_model_is_frozen(self) -> None:
        p = TourSalesModePolicyService.policy_for_sales_mode(TourSalesMode.PER_SEAT)
        with self.assertRaises(ValidationError):
            p.effective_sales_mode = TourSalesMode.FULL_BUS  # type: ignore[misc]

    def test_core_reservation_creation_unwired_to_sales_mode_policy(self) -> None:
        """Shared booking engine stays free of sales-mode policy; channel layers gate (Mini App booking, private bot)."""
        root = Path(__file__).resolve().parents[2]
        text = (root / "app/services/reservation_creation.py").read_text(encoding="utf-8")
        self.assertNotIn(
            "tour_sales_mode_policy",
            text,
            msg="reservation_creation must not import sales-mode policy",
        )
