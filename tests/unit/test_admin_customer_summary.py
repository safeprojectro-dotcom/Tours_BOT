"""Unit tests for admin/ops customer summary derivation (Y35.5)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.services.admin_customer_summary import (
    build_admin_customer_summary,
    build_admin_customer_summary_from_user,
    derive_display_name,
)


class TestAdminCustomerSummary(unittest.TestCase):
    def test_display_name_from_first_and_last(self) -> None:
        s = build_admin_customer_summary(
            telegram_user_id=55,
            first_name=" Ada ",
            last_name=" Lovelace ",
        )
        self.assertIsNotNone(s)
        assert s is not None
        self.assertEqual(s.display_name, "Ada Lovelace")
        self.assertEqual(s.summary_line, "customer: Ada Lovelace")

    def test_display_name_from_first_only(self) -> None:
        s = build_admin_customer_summary(telegram_user_id=1, first_name="Solo", last_name="   ")
        self.assertIsNotNone(s)
        assert s is not None
        self.assertEqual(s.display_name, "Solo")
        self.assertEqual(s.summary_line, "customer: Solo")

    def test_summary_with_username_and_fallback_tg(self) -> None:
        s = build_admin_customer_summary(
            telegram_user_id=5330304811,
            first_name=None,
            last_name=None,
            username="alice_test",
        )
        self.assertIsNotNone(s)
        assert s is not None
        self.assertIsNone(s.display_name)
        self.assertEqual(s.username, "alice_test")
        self.assertEqual(s.summary_line, "customer: tg:5330304811 @alice_test")

    def test_username_strips_leading_at(self) -> None:
        s = build_admin_customer_summary(
            telegram_user_id=2,
            first_name="A",
            last_name=None,
            username="@handle",
        )
        self.assertIsNotNone(s)
        assert s is not None
        self.assertEqual(s.username, "handle")
        self.assertEqual(s.summary_line, "customer: A @handle")

    def test_none_telegram_returns_none(self) -> None:
        self.assertIsNone(
            build_admin_customer_summary(telegram_user_id=None, first_name="X", last_name="Y"),
        )

    def test_derive_display_name_empty(self) -> None:
        self.assertIsNone(derive_display_name("", ""))
        self.assertIsNone(derive_display_name("  ", None))

    def test_build_from_user_none(self) -> None:
        self.assertIsNone(build_admin_customer_summary_from_user(None))

    def test_build_from_user_simple_namespace(self) -> None:
        u = SimpleNamespace(
            telegram_user_id=99,
            first_name="Fn",
            last_name="Ln",
            username="n",
        )
        s = build_admin_customer_summary_from_user(u)
        self.assertIsNotNone(s)
        assert s is not None
        self.assertEqual(s.summary_line, "customer: Fn Ln @n")
