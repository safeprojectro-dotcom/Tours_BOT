"""V3: operational transition visibility (selection → bridge → customer path)."""

from __future__ import annotations

import unittest
from datetime import UTC, date, datetime

from app.models.enums import (
    CommercialResolutionKind,
    CustomMarketplaceRequestStatus,
    CustomMarketplaceRequestType,
    CustomRequestBookingBridgeStatus,
)
from app.schemas.custom_marketplace import (
    CustomRequestBookingBridgeRead,
    OperationalCustomerPathVisibilityRead,
    OperationalSelectionLinkRead,
)
from app.services.operational_custom_request_hints import (
    build_operational_detail_hints,
    build_operational_list_hints,
)


class V3TransitionVisibilityTests(unittest.TestCase):
    def test_list_has_transition_one_liner(self) -> None:
        h = build_operational_list_hints(
            status=CustomMarketplaceRequestStatus.OPEN,
            request_type=CustomMarketplaceRequestType.OTHER,
            travel_date_start=date(2026, 1, 1),
            travel_date_end=None,
            group_size=None,
            route_notes="X",
            proposed_supplier_response_count=0,
            selected_supplier_response_id=None,
        )
        self.assertIn("Transition:", h.transition_stage_one_liner)
        self.assertIn("before commercial selection", h.transition_stage_one_liner.lower())

    def test_detail_open_pre_selection_enums(self) -> None:
        d = build_operational_detail_hints(
            status=CustomMarketplaceRequestStatus.UNDER_REVIEW,
            request_type=CustomMarketplaceRequestType.GROUP_TRIP,
            travel_date_start=date(2026, 6, 1),
            travel_date_end=None,
            group_size=10,
            route_notes="Trip",
            proposed_supplier_response_count=1,
            selected_supplier_response_id=None,
            booking_bridge=None,
            commercial_resolution_kind=None,
        )
        self.assertEqual(d.selection_link_state, OperationalSelectionLinkRead.PRE_COMMERCIAL_DECISION)
        self.assertEqual(d.customer_path_visibility, OperationalCustomerPathVisibilityRead.NOT_YET_APPLICABLE)
        self.assertIn("intake/review", d.transition_chain_summary.lower())
        self.assertNotIn("paid", d.transition_chain_summary.lower())

    def test_detail_selected_no_bridge(self) -> None:
        d = build_operational_detail_hints(
            status=CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
            request_type=CustomMarketplaceRequestType.GROUP_TRIP,
            travel_date_start=date(2026, 6, 1),
            travel_date_end=None,
            group_size=10,
            route_notes="Trip",
            proposed_supplier_response_count=1,
            selected_supplier_response_id=42,
            booking_bridge=None,
            commercial_resolution_kind=None,
        )
        self.assertEqual(d.selection_link_state, OperationalSelectionLinkRead.SELECTED_RESPONSE_ON_FILE)
        self.assertEqual(d.customer_path_visibility, OperationalCustomerPathVisibilityRead.NO_CUSTOMER_PATH_LINKED)
        self.assertIn("absent", d.transition_chain_summary.lower())

    def test_detail_selection_id_missing(self) -> None:
        d = build_operational_detail_hints(
            status=CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
            request_type=CustomMarketplaceRequestType.GROUP_TRIP,
            travel_date_start=date(2026, 6, 1),
            travel_date_end=None,
            group_size=10,
            route_notes="Trip",
            proposed_supplier_response_count=1,
            selected_supplier_response_id=None,
            booking_bridge=None,
            commercial_resolution_kind=None,
        )
        self.assertEqual(d.selection_link_state, OperationalSelectionLinkRead.SELECTION_DATA_INCOMPLETE)
        self.assertIn("reconcile", d.transition_chain_summary.lower())

    def test_detail_ready_bridge_customer_may_exist_not_paid(self) -> None:
        now = datetime.now(UTC)
        bridge = CustomRequestBookingBridgeRead(
            id=1,
            request_id=10,
            selected_supplier_response_id=42,
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
            selected_supplier_response_id=42,
            booking_bridge=bridge,
            commercial_resolution_kind=None,
        )
        self.assertEqual(
            d.customer_path_visibility,
            OperationalCustomerPathVisibilityRead.CUSTOMER_CONTINUATION_MAY_EXIST,
        )
        low = d.transition_chain_summary.lower()
        self.assertNotIn("payment confirmed", low)
        self.assertNotIn("has paid", low)

    def test_detail_terminal_includes_resolution_kind(self) -> None:
        d = build_operational_detail_hints(
            status=CustomMarketplaceRequestStatus.CLOSED_EXTERNAL,
            request_type=CustomMarketplaceRequestType.GROUP_TRIP,
            travel_date_start=date(2026, 6, 1),
            travel_date_end=None,
            group_size=10,
            route_notes="Trip",
            proposed_supplier_response_count=0,
            selected_supplier_response_id=None,
            booking_bridge=None,
            commercial_resolution_kind=CommercialResolutionKind.EXTERNAL_RECORD,
        )
        self.assertEqual(d.selection_link_state, OperationalSelectionLinkRead.CLOSED_RECORD)
        self.assertEqual(
            d.customer_path_visibility,
            OperationalCustomerPathVisibilityRead.TERMINAL_NO_FORWARD_PATH,
        )
        self.assertIn("external_record", d.transition_chain_summary)


if __name__ == "__main__":
    unittest.main()
