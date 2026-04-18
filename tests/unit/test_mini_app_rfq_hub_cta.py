"""Track 5d: My Requests hub — pure CTA and label helpers (no Flet)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.models.enums import CustomMarketplaceRequestStatus, CustomRequestBookingBridgeStatus
from app.schemas.mini_app import MiniAppBookingFacadeState, MiniAppBookingPrimaryCta

from mini_app.rfq_hub_cta import (
    DetailPrimaryCtaKind,
    detail_context_line_keys,
    pick_booking_for_bridge_tour,
    request_status_lists_action_followup,
    request_status_user_label,
    resolve_detail_primary_cta,
)


def _booking_item(*, code: str, facade: MiniAppBookingFacadeState, order_id: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        summary=SimpleNamespace(
            tour=SimpleNamespace(code=code, localized_content=SimpleNamespace(title="T")),
            order=SimpleNamespace(id=order_id),
        ),
        facade_state=facade,
        primary_cta=MiniAppBookingPrimaryCta.PAY_NOW,
    )


class RfqHubCtaTests(unittest.TestCase):
    def test_list_followup_hint_statuses(self) -> None:
        self.assertTrue(request_status_lists_action_followup(CustomMarketplaceRequestStatus.SUPPLIER_SELECTED))
        self.assertTrue(request_status_lists_action_followup(CustomMarketplaceRequestStatus.CLOSED_ASSISTED))
        self.assertFalse(request_status_lists_action_followup(CustomMarketplaceRequestStatus.OPEN))
        self.assertFalse(request_status_lists_action_followup(CustomMarketplaceRequestStatus.UNDER_REVIEW))

    def test_pick_booking_prefers_active_hold(self) -> None:
        items = [
            _booking_item(code="A", facade=MiniAppBookingFacadeState.CONFIRMED, order_id=1),
            _booking_item(code="X", facade=MiniAppBookingFacadeState.ACTIVE_TEMPORARY_RESERVATION, order_id=2),
            _booking_item(code="X", facade=MiniAppBookingFacadeState.EXPIRED_TEMPORARY_RESERVATION, order_id=3),
        ]
        picked = pick_booking_for_bridge_tour(items, "X")
        assert picked is not None
        self.assertEqual(picked.summary.order.id, 2)

    def test_resolve_payment_over_self_service(self) -> None:
        prep = SimpleNamespace(self_service_available=True, tour_code="T")
        elig = SimpleNamespace(payment_entry_allowed=True, order_id=99)
        kind, oid = resolve_detail_primary_cta(
            prep=prep,
            payment_elig=elig,
            hold_order_id=99,
            matching_booking=_booking_item(
                code="T",
                facade=MiniAppBookingFacadeState.ACTIVE_TEMPORARY_RESERVATION,
                order_id=99,
            ),
        )
        self.assertEqual(kind, DetailPrimaryCtaKind.CONTINUE_TO_PAYMENT)
        self.assertEqual(oid, 99)

    def test_resolve_self_service_without_payment(self) -> None:
        prep = SimpleNamespace(self_service_available=True, tour_code="T")
        kind, oid = resolve_detail_primary_cta(
            prep=prep,
            payment_elig=None,
            hold_order_id=None,
            matching_booking=None,
        )
        self.assertEqual(kind, DetailPrimaryCtaKind.CONTINUE_BOOKING)
        self.assertIsNone(oid)

    def test_resolve_open_booking_confirmed(self) -> None:
        prep = SimpleNamespace(self_service_available=False, tour_code="T")
        mb = _booking_item(code="T", facade=MiniAppBookingFacadeState.CONFIRMED, order_id=7)
        kind, oid = resolve_detail_primary_cta(
            prep=prep,
            payment_elig=None,
            hold_order_id=None,
            matching_booking=mb,
        )
        self.assertEqual(kind, DetailPrimaryCtaKind.OPEN_BOOKING)
        self.assertEqual(oid, 7)

    def test_resolve_none_when_blocked_no_booking(self) -> None:
        prep = SimpleNamespace(self_service_available=False, tour_code="T")
        kind, oid = resolve_detail_primary_cta(
            prep=prep,
            payment_elig=None,
            hold_order_id=None,
            matching_booking=None,
        )
        self.assertEqual(kind, DetailPrimaryCtaKind.NONE)

    def test_resolve_terminal_bridge_active_hold_uses_order_payment_cta(self) -> None:
        """Track 5e: bridge prep/eligibility unavailable, but Layer A hold still allows pay via order id."""
        mb = _booking_item(
            code="T",
            facade=MiniAppBookingFacadeState.ACTIVE_TEMPORARY_RESERVATION,
            order_id=42,
        )
        kind, oid = resolve_detail_primary_cta(
            prep=None,
            payment_elig=None,
            hold_order_id=42,
            matching_booking=mb,
            latest_booking_bridge_status=CustomRequestBookingBridgeStatus.CANCELLED,
        )
        self.assertEqual(kind, DetailPrimaryCtaKind.CONTINUE_TO_PAYMENT)
        self.assertEqual(oid, 42)

    def test_detail_context_prefers_closed_copy_when_terminal(self) -> None:
        key, _ = detail_context_line_keys(
            prep=None,
            prep_http_not_found=True,
            latest_booking_bridge_status=CustomRequestBookingBridgeStatus.SUPERSEDED,
        )
        self.assertEqual(key, "rfq_hub_detail_bridge_closed")

    def test_status_labels_resolve_en(self) -> None:
        self.assertIn("review", request_status_user_label("en", CustomMarketplaceRequestStatus.UNDER_REVIEW).lower())
        self.assertIn("received", request_status_user_label("en", CustomMarketplaceRequestStatus.OPEN).lower())


if __name__ == "__main__":
    unittest.main()
