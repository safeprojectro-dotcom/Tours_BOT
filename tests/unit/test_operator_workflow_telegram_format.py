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
        self.assertIn("ready_to_publish_showcase", text)
        self.assertIn("publish_showcase_channel", text)
        self.assertIn("orphan_promo_code", text)
        self.assertNotIn("public_dangerous", text)
        self.assertIn("public channel", text)
        self.assertIn("Confirm before publishing", text)
        self.assertIn("Warnings (3):", text)

    def test_warning_bracket_extracts_code_only(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="awaiting_moderation",
            primary_next_action=None,
            actions=[],
            blocking_reasons=[],
            warnings=["[orphan_promo_code] Technical English detail should not dominate the card."],
        )
        text = format_operator_workflow_for_telegram(ow, language_code="en", translate_fn=translate)
        self.assertIn("orphan_promo_code", text)
        self.assertNotIn("Technical English", text)
