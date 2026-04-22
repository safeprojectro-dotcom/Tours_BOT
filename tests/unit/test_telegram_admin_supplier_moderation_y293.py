"""Y29.3: Telegram admin supplier moderation workspace (allowlist + profile actions)."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.bot.constants import (
    ADMIN_SUPPLIERS_ACTION_APPROVE,
    ADMIN_SUPPLIERS_ACTION_CALLBACK_PREFIX,
    ADMIN_SUPPLIERS_ACTION_REACTIVATE,
    ADMIN_SUPPLIERS_ACTION_REJECT,
    ADMIN_SUPPLIERS_ACTION_REVOKE,
    ADMIN_SUPPLIERS_ACTION_SUSPEND,
)
from app.bot.handlers import admin_supplier_moderation
from app.core.config import get_settings
from app.models.enums import SupplierLegalEntityType, SupplierOnboardingStatus
from tests.unit.base import FoundationDBTestCase


class _SessionLocalBinder:
    def __init__(self, session) -> None:
        self._session = session

    def __call__(self):
        return self._session


class _DictFSMState:
    def __init__(self) -> None:
        self.data: dict = {}
        self.last_state = None

    async def update_data(self, data: dict | None = None, **kwargs: object) -> dict:
        if data:
            self.data.update(dict(data))
        if kwargs:
            self.data.update(kwargs)
        return dict(self.data)

    async def get_data(self) -> dict:
        return dict(self.data)

    async def clear(self) -> None:
        self.data.clear()
        self.last_state = None

    async def set_state(self, value) -> None:
        self.last_state = value

    async def get_state(self):
        return self.last_state


def _private_message(*, telegram_user_id: int) -> MagicMock:
    message = MagicMock()
    message.from_user = MagicMock()
    message.from_user.id = telegram_user_id
    message.from_user.username = "admin_user"
    message.from_user.first_name = "Admin"
    message.from_user.last_name = "User"
    message.from_user.language_code = "en"
    message.chat = MagicMock()
    message.chat.type = "private"
    message.chat.id = 777_010
    message.answer = AsyncMock(return_value=MagicMock(message_id=1))
    return message


def _callback(*, telegram_user_id: int, data: str, message: MagicMock) -> MagicMock:
    cb = MagicMock()
    cb.from_user = message.from_user
    cb.from_user.id = telegram_user_id
    cb.from_user.language_code = "en"
    cb.data = data
    cb.message = message
    cb.answer = AsyncMock()
    return cb


class TelegramAdminSupplierModerationY293Tests(FoundationDBTestCase):
    @staticmethod
    def _run(coro) -> None:
        asyncio.run(coro)

    def setUp(self) -> None:
        super().setUp()
        self._orig_allowlist = get_settings().telegram_admin_allowlist_user_ids
        get_settings().telegram_admin_allowlist_user_ids = "991001"

    def tearDown(self) -> None:
        get_settings().telegram_admin_allowlist_user_ids = self._orig_allowlist
        super().tearDown()

    @staticmethod
    def _all_answer_texts(message: MagicMock) -> str:
        return "\n".join(c.args[0].lower() for c in message.answer.call_args_list if c.args)

    @staticmethod
    def _inline_button_texts(message: MagicMock) -> list[str]:
        texts: list[str] = []
        for call in message.answer.call_args_list:
            markup = call.kwargs.get("reply_markup")
            if markup is None:
                continue
            inline_rows = getattr(markup, "inline_keyboard", None) or []
            for row in inline_rows:
                for btn in row:
                    txt = getattr(btn, "text", None)
                    if isinstance(txt, str):
                        texts.append(txt.lower())
        return texts

    def _create_supplier(self, *, status: SupplierOnboardingStatus) -> int:
        supplier = self.create_supplier(
            code=f"Y293-{status.value}-{self._next()}",
            display_name=f"Supplier {status.value}",
            is_active=status == SupplierOnboardingStatus.APPROVED,
            onboarding_status=status,
            primary_telegram_user_id=880_000 + self._next(),
            legal_entity_type=SupplierLegalEntityType.COMPANY,
            legal_registered_name="RoadJet SRL",
            legal_registration_code="ROY293",
            permit_license_type="Carrier license",
            permit_license_number="CL-293",
        )
        self.session.commit()
        return supplier.id

    def test_allowlisted_admin_can_open_supplier_queue(self) -> None:
        supplier_id = self._create_supplier(status=SupplierOnboardingStatus.PENDING_REVIEW)

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=991001)
            with patch.object(admin_supplier_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_supplier_moderation.cmd_admin_supplier_queue(message, state)
            return self._all_answer_texts(message)

        text = asyncio.run(body())
        self.assertIn("pending-review queue", text)
        self.assertIn(f"#{supplier_id}", text)

    def test_pending_supplier_can_be_approved(self) -> None:
        supplier_id = self._create_supplier(status=SupplierOnboardingStatus.PENDING_REVIEW)

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=991001)
            cb = _callback(
                telegram_user_id=991001,
                data=f"{ADMIN_SUPPLIERS_ACTION_CALLBACK_PREFIX}{ADMIN_SUPPLIERS_ACTION_APPROVE}:{supplier_id}",
                message=message,
            )
            with patch.object(admin_supplier_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_supplier_moderation.admin_supplier_action(cb, state)
            row = self.session.get(admin_supplier_moderation.Supplier, supplier_id)
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row.onboarding_status, SupplierOnboardingStatus.APPROVED)
            return self._all_answer_texts(message)

        text = asyncio.run(body())
        self.assertIn("approved", text)

    def test_pending_supplier_can_be_rejected_with_reason(self) -> None:
        supplier_id = self._create_supplier(status=SupplierOnboardingStatus.PENDING_REVIEW)

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=991001)
            cb = _callback(
                telegram_user_id=991001,
                data=f"{ADMIN_SUPPLIERS_ACTION_CALLBACK_PREFIX}{ADMIN_SUPPLIERS_ACTION_REJECT}:{supplier_id}",
                message=message,
            )
            with patch.object(admin_supplier_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_supplier_moderation.admin_supplier_action(cb, state)
            reason_message = _private_message(telegram_user_id=991001)
            reason_message.text = "Incomplete legal profile"
            with patch.object(admin_supplier_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_supplier_moderation.admin_supplier_reason(reason_message, state)
            row = self.session.get(admin_supplier_moderation.Supplier, supplier_id)
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row.onboarding_status, SupplierOnboardingStatus.REJECTED)
            self.assertEqual(row.onboarding_rejection_reason, "Incomplete legal profile")
            return self._all_answer_texts(reason_message)

        text = asyncio.run(body())
        self.assertIn("rejected", text)

    def test_approved_supplier_can_be_suspended(self) -> None:
        supplier_id = self._create_supplier(status=SupplierOnboardingStatus.APPROVED)

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=991001)
            cb = _callback(
                telegram_user_id=991001,
                data=f"{ADMIN_SUPPLIERS_ACTION_CALLBACK_PREFIX}{ADMIN_SUPPLIERS_ACTION_SUSPEND}:{supplier_id}",
                message=message,
            )
            with patch.object(admin_supplier_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_supplier_moderation.admin_supplier_action(cb, state)
            reason_message = _private_message(telegram_user_id=991001)
            reason_message.text = "Policy violation"
            with patch.object(admin_supplier_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_supplier_moderation.admin_supplier_reason(reason_message, state)
            row = self.session.get(admin_supplier_moderation.Supplier, supplier_id)
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row.onboarding_status, SupplierOnboardingStatus.SUSPENDED)
            self.assertEqual(row.onboarding_suspension_reason, "Policy violation")
            return self._all_answer_texts(reason_message)

        text = asyncio.run(body())
        self.assertIn("suspended", text)

    def test_suspended_supplier_can_be_reactivated(self) -> None:
        supplier_id = self._create_supplier(status=SupplierOnboardingStatus.SUSPENDED)

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=991001)
            cb = _callback(
                telegram_user_id=991001,
                data=f"{ADMIN_SUPPLIERS_ACTION_CALLBACK_PREFIX}{ADMIN_SUPPLIERS_ACTION_REACTIVATE}:{supplier_id}",
                message=message,
            )
            with patch.object(admin_supplier_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_supplier_moderation.admin_supplier_action(cb, state)
            row = self.session.get(admin_supplier_moderation.Supplier, supplier_id)
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row.onboarding_status, SupplierOnboardingStatus.APPROVED)
            self.assertIsNone(row.onboarding_suspension_reason)
            return self._all_answer_texts(message)

        text = asyncio.run(body())
        self.assertIn("reactivated", text)

    def test_approved_or_suspended_supplier_can_be_revoked(self) -> None:
        approved_id = self._create_supplier(status=SupplierOnboardingStatus.APPROVED)
        suspended_id = self._create_supplier(status=SupplierOnboardingStatus.SUSPENDED)

        async def revoke_with_reason(supplier_id: int, reason: str) -> None:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=991001)
            cb = _callback(
                telegram_user_id=991001,
                data=f"{ADMIN_SUPPLIERS_ACTION_CALLBACK_PREFIX}{ADMIN_SUPPLIERS_ACTION_REVOKE}:{supplier_id}",
                message=message,
            )
            with patch.object(admin_supplier_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_supplier_moderation.admin_supplier_action(cb, state)
            reason_message = _private_message(telegram_user_id=991001)
            reason_message.text = reason
            with patch.object(admin_supplier_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_supplier_moderation.admin_supplier_reason(reason_message, state)

        self._run(revoke_with_reason(approved_id, "Fraud risk"))
        self._run(revoke_with_reason(suspended_id, "Permanent ban"))
        row_a = self.session.get(admin_supplier_moderation.Supplier, approved_id)
        row_s = self.session.get(admin_supplier_moderation.Supplier, suspended_id)
        self.assertIsNotNone(row_a)
        self.assertIsNotNone(row_s)
        assert row_a is not None
        assert row_s is not None
        self.assertEqual(row_a.onboarding_status, SupplierOnboardingStatus.REVOKED)
        self.assertEqual(row_s.onboarding_status, SupplierOnboardingStatus.REVOKED)

    def test_invalid_action_state_combination_shows_explicit_feedback(self) -> None:
        supplier_id = self._create_supplier(status=SupplierOnboardingStatus.REJECTED)

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=991001)
            cb = _callback(
                telegram_user_id=991001,
                data=f"{ADMIN_SUPPLIERS_ACTION_CALLBACK_PREFIX}{ADMIN_SUPPLIERS_ACTION_REACTIVATE}:{supplier_id}",
                message=message,
            )
            with patch.object(admin_supplier_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_supplier_moderation.admin_supplier_action(cb, state)
            return self._all_answer_texts(message)

        text = asyncio.run(body())
        self.assertIn("unavailable", text)
        self.assertIn("only suspended suppliers can be reactivated", text)

    def test_no_offer_moderation_semantics_mixed_into_supplier_workspace(self) -> None:
        supplier_id = self._create_supplier(status=SupplierOnboardingStatus.APPROVED)
        supplier = self.session.get(admin_supplier_moderation.Supplier, supplier_id)
        self.assertIsNotNone(supplier)
        assert supplier is not None
        actions = [payload for _, payload in admin_supplier_moderation._action_button_rows("en", supplier)]
        self.assertIn(f"admin:suppliers:action:suspend:{supplier_id}", actions)
        self.assertIn(f"admin:suppliers:action:revoke:{supplier_id}", actions)
        self.assertNotIn(f"admin:suppliers:action:publish:{supplier_id}", actions)
        self.assertNotIn(f"admin:suppliers:action:retract:{supplier_id}", actions)

        async def body() -> list[str]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=991001)
            with patch.object(admin_supplier_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_supplier_moderation.cmd_admin_suppliers(message, state)
            return self._inline_button_texts(message)

        button_texts = asyncio.run(body())
        self.assertIn("suspend", button_texts)
        self.assertIn("revoke", button_texts)
        self.assertNotIn("publish", button_texts)
        self.assertNotIn("retract", button_texts)


if __name__ == "__main__":
    unittest.main()
