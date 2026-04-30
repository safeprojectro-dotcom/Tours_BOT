"""Slice C2B3: Telegram admin offer detail keyboard labels + ordering (UX polish only)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from app.bot.constants import (
    ADMIN_OFFERS_ACTION_APPROVE,
    ADMIN_OFFERS_ACTION_CALLBACK_PREFIX,
    ADMIN_OPS_OW_MEDIA_REQ_PROPOSE_PREFIX,
    ADMIN_OPS_OW_PKG_APPROVE_PROPOSE_PREFIX,
    ADMIN_OPS_OW_PKG_GEN_PROPOSE_PREFIX,
    ADMIN_OPS_OW_REVIEW_REFRESH_PREFIX,
    ADMIN_OPS_OW_SHOWCASE_PREVIEW_PREFIX,
)
from app.bot.handlers.admin_moderation import _detail_keyboard
from app.models.enums import SupplierOfferLifecycle
from app.schemas.supplier_admin import (
    AdminSupplierOfferOperatorWorkflowActionRead,
    AdminSupplierOfferOperatorWorkflowRead,
)


def _read_act(code: str) -> AdminSupplierOfferOperatorWorkflowActionRead:
    return AdminSupplierOfferOperatorWorkflowActionRead(
        code=code,
        label=code,
        enabled=True,
        danger_level="safe_read",
        requires_confirmation=False,
        method="GET",
        endpoint="/admin/x",
    )


def _mut_act(code: str) -> AdminSupplierOfferOperatorWorkflowActionRead:
    return AdminSupplierOfferOperatorWorkflowActionRead(
        code=code,
        label=code,
        enabled=True,
        danger_level="safe_mutation",
        requires_confirmation=True,
        method="POST",
        endpoint="/admin/y",
    )


def _flat_markup(markup):
    texts: list[str] = []
    callbacks: list[str | None] = []
    for row in markup.inline_keyboard:
        for btn in row:
            texts.append(btn.text or "")
            callbacks.append(btn.callback_data)
    return texts, callbacks


class OperatorWorkflowC2b3KeyboardTests(unittest.TestCase):
    @patch("app.bot.handlers.admin_moderation.SupplierOfferReviewPackageService")
    def test_ro_order_read_then_packaging_then_legacy_then_ops_nav(self, mock_review_svc: MagicMock) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[
                _read_act("review_package_refresh"),
                _read_act("get_showcase_preview"),
                _mut_act("request_cover_photo_replacement"),
                _mut_act("generate_packaging_draft"),
                _mut_act("approve_packaging_for_publish"),
            ],
            blocking_reasons=[],
            warnings=[],
        )
        mock_review_svc.return_value.review_package.return_value = MagicMock(operator_workflow=ow)
        offer = MagicMock()
        offer.id = 99
        offer.lifecycle_status = SupplierOfferLifecycle.READY_FOR_MODERATION

        kb = _detail_keyboard("ro", offer, session=MagicMock())
        texts, callbacks = _flat_markup(kb.as_markup())

        ix = {t: n for n, t in enumerate(texts)}
        self.assertLess(ix["Actualizează"], ix["Preview"])
        self.assertLess(ix["Preview"], ix["Cere poză"])
        self.assertLess(ix["Cere poză"], ix["Pregătește"])
        self.assertLess(ix["Pregătește"], ix["Aprobă text"])
        self.assertLess(ix["Aprobă text"], ix["Aprobă oferta"])
        self.assertLess(ix["Aprobă oferta"], ix["Respinge oferta"])
        self.assertLess(ix["Respinge oferta"], ix["📦 Comenzi"])

        joined_lc = " ".join(texts).lower()
        for needle in ("review-package", "showcase", "approve_packaging", "generate_packaging"):
            self.assertNotIn(needle, joined_lc)
        self.assertNotIn("_", "".join(texts))

        self.assertTrue(any(str(c).startswith(ADMIN_OPS_OW_REVIEW_REFRESH_PREFIX) for c in callbacks if c))
        self.assertTrue(any(str(c).startswith(ADMIN_OPS_OW_SHOWCASE_PREVIEW_PREFIX) for c in callbacks if c))
        self.assertTrue(any(str(c).startswith(ADMIN_OPS_OW_MEDIA_REQ_PROPOSE_PREFIX) for c in callbacks if c))
        self.assertTrue(any(str(c).startswith(ADMIN_OPS_OW_PKG_GEN_PROPOSE_PREFIX) for c in callbacks if c))
        self.assertTrue(any(str(c).startswith(ADMIN_OPS_OW_PKG_APPROVE_PROPOSE_PREFIX) for c in callbacks if c))
        approve_legacy = f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_APPROVE}:99"
        self.assertIn(approve_legacy, callbacks)

    @patch("app.bot.handlers.admin_moderation.SupplierOfferReviewPackageService")
    def test_en_packaging_before_legacy(self, mock_review_svc: MagicMock) -> None:
        ow = AdminSupplierOfferOperatorWorkflowRead(
            state="s",
            primary_next_action=None,
            actions=[_mut_act("generate_packaging_draft")],
            blocking_reasons=[],
            warnings=[],
        )
        mock_review_svc.return_value.review_package.return_value = MagicMock(operator_workflow=ow)
        offer = MagicMock()
        offer.id = 3
        offer.lifecycle_status = SupplierOfferLifecycle.READY_FOR_MODERATION

        texts, _ = _flat_markup(_detail_keyboard("en", offer, session=MagicMock()).as_markup())
        ix = {t: n for n, t in enumerate(texts)}
        self.assertLess(ix["Prepare"], ix["Approve offer"])
