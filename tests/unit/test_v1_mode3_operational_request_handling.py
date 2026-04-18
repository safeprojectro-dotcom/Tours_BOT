"""V1: operational hints for admin custom-request API (read-side only)."""

from __future__ import annotations

import unittest
from datetime import UTC, date, datetime

from app.models.enums import (
    CustomMarketplaceRequestStatus,
    CustomMarketplaceRequestType,
    CustomRequestBookingBridgeStatus,
)
from app.schemas.custom_marketplace import CustomRequestBookingBridgeRead
from app.services.operational_custom_request_hints import (
    bridge_status_operational_label,
    build_operational_detail_hints,
    build_operational_list_hints,
    operational_is_terminal_status,
    operational_scan_summary_line,
)


class V1OperationalCustomRequestHintsTests(unittest.TestCase):
    def test_scan_line_includes_type_dates_route(self) -> None:
        line = operational_scan_summary_line(
            request_type=CustomMarketplaceRequestType.CUSTOM_ROUTE,
            travel_date_start=date(2026, 9, 1),
            travel_date_end=date(2026, 9, 3),
            group_size=40,
            route_notes="Timisoara to coast",
        )
        self.assertIn("Custom route", line)
        self.assertIn("2026-09-01", line)
        self.assertIn("group 40", line)
        self.assertIn("Timisoara", line)

    def test_terminal_flags(self) -> None:
        self.assertTrue(operational_is_terminal_status(CustomMarketplaceRequestStatus.CANCELLED))
        self.assertFalse(operational_is_terminal_status(CustomMarketplaceRequestStatus.OPEN))

    def test_list_hints_open_zero_proposals(self) -> None:
        h = build_operational_list_hints(
            status=CustomMarketplaceRequestStatus.OPEN,
            request_type=CustomMarketplaceRequestType.OTHER,
            travel_date_start=date(2026, 1, 1),
            travel_date_end=None,
            group_size=None,
            route_notes="Corp outing",
            proposed_supplier_response_count=0,
            selected_supplier_response_id=None,
        )
        self.assertFalse(h.is_terminal)
        self.assertEqual(h.proposed_supplier_response_count, 0)
        low = h.handling_hint.lower()
        self.assertNotIn("payment ready", low)
        self.assertNotIn("paid", low)

    def test_detail_hints_supplier_selected_no_bridge(self) -> None:
        d = build_operational_detail_hints(
            status=CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
            request_type=CustomMarketplaceRequestType.GROUP_TRIP,
            travel_date_start=date(2026, 6, 1),
            travel_date_end=None,
            group_size=12,
            route_notes="Day trip",
            proposed_supplier_response_count=1,
            selected_supplier_response_id=99,
            booking_bridge=None,
        )
        self.assertFalse(d.booking_bridge_present)
        self.assertIsNone(d.booking_bridge_operational_label)
        self.assertIn("no booking bridge", d.handling_hint.lower())
        self.assertIn("bridge", d.continuation_summary.lower())

    def test_detail_hints_with_ready_bridge(self) -> None:
        now = datetime.now(UTC)
        bridge = CustomRequestBookingBridgeRead(
            id=1,
            request_id=10,
            selected_supplier_response_id=99,
            user_id=5,
            tour_id=100,
            bridge_status=CustomRequestBookingBridgeStatus.READY,
            admin_note=None,
            created_at=now,
            updated_at=now,
        )
        d = build_operational_detail_hints(
            status=CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
            request_type=CustomMarketplaceRequestType.GROUP_TRIP,
            travel_date_start=date(2026, 6, 1),
            travel_date_end=None,
            group_size=12,
            route_notes="Day trip",
            proposed_supplier_response_count=1,
            selected_supplier_response_id=99,
            booking_bridge=bridge,
        )
        self.assertTrue(d.booking_bridge_present)
        self.assertIn("ready", (d.booking_bridge_operational_label or "").lower())
        self.assertIn("booking bridge:", d.handling_hint.lower())

    def test_bridge_labels_are_human_readable(self) -> None:
        lbl = bridge_status_operational_label(CustomRequestBookingBridgeStatus.PENDING_VALIDATION)
        self.assertIn("validation", lbl.lower())
        self.assertNotEqual(lbl, CustomRequestBookingBridgeStatus.PENDING_VALIDATION.value)


if __name__ == "__main__":
    unittest.main()
