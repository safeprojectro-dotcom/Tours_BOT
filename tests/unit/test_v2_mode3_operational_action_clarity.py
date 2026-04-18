"""V2: operational action focus and bridge interpretation (admin read-side)."""

from __future__ import annotations

import unittest
from datetime import UTC, date, datetime

from app.models.enums import (
    CustomMarketplaceRequestStatus,
    CustomMarketplaceRequestType,
    CustomRequestBookingBridgeStatus,
)
from app.schemas.custom_marketplace import CustomRequestBookingBridgeRead, OperationalActionFocusRead
from app.services.operational_custom_request_hints import (
    build_operational_detail_hints,
    build_operational_list_hints,
)


class V2OperationalActionClarityTests(unittest.TestCase):
    def test_list_open_zero_proposals_awaits_supplier(self) -> None:
        h = build_operational_list_hints(
            status=CustomMarketplaceRequestStatus.OPEN,
            request_type=CustomMarketplaceRequestType.OTHER,
            travel_date_start=date(2026, 1, 1),
            travel_date_end=None,
            group_size=None,
            route_notes="Test",
            proposed_supplier_response_count=0,
            selected_supplier_response_id=None,
        )
        self.assertEqual(h.action_focus, OperationalActionFocusRead.AWAITING_SUPPLIER_PROPOSALS)
        self.assertTrue(h.needs_internal_ops_attention)

    def test_list_open_with_proposals_internal_review(self) -> None:
        h = build_operational_list_hints(
            status=CustomMarketplaceRequestStatus.OPEN,
            request_type=CustomMarketplaceRequestType.OTHER,
            travel_date_start=date(2026, 1, 1),
            travel_date_end=None,
            group_size=None,
            route_notes="Test",
            proposed_supplier_response_count=2,
            selected_supplier_response_id=None,
        )
        self.assertEqual(h.action_focus, OperationalActionFocusRead.INTERNAL_REVIEW_OR_RESOLUTION)

    def test_terminal_list_no_ops_attention(self) -> None:
        h = build_operational_list_hints(
            status=CustomMarketplaceRequestStatus.CANCELLED,
            request_type=CustomMarketplaceRequestType.OTHER,
            travel_date_start=date(2026, 1, 1),
            travel_date_end=None,
            group_size=None,
            route_notes="Test",
            proposed_supplier_response_count=0,
            selected_supplier_response_id=None,
        )
        self.assertEqual(h.action_focus, OperationalActionFocusRead.TERMINAL)
        self.assertFalse(h.needs_internal_ops_attention)

    def test_detail_ready_bridge_monitors_customer_not_internal(self) -> None:
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
        self.assertEqual(d.action_focus, OperationalActionFocusRead.MONITOR_CUSTOMER_CONTINUATION)
        self.assertFalse(d.needs_internal_ops_attention)
        self.assertIn("does not confirm payment", d.primary_action_hint.lower())
        self.assertIn("prep/payment", d.bridge_continuation_interpretation.lower())

    def test_detail_cancelled_bridge_reconcile(self) -> None:
        now = datetime.now(UTC)
        bridge = CustomRequestBookingBridgeRead(
            id=1,
            request_id=10,
            selected_supplier_response_id=99,
            user_id=5,
            tour_id=100,
            bridge_status=CustomRequestBookingBridgeStatus.CANCELLED,
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
        self.assertEqual(d.action_focus, OperationalActionFocusRead.RECONCILE_CLOSED_BRIDGE)
        self.assertTrue(d.needs_internal_ops_attention)
        low = d.primary_action_hint.lower()
        self.assertNotIn("payment ready", low)
        self.assertNotIn("customer has paid", low)


if __name__ == "__main__":
    unittest.main()
