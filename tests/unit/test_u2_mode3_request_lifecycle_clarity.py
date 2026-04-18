"""U2: Mode 3 request lifecycle copy and read-side helpers (no Flet)."""

from __future__ import annotations

import unittest

from app.models.enums import CustomMarketplaceRequestStatus

from mini_app.rfq_hub_cta import (
    DetailPrimaryCtaKind,
    detail_next_step_key,
    is_request_status_terminal,
    my_requests_list_summary_key,
    my_requests_row_hint_key,
    request_status_user_label,
)
from mini_app.ui_strings import shell


_U2_SHELL_KEYS: frozenset[str] = frozenset(
    {
        "my_requests_list_summary_all_closed",
        "my_requests_list_summary_all_active",
        "my_requests_list_summary_mixed",
        "my_requests_list_expectation_note",
        "my_requests_row_hint_open",
        "my_requests_row_hint_under_review",
        "my_requests_row_hint_supplier_selected",
        "my_requests_row_hint_closed_assisted",
        "my_requests_row_hint_closed_external",
        "my_requests_row_hint_cancelled",
        "my_requests_row_hint_fulfilled",
        "my_requests_detail_next_heading",
        "my_requests_detail_next_pay_when_ready",
        "my_requests_detail_next_continue_booking",
        "my_requests_detail_next_open_booking",
        "my_requests_detail_next_cancelled",
        "my_requests_detail_next_closed",
        "my_requests_detail_next_open",
        "my_requests_detail_next_under_review",
        "my_requests_detail_next_supplier_selected",
        "my_requests_detail_next_generic",
        "my_requests_cta_caption_payment",
        "my_requests_cta_caption_booking",
        "my_requests_cta_caption_open_booking",
        "rfq_status_fulfilled",
    }
)

_WAITING_FORBIDDEN = (
    "payment confirmed",
    "confirmed booking",
    "supplier confirmed",
    "definitely be notified",
    "operator contacted",
)


class U2Mode3RequestLifecycleClarityTests(unittest.TestCase):
    def test_u2_keys_exist_in_english_table(self) -> None:
        for key in sorted(_U2_SHELL_KEYS):
            with self.subTest(key=key):
                text = shell("en", key)
                self.assertGreater(len(text.strip()), 0)

    def test_list_summary_keys(self) -> None:
        self.assertIsNone(my_requests_list_summary_key(n_total=0, n_active=0, n_closed=0))
        self.assertEqual(
            my_requests_list_summary_key(n_total=2, n_active=0, n_closed=2),
            "my_requests_list_summary_all_closed",
        )
        self.assertEqual(
            my_requests_list_summary_key(n_total=2, n_active=2, n_closed=0),
            "my_requests_list_summary_all_active",
        )
        self.assertEqual(
            my_requests_list_summary_key(n_total=3, n_active=2, n_closed=1),
            "my_requests_list_summary_mixed",
        )

    def test_terminal_statuses_for_list_grouping(self) -> None:
        self.assertTrue(is_request_status_terminal(CustomMarketplaceRequestStatus.CANCELLED))
        self.assertTrue(is_request_status_terminal(CustomMarketplaceRequestStatus.FULFILLED))
        self.assertFalse(is_request_status_terminal(CustomMarketplaceRequestStatus.OPEN))
        self.assertFalse(is_request_status_terminal(CustomMarketplaceRequestStatus.UNDER_REVIEW))

    def test_row_hint_keys_resolve(self) -> None:
        for st in CustomMarketplaceRequestStatus:
            key = my_requests_row_hint_key(st)
            with self.subTest(status=st):
                self.assertGreater(len(shell("en", key).strip()), 0)

    def test_status_labels_are_human_readable_not_enum_dump(self) -> None:
        for st in CustomMarketplaceRequestStatus:
            label = request_status_user_label("en", st)
            with self.subTest(status=st):
                self.assertNotIn("custommarketplace", label.lower())
                self.assertNotIn("requeststatus", label.lower())

    def test_waiting_next_step_copy_guardrails(self) -> None:
        for st in (CustomMarketplaceRequestStatus.OPEN, CustomMarketplaceRequestStatus.UNDER_REVIEW):
            key = detail_next_step_key(status=st, cta_kind=DetailPrimaryCtaKind.NONE)
            text = shell("en", key).lower()
            for bad in _WAITING_FORBIDDEN:
                with self.subTest(status=st, bad=bad):
                    self.assertNotIn(bad, text)

    def test_next_step_aligns_with_primary_cta_when_present(self) -> None:
        self.assertEqual(
            detail_next_step_key(
                status=CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
                cta_kind=DetailPrimaryCtaKind.CONTINUE_TO_PAYMENT,
            ),
            "my_requests_detail_next_pay_when_ready",
        )
        self.assertEqual(
            detail_next_step_key(
                status=CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
                cta_kind=DetailPrimaryCtaKind.CONTINUE_BOOKING,
            ),
            "my_requests_detail_next_continue_booking",
        )
        self.assertEqual(
            detail_next_step_key(
                status=CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
                cta_kind=DetailPrimaryCtaKind.OPEN_BOOKING,
            ),
            "my_requests_detail_next_open_booking",
        )

    def test_closed_next_step_does_not_push_payment_cta_language(self) -> None:
        key = detail_next_step_key(
            status=CustomMarketplaceRequestStatus.CLOSED_EXTERNAL,
            cta_kind=DetailPrimaryCtaKind.NONE,
        )
        text = shell("en", key).lower()
        self.assertNotIn("continue to payment", text)
        self.assertNotIn("pay now", text)


if __name__ == "__main__":
    unittest.main()
