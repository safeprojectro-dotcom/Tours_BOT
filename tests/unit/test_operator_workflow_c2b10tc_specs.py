"""Slice C2B10T-C: Telegram operator_workflow create_execution_link callback wiring."""

from __future__ import annotations

import unittest

from app.bot.constants import ADMIN_OPS_OW_EXEC_LINK_PROPOSE_PREFIX
from app.bot.handlers.admin_moderation import (
    OPERATOR_WORKFLOW_C2B10TC_CREATE_EXECUTION_LINK_CODE,
    _operator_workflow_c2b10tc_exec_link_propose_callback,
)
from app.schemas.supplier_admin import (
    AdminSupplierOfferOperatorWorkflowActionRead,
    AdminSupplierOfferOperatorWorkflowRead,
)


class OperatorWorkflowC2b10tcSpecsTests(unittest.TestCase):
    def test_propose_callback_when_action_enabled(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[
                AdminSupplierOfferOperatorWorkflowActionRead(
                    code=OPERATOR_WORKFLOW_C2B10TC_CREATE_EXECUTION_LINK_CODE,
                    label="x",
                    enabled=True,
                    danger_level="conversion_enabling",
                    requires_confirmation=True,
                    method="POST",
                    endpoint="/admin/supplier-offers/{offer_id}/execution-link",
                ),
            ],
            blocking_reasons=[],
            warnings=[],
        )
        cb = _operator_workflow_c2b10tc_exec_link_propose_callback(7, ow)
        self.assertEqual(cb, f"{ADMIN_OPS_OW_EXEC_LINK_PROPOSE_PREFIX}7")

    def test_propose_callback_none_when_disabled(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[
                AdminSupplierOfferOperatorWorkflowActionRead(
                    code=OPERATOR_WORKFLOW_C2B10TC_CREATE_EXECUTION_LINK_CODE,
                    label="x",
                    enabled=False,
                    danger_level="conversion_enabling",
                    requires_confirmation=True,
                    method="POST",
                    endpoint="/admin/x",
                ),
            ],
            blocking_reasons=[],
            warnings=[],
        )
        self.assertIsNone(_operator_workflow_c2b10tc_exec_link_propose_callback(1, ow))
