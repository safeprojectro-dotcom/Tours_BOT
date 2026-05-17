"""Slice C1 / C1.1: Telegram formatting for operator_workflow (read-only strings)."""

from __future__ import annotations

import unittest

from app.bot.messages import translate
from app.bot.supplier_offer_operator_workflow_telegram import format_operator_workflow_for_telegram
from app.schemas.supplier_admin import (
    AdminSupplierOfferOperatorWorkflowActionRead,
    AdminSupplierOfferOperatorWorkflowRead,
)


class OperatorWorkflowTelegramFormatTests(unittest.TestCase):
    def test_includes_state_primary_warnings_example(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="ready_to_publish_showcase",
            primary_next_action="publish_showcase_channel",
            actions=[
                AdminSupplierOfferOperatorWorkflowActionRead(
                    code="publish_showcase_channel",
                    label="Publish showcase to Telegram channel",
                    enabled=True,
                    danger_level="public_dangerous",
                    requires_confirmation=True,
                    method="POST",
                    endpoint="/admin/supplier-offers/{offer_id}/publish",
                ),
            ],
            blocking_reasons=[],
            warnings=[
                "orphan_promo_code",
                "discount_deadline_without_value",
                "description_thin",
            ],
        )
        text = format_operator_workflow_for_telegram(ow, language_code="en", translate_fn=translate)
        self.assertIn("Ready to publish showcase", text)
        self.assertIn("Publish showcase to channel", text)
        self.assertNotIn("orphan_promo_code", text)
        self.assertNotIn("description_thin", text)
        self.assertIn("Promo or discount", text)
        self.assertIn("Description looks too short", text)
        self.assertNotIn("public_dangerous", text)
        self.assertIn("Public channel", text)
        self.assertIn("Confirm before publishing", text)
        self.assertIn("Notes (3):", text)
        self.assertNotIn("Admin API", text)
        self.assertNotIn("review-package", text.lower())

    def test_warning_bracket_extracts_code_only(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="awaiting_moderation",
            primary_next_action=None,
            actions=[],
            blocking_reasons=[],
            warnings=["[orphan_promo_code] Technical English detail should not dominate the card."],
        )
        text = format_operator_workflow_for_telegram(ow, language_code="en", translate_fn=translate)
        self.assertNotIn("orphan_promo_code", text)
        self.assertNotIn("Technical English", text)
        self.assertIn("Promo or discount", text)
        self.assertIn("Awaiting moderation", text)

    def test_duplicate_warning_lines_are_deduped(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="awaiting_moderation",
            primary_next_action=None,
            actions=[],
            blocking_reasons=[],
            warnings=["orphan_promo_code", "orphan_promo_code", "discount_deadline_without_value"],
        )
        text = format_operator_workflow_for_telegram(ow, language_code="en", translate_fn=translate)
        self.assertEqual(text.count("Promo or discount"), 1)

    def test_duplicate_blocking_lines_are_deduped(self) -> None:
        br = "opaque_blocking_reason_abc_001"
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="awaiting_moderation",
            primary_next_action=None,
            actions=[],
            blocking_reasons=[br, br, br],
            warnings=[],
        )
        text = format_operator_workflow_for_telegram(ow, language_code="en", translate_fn=translate)
        self.assertEqual(text.count("Requires internal verification"), 1)
