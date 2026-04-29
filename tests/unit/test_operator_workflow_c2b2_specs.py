"""Slice C2B2: generate_packaging_draft Telegram callback helpers."""

from __future__ import annotations

import unittest

from app.bot.constants import ADMIN_OPS_OW_PKG_GEN_PROPOSE_PREFIX
from app.bot.handlers.admin_moderation import (
    OPERATOR_WORKFLOW_C2B2_GENERATE_CODE,
    _operator_workflow_c2b2_generate_propose_callback,
)
from app.schemas.supplier_admin import (
    AdminSupplierOfferOperatorWorkflowActionRead,
    AdminSupplierOfferOperatorWorkflowRead,
)


def _safe_act(code: str, *, enabled: bool = True) -> AdminSupplierOfferOperatorWorkflowActionRead:
    return AdminSupplierOfferOperatorWorkflowActionRead(
        code=code,
        label=code,
        enabled=enabled,
        danger_level="safe_mutation",
        requires_confirmation=False,
        method="POST",
        endpoint="/x",
    )


class OperatorWorkflowC2b2SpecsTests(unittest.TestCase):
    def test_propose_callback_when_generate_enabled(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[
                _safe_act("review_package_refresh"),
                _safe_act(OPERATOR_WORKFLOW_C2B2_GENERATE_CODE),
            ],
            blocking_reasons=[],
            warnings=[],
        )
        cb = _operator_workflow_c2b2_generate_propose_callback(99, ow)
        self.assertEqual(cb, f"{ADMIN_OPS_OW_PKG_GEN_PROPOSE_PREFIX}99")

    def test_propose_callback_none_when_disabled(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[_safe_act(OPERATOR_WORKFLOW_C2B2_GENERATE_CODE, enabled=False)],
            blocking_reasons=[],
            warnings=[],
        )
        self.assertIsNone(_operator_workflow_c2b2_generate_propose_callback(1, ow))
