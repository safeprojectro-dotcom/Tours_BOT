"""V4: follow-through posture vs customer progression evidence (admin read-side)."""

from __future__ import annotations

import unittest
from datetime import UTC, date, datetime

from app.models.enums import (
    CustomMarketplaceRequestStatus,
    CustomMarketplaceRequestType,
    CustomRequestBookingBridgeStatus,
)
from app.schemas.custom_marketplace import (
    CustomRequestBookingBridgeRead,
    OperationalCustomerProgressionEvidenceRead,
    OperationalFollowThroughPostureRead,
)
from app.services.operational_custom_request_hints import (
    build_operational_detail_hints,
    build_operational_list_hints,
)


class V4FollowThroughVisibilityTests(unittest.TestCase):
    def test_list_follow_through_one_liner(self) -> None:
        h = build_operational_list_hints(
            status=CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
            request_type=CustomMarketplaceRequestType.GROUP_TRIP,
            travel_date_start=date(2026, 6, 1),
            travel_date_end=None,
            group_size=None,
            route_notes="R",
            proposed_supplier_response_count=1,
            selected_supplier_response_id=1,
        )
        self.assertIn("Follow-through:", h.follow_through_one_liner)

    def test_commercial_without_bridge_stall(self) -> None:
        d = build_operational_detail_hints(
            status=CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
            request_type=CustomMarketplaceRequestType.GROUP_TRIP,
            travel_date_start=date(2026, 6, 1),
            travel_date_end=None,
            group_size=10,
            route_notes="Trip",
            proposed_supplier_response_count=1,
            selected_supplier_response_id=99,
            booking_bridge=None,
            commercial_resolution_kind=None,
        )
        self.assertEqual(
            d.follow_through_posture,
            OperationalFollowThroughPostureRead.COMMERCIAL_WITHOUT_BRIDGE,
        )
        self.assertEqual(
            d.customer_progression_evidence,
            OperationalCustomerProgressionEvidenceRead.NO_CUSTOMER_PATH_VISIBLE,
        )
        low = d.follow_through_summary.lower()
        self.assertIn("stall", low)
        self.assertNotIn("paid", low)
        self.assertNotIn("payment confirmed", low)

    def test_ready_bridge_path_no_booking_evidence(self) -> None:
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
            group_size=10,
            route_notes="Trip",
            proposed_supplier_response_count=1,
            selected_supplier_response_id=99,
            booking_bridge=bridge,
            commercial_resolution_kind=None,
        )
        self.assertEqual(
            d.follow_through_posture,
            OperationalFollowThroughPostureRead.PATH_MAY_EXIST_NO_PROGRESSION_EVIDENCE_HERE,
        )
        self.assertEqual(
            d.customer_progression_evidence,
            OperationalCustomerProgressionEvidenceRead.NO_BOOKING_OR_PAYMENT_EVIDENCE_IN_THIS_VIEW,
        )
        self.assertNotIn("customer has completed", d.follow_through_summary.lower())

    def test_customer_notified_milestone_not_completion(self) -> None:
        now = datetime.now(UTC)
        bridge = CustomRequestBookingBridgeRead(
            id=1,
            request_id=10,
            selected_supplier_response_id=99,
            user_id=5,
            tour_id=100,
            bridge_status=CustomRequestBookingBridgeStatus.CUSTOMER_NOTIFIED,
            admin_note=None,
            created_at=now,
            updated_at=now,
        )
        d = build_operational_detail_hints(
            status=CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
            request_type=CustomMarketplaceRequestType.GROUP_TRIP,
            travel_date_start=date(2026, 6, 1),
            travel_date_end=None,
            group_size=10,
            route_notes="Trip",
            proposed_supplier_response_count=1,
            selected_supplier_response_id=99,
            booking_bridge=bridge,
            commercial_resolution_kind=None,
        )
        self.assertEqual(
            d.follow_through_posture,
            OperationalFollowThroughPostureRead.NOTIFY_MILESTONE_NO_COMPLETION_EVIDENCE,
        )
        self.assertEqual(
            d.customer_progression_evidence,
            OperationalCustomerProgressionEvidenceRead.NOTIFICATION_MILESTONE_ONLY,
        )
        self.assertIn("not booking", d.follow_through_summary.lower())

    def test_inactive_bridge_stalled(self) -> None:
        now = datetime.now(UTC)
        bridge = CustomRequestBookingBridgeRead(
            id=1,
            request_id=10,
            selected_supplier_response_id=99,
            user_id=5,
            tour_id=100,
            bridge_status=CustomRequestBookingBridgeStatus.SUPERSEDED,
            admin_note=None,
            created_at=now,
            updated_at=now,
        )
        d = build_operational_detail_hints(
            status=CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
            request_type=CustomMarketplaceRequestType.GROUP_TRIP,
            travel_date_start=date(2026, 6, 1),
            travel_date_end=None,
            group_size=10,
            route_notes="Trip",
            proposed_supplier_response_count=1,
            selected_supplier_response_id=99,
            booking_bridge=bridge,
            commercial_resolution_kind=None,
        )
        self.assertEqual(
            d.follow_through_posture,
            OperationalFollowThroughPostureRead.BRIDGE_INACTIVE_STALLED,
        )
        self.assertEqual(
            d.customer_progression_evidence,
            OperationalCustomerProgressionEvidenceRead.NO_CUSTOMER_PATH_VISIBLE,
        )

    def test_terminal_posture(self) -> None:
        d = build_operational_detail_hints(
            status=CustomMarketplaceRequestStatus.CANCELLED,
            request_type=CustomMarketplaceRequestType.GROUP_TRIP,
            travel_date_start=date(2026, 6, 1),
            travel_date_end=None,
            group_size=10,
            route_notes="Trip",
            proposed_supplier_response_count=0,
            selected_supplier_response_id=None,
            booking_bridge=None,
            commercial_resolution_kind=None,
        )
        self.assertEqual(
            d.follow_through_posture,
            OperationalFollowThroughPostureRead.TERMINAL_CLOSED,
        )
        self.assertEqual(
            d.customer_progression_evidence,
            OperationalCustomerProgressionEvidenceRead.TERMINAL_NO_FURTHER_EVIDENCE_EXPECTED,
        )


if __name__ == "__main__":
    unittest.main()
