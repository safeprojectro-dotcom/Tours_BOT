"""Slice C2B8B: Telegram operator_workflow publish_showcase_channel callback wiring."""

from __future__ import annotations

import unittest

from app.bot.constants import ADMIN_OPS_OW_PUBLISH_SHOWCASE_PROPOSE_PREFIX
from app.bot.handlers.admin_moderation import (
    OPERATOR_WORKFLOW_C2B8B_PUBLISH_SHOWCASE_CODE,
    _operator_workflow_c2b8b_publish_propose_callback,
)
from app.schemas.supplier_admin import (
    AdminSupplierOfferOperatorWorkflowActionRead,
    AdminSupplierOfferOperatorWorkflowRead,
)


class OperatorWorkflowC2b8bSpecsTests(unittest.TestCase):
    def test_propose_callback_when_action_enabled(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[
                AdminSupplierOfferOperatorWorkflowActionRead(
                    code=OPERATOR_WORKFLOW_C2B8B_PUBLISH_SHOWCASE_CODE,
                    label="x",
                    enabled=True,
                    danger_level="public_dangerous",
                    requires_confirmation=True,
                    method="POST",
                    endpoint="/admin/supplier-offers/{offer_id}/publish",
                ),
            ],
            blocking_reasons=[],
            warnings=[],
        )
        cb = _operator_workflow_c2b8b_publish_propose_callback(7, ow)
        self.assertEqual(cb, f"{ADMIN_OPS_OW_PUBLISH_SHOWCASE_PROPOSE_PREFIX}7")

    def test_propose_callback_none_when_disabled(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[
                AdminSupplierOfferOperatorWorkflowActionRead(
                    code=OPERATOR_WORKFLOW_C2B8B_PUBLISH_SHOWCASE_CODE,
                    label="x",
                    enabled=False,
                    danger_level="public_dangerous",
                    requires_confirmation=True,
                    method="POST",
                    endpoint="/admin/x",
                ),
            ],
            blocking_reasons=[],
            warnings=[],
        )
        self.assertIsNone(_operator_workflow_c2b8b_publish_propose_callback(1, ow))
