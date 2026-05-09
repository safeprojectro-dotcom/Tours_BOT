"""B12C: Telegram showcase template picker — callback prefix helpers."""

from __future__ import annotations

import unittest

from app.bot.constants import (
    ADMIN_OPS_OW_TEMPLATE_APPLY_PREFIX,
    ADMIN_OPS_OW_TEMPLATE_OPEN_PREFIX,
)
from app.bot.handlers.admin_moderation import (
    OPERATOR_WORKFLOW_B12C_TEMPLATE_PATCH_CODE,
    _operator_workflow_b12c_template_open_callback,
    _parse_template_apply_callback,
    _template_apply_callback_data,
    _template_id_allowed_for_telegram_direct_apply,
)
from app.schemas.supplier_admin import (
    AdminSupplierOfferOperatorWorkflowActionRead,
    AdminSupplierOfferOperatorWorkflowRead,
    AdminSupplierOfferShowcaseTemplateChoiceRead,
    AdminSupplierOfferShowcaseTemplatePreviewRead,
)


def _patch_act(*, enabled: bool = True) -> AdminSupplierOfferOperatorWorkflowActionRead:
    return AdminSupplierOfferOperatorWorkflowActionRead(
        code=OPERATOR_WORKFLOW_B12C_TEMPLATE_PATCH_CODE,
        label="patch",
        enabled=enabled,
        danger_level="safe_mutation",
        requires_confirmation=False,
        method="PATCH",
        endpoint="/admin/supplier-offers/{offer_id}/packaging/showcase-template",
    )


class OperatorWorkflowB12cSpecsTests(unittest.TestCase):
    def test_open_callback_when_patch_enabled(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[_patch_act()],
            blocking_reasons=[],
            warnings=[],
        )
        cb = _operator_workflow_b12c_template_open_callback(42, ow)
        self.assertEqual(cb, f"{ADMIN_OPS_OW_TEMPLATE_OPEN_PREFIX}42")

    def test_open_callback_none_when_disabled(self) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[_patch_act(enabled=False)],
            blocking_reasons=[],
            warnings=[],
        )
        self.assertIsNone(_operator_workflow_b12c_template_open_callback(1, ow))

    def test_parse_apply_roundtrip(self) -> None:
        raw = _template_apply_callback_data(offer_id=7, template_id="short_announcement")
        self.assertEqual(raw, f"{ADMIN_OPS_OW_TEMPLATE_APPLY_PREFIX}7:short_announcement")
        parsed = _parse_template_apply_callback(raw)
        assert parsed is not None
        self.assertEqual(parsed, (7, "short_announcement"))

    def test_direct_apply_allowed_only_without_verified_seats_flag(self) -> None:
        stp = AdminSupplierOfferShowcaseTemplatePreviewRead(
            inferred_template_id="per_seat_standard",
            selected_template_id=None,
            effective_template_id="per_seat_standard",
            selection_overrides_inference=False,
            preview_fact_lines_ro_html=[],
            notes=[],
            template_choices=[
                AdminSupplierOfferShowcaseTemplateChoiceRead(
                    template_id="per_seat_standard",
                    requires_verified_live_seats=False,
                ),
                AdminSupplierOfferShowcaseTemplateChoiceRead(
                    template_id="last_seats_urgent",
                    requires_verified_live_seats=True,
                ),
            ],
        )
        self.assertTrue(_template_id_allowed_for_telegram_direct_apply(stp, "per_seat_standard"))
        self.assertFalse(_template_id_allowed_for_telegram_direct_apply(stp, "last_seats_urgent"))
