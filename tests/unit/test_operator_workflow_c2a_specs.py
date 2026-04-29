"""Slice C2A: operator_workflow safe Telegram callback specs."""

from __future__ import annotations

import unittest

from app.bot.constants import ADMIN_OPS_OW_REVIEW_REFRESH_PREFIX, ADMIN_OPS_OW_SHOWCASE_PREVIEW_PREFIX
from app.bot.handlers.admin_moderation import OPERATOR_WORKFLOW_C2A_ACTION_CODES, _operator_workflow_c2a_callback_specs
from app.schemas.supplier_admin import (
    AdminSupplierOfferOperatorWorkflowActionRead,
    AdminSupplierOfferOperatorWorkflowRead,
)


def _act(code: str, *, enabled: bool = True) -> AdminSupplierOfferOperatorWorkflowActionRead:
    return AdminSupplierOfferOperatorWorkflowActionRead(
        code=code,
        label=code,
        enabled=enabled,
        danger_level="safe_read",
        requires_confirmation=False,
        method="GET",
        endpoint="/x",
    )


class OperatorWorkflowC2aSpecsTests(unittest.TestCase):
    def test_allowed_codes_frozen(self) -> None:
        self.assertEqual(OPERATOR_WORKFLOW_C2A_ACTION_CODES, frozenset({"review_package_refresh", "get_showcase_preview"}))

    def test_specs_maps_refresh_and_showcase(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[
                _act("review_package_refresh"),
                _act("get_showcase_preview"),
            ],
            blocking_reasons=[],
            warnings=[],
        )
        specs = _operator_workflow_c2a_callback_specs(42, ow)
        self.assertEqual(len(specs), 2)
        self.assertEqual(specs[0][0], f"{ADMIN_OPS_OW_REVIEW_REFRESH_PREFIX}42")
        self.assertEqual(specs[0][1], "admin_offer_ow_btn_review_refresh")
        self.assertEqual(specs[1][0], f"{ADMIN_OPS_OW_SHOWCASE_PREVIEW_PREFIX}42")
        self.assertEqual(specs[1][1], "admin_offer_ow_btn_showcase_preview")

    def test_disabled_actions_omitted(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[_act("review_package_refresh", enabled=False)],
            blocking_reasons=[],
            warnings=[],
        )
        self.assertEqual(_operator_workflow_c2a_callback_specs(1, ow), [])

    def test_mutating_codes_ignored(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[
                AdminSupplierOfferOperatorWorkflowActionRead(
                    code="publish_showcase_channel",
                    label="Publish",
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
        self.assertEqual(_operator_workflow_c2a_callback_specs(1, ow), [])

