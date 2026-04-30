"""Slice C2B6: Telegram operator_workflow media replacement request callback wiring."""

from __future__ import annotations

import unittest

from app.bot.constants import ADMIN_OPS_OW_MEDIA_REQ_PROPOSE_PREFIX
from app.bot.handlers.admin_moderation import (
    OPERATOR_WORKFLOW_C2B6_REQUEST_PHOTO_CODE,
    _operator_workflow_c2b6_media_req_propose_callback,
)
from app.schemas.supplier_admin import (
    AdminSupplierOfferOperatorWorkflowActionRead,
    AdminSupplierOfferOperatorWorkflowRead,
)


class OperatorWorkflowC2b6SpecsTests(unittest.TestCase):
    def test_propose_callback_when_action_enabled(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[
                AdminSupplierOfferOperatorWorkflowActionRead(
                    code=OPERATOR_WORKFLOW_C2B6_REQUEST_PHOTO_CODE,
                    label="x",
                    enabled=True,
                    danger_level="safe_mutation",
                    requires_confirmation=True,
                    method="POST",
                    endpoint="/admin/supplier-offers/{offer_id}/media/request-replacement",
                ),
            ],
            blocking_reasons=[],
            warnings=[],
        )
        cb = _operator_workflow_c2b6_media_req_propose_callback(7, ow)
        self.assertEqual(cb, f"{ADMIN_OPS_OW_MEDIA_REQ_PROPOSE_PREFIX}7")

    def test_propose_callback_none_when_disabled(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[
                AdminSupplierOfferOperatorWorkflowActionRead(
                    code=OPERATOR_WORKFLOW_C2B6_REQUEST_PHOTO_CODE,
                    label="x",
                    enabled=False,
                    danger_level="safe_mutation",
                    requires_confirmation=True,
                    method="POST",
                    endpoint="/x",
                ),
            ],
            blocking_reasons=[],
            warnings=[],
        )
        self.assertIsNone(_operator_workflow_c2b6_media_req_propose_callback(1, ow))
