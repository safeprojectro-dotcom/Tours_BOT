"""Y2.1: supplier Telegram identity binding + onboarding + admin approve/reject gate."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.bot.handlers import supplier_onboarding
from app.bot.state import SupplierOnboardingState
from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import SupplierOnboardingStatus, SupplierServiceComposition
from app.services.supplier_onboarding_service import SupplierOnboardingService
from tests.unit.base import FoundationDBTestCase


class _SessionLocalBinder:
    def __init__(self, session) -> None:
        self._session = session

    def __call__(self):
        return self._session


def _private_message(*, telegram_user_id: int) -> MagicMock:
    message = MagicMock()
    message.from_user = MagicMock()
    message.from_user.id = telegram_user_id
    message.from_user.username = "supplier_user"
    message.from_user.first_name = "Sup"
    message.from_user.last_name = "User"
    message.from_user.language_code = "en"
    message.chat = MagicMock()
    message.chat.type = "private"
    message.chat.id = 777_001
    message.answer = AsyncMock(return_value=MagicMock(message_id=1))
    return message


class SupplierTelegramOnboardingY21Tests(FoundationDBTestCase):
    @staticmethod
    def _run(coro) -> None:
        asyncio.run(coro)

    def setUp(self) -> None:
        super().setUp()
        self.nested = self.connection.begin_nested()

        @event.listens_for(self.session, "after_transaction_end")
        def restart_savepoint(session, transaction) -> None:
            parent = getattr(transaction, "_parent", None)
            if transaction.nested and not getattr(parent, "nested", False):
                self.nested = self.connection.begin_nested()

        self._restart_savepoint = restart_savepoint
        self.app = create_app()
        self._original_admin = get_settings().admin_api_token
        get_settings().admin_api_token = "test-admin-secret"

        def override_get_db():
            yield self.session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()
        self.app.dependency_overrides.clear()
        get_settings().admin_api_token = self._original_admin
        event.remove(self.session, "after_transaction_end", self._restart_savepoint)
        super().tearDown()

    def test_supplier_command_starts_onboarding_entry_path(self) -> None:
        async def body() -> None:
            message = _private_message(telegram_user_id=811_001)
            state = MagicMock()
            state.clear = AsyncMock()
            state.set_state = AsyncMock()
            state.update_data = AsyncMock()
            binder = _SessionLocalBinder(self.session)
            with patch.object(supplier_onboarding, "SessionLocal", binder):
                await supplier_onboarding.cmd_supplier_entry(message, state)
            state.set_state.assert_awaited_with(SupplierOnboardingState.entering_display_name)
            text = message.answer.call_args[0][0].lower()
            self.assertIn("supplier onboarding", text)

        self._run(body())

    def test_supplier_command_pending_user_gets_status_message(self) -> None:
        SupplierOnboardingService().submit_from_telegram(
            self.session,
            telegram_user_id=811_010,
            display_name="Pending Bot Co",
            contact_info="+4010",
            region="RO",
            service_composition=SupplierServiceComposition.TRANSPORT_ONLY,
            fleet_summary=None,
        )
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=811_010)
            state = MagicMock()
            state.clear = AsyncMock()
            state.set_state = AsyncMock()
            state.update_data = AsyncMock()
            binder = _SessionLocalBinder(self.session)
            with patch.object(supplier_onboarding, "SessionLocal", binder):
                await supplier_onboarding.cmd_supplier_entry(message, state)
            text = message.answer.call_args[0][0].lower()
            self.assertIn("pending", text)
            state.set_state.assert_not_awaited()

        self._run(body())

    def test_onboarding_submission_persists_fields_and_telegram_binding(self) -> None:
        svc = SupplierOnboardingService()
        supplier, result = svc.submit_from_telegram(
            self.session,
            telegram_user_id=811_002,
            display_name="RoadJet",
            contact_info="+40111222333 @roadjet",
            region="RO West",
            service_composition=SupplierServiceComposition.TRANSPORT_GUIDE,
            fleet_summary="2 buses",
        )
        self.session.commit()
        self.assertEqual(result, "submitted")
        self.assertEqual(supplier.primary_telegram_user_id, 811_002)
        self.assertEqual(supplier.onboarding_status, SupplierOnboardingStatus.PENDING_REVIEW)
        self.assertEqual(supplier.onboarding_service_composition, SupplierServiceComposition.TRANSPORT_GUIDE)
        self.assertFalse(supplier.is_active)

    def test_pending_supplier_is_not_approved(self) -> None:
        svc = SupplierOnboardingService()
        supplier, _ = svc.submit_from_telegram(
            self.session,
            telegram_user_id=811_003,
            display_name="Pending Co",
            contact_info="+4000000",
            region="RO",
            service_composition=SupplierServiceComposition.TRANSPORT_ONLY,
            fleet_summary=None,
        )
        self.session.commit()
        self.assertEqual(supplier.onboarding_status, SupplierOnboardingStatus.PENDING_REVIEW)
        self.assertFalse(supplier.is_active)

    def test_admin_approve_reject_routes(self) -> None:
        svc = SupplierOnboardingService()
        supplier, _ = svc.submit_from_telegram(
            self.session,
            telegram_user_id=811_004,
            display_name="Gate Co",
            contact_info="+40444",
            region="RO South",
            service_composition=SupplierServiceComposition.TRANSPORT_WATER,
            fleet_summary=None,
        )
        self.session.commit()
        headers = {"Authorization": "Bearer test-admin-secret"}

        reject = self.client.post(
            f"/admin/suppliers/{supplier.id}/onboarding/reject",
            headers=headers,
            json={"reason": "Need clearer profile"},
        )
        self.assertEqual(reject.status_code, 200, reject.text)
        self.assertEqual(reject.json()["onboarding_status"], "rejected")
        self.assertFalse(reject.json()["is_active"])

        approve = self.client.post(
            f"/admin/suppliers/{supplier.id}/onboarding/approve",
            headers=headers,
        )
        self.assertEqual(approve.status_code, 200, approve.text)
        self.assertEqual(approve.json()["onboarding_status"], "approved")
        self.assertTrue(approve.json()["is_active"])

    def test_rejected_supplier_resubmission_returns_pending(self) -> None:
        svc = SupplierOnboardingService()
        supplier, _ = svc.submit_from_telegram(
            self.session,
            telegram_user_id=811_005,
            display_name="Retry Co",
            contact_info="+40555",
            region="RO East",
            service_composition=SupplierServiceComposition.TRANSPORT_ONLY,
            fleet_summary=None,
        )
        svc.admin_reject(self.session, supplier_id=supplier.id, reason="Need more details")
        again, result = svc.submit_from_telegram(
            self.session,
            telegram_user_id=811_005,
            display_name="Retry Co Updated",
            contact_info="+40555 @retry",
            region="RO East Updated",
            service_composition=SupplierServiceComposition.TRANSPORT_GUIDE_WATER,
            fleet_summary="4 vehicles",
        )
        self.session.commit()
        self.assertEqual(result, "resubmitted")
        self.assertEqual(again.onboarding_status, SupplierOnboardingStatus.PENDING_REVIEW)
        self.assertEqual(again.display_name, "Retry Co Updated")
        self.assertEqual(again.onboarding_service_composition, SupplierServiceComposition.TRANSPORT_GUIDE_WATER)


if __name__ == "__main__":
    unittest.main()
