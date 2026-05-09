"""Slice C2B10T-B: Telegram operator_workflow activate_tour_for_catalog callback wiring."""

from __future__ import annotations

import unittest

from app.bot.constants import ADMIN_OPS_OW_ACTIVATE_CATALOG_PROPOSE_PREFIX
from app.bot.handlers.admin_moderation import (
    OPERATOR_WORKFLOW_C2B10TB_ACTIVATE_CATALOG_CODE,
    _operator_workflow_c2b10tb_activate_catalog_propose_callback,
)
from app.schemas.supplier_admin import (
    AdminSupplierOfferOperatorWorkflowActionRead,
    AdminSupplierOfferOperatorWorkflowRead,
)


class OperatorWorkflowC2b10tbSpecsTests(unittest.TestCase):
    def test_propose_callback_when_action_enabled(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[
                AdminSupplierOfferOperatorWorkflowActionRead(
                    code=OPERATOR_WORKFLOW_C2B10TB_ACTIVATE_CATALOG_CODE,
                    label="x",
                    enabled=True,
                    danger_level="conversion_enabling",
                    requires_confirmation=True,
                    method="POST",
                    endpoint="/admin/tours/{tour_id}/activate-for-catalog",
                ),
            ],
            blocking_reasons=[],
            warnings=[],
        )
        cb = _operator_workflow_c2b10tb_activate_catalog_propose_callback(7, ow)
        self.assertEqual(cb, f"{ADMIN_OPS_OW_ACTIVATE_CATALOG_PROPOSE_PREFIX}7")

    def test_propose_callback_none_when_disabled(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[
                AdminSupplierOfferOperatorWorkflowActionRead(
                    code=OPERATOR_WORKFLOW_C2B10TB_ACTIVATE_CATALOG_CODE,
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
        self.assertIsNone(_operator_workflow_c2b10tb_activate_catalog_propose_callback(1, ow))
