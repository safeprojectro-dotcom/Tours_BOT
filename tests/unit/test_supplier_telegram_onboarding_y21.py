"""Y2.1: supplier Telegram identity binding + onboarding + admin approve/reject gate."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.bot.constants import SUPPLIER_ONBOARDING_NAV_BACK_CALLBACK, SUPPLIER_ONBOARDING_NAV_HOME_CALLBACK
from app.bot.handlers import supplier_onboarding
from app.bot.state import SupplierOnboardingState
from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import SupplierLegalEntityType, SupplierOnboardingStatus, SupplierServiceComposition
from app.services.supplier_onboarding_service import (
    SupplierOnboardingApprovalValidationError,
    SupplierOnboardingService,
)
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


def _callback(*, telegram_user_id: int, data: str, message: MagicMock) -> MagicMock:
    cb = MagicMock()
    cb.from_user = message.from_user
    cb.from_user.id = telegram_user_id
    cb.from_user.language_code = "en"
    cb.data = data
    cb.message = message
    cb.answer = AsyncMock()
    return cb


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

    def test_onboarding_region_moves_to_required_legal_entity_step(self) -> None:
        async def body() -> None:
            message = _private_message(telegram_user_id=811_007)
            message.text = "RO Center"
            state = MagicMock()
            state.update_data = AsyncMock()
            state.set_state = AsyncMock()
            binder = _SessionLocalBinder(self.session)
            with patch.object(supplier_onboarding, "SessionLocal", binder):
                await supplier_onboarding.onboarding_region(message, state)
            state.set_state.assert_awaited_with(SupplierOnboardingState.choosing_legal_entity_type)
            text = message.answer.call_args[0][0].lower()
            self.assertIn("legal entity", text)

        self._run(body())

    def test_onboarding_back_moves_to_previous_step(self) -> None:
        async def body() -> None:
            message = _private_message(telegram_user_id=811_050)
            message.text = "Inapoi"
            state = _DictFSMState()
            await state.set_state(SupplierOnboardingState.entering_contact_info)
            await state.update_data(display_name="RoadJet")
            binder = _SessionLocalBinder(self.session)
            with patch.object(supplier_onboarding, "SessionLocal", binder):
                await supplier_onboarding.onboarding_contact_info(message, state)
            self.assertEqual(state.last_state, SupplierOnboardingState.entering_display_name)
            self.assertEqual(state.data.get("display_name"), "RoadJet")

        self._run(body())

    def test_onboarding_back_preserves_draft_data(self) -> None:
        async def body() -> None:
            message = _private_message(telegram_user_id=811_051)
            message.text = "Inapoi"
            state = _DictFSMState()
            await state.set_state(SupplierOnboardingState.entering_legal_registration_code)
            await state.update_data(
                display_name="RoadJet",
                contact_info="+401",
                region="RO",
                legal_entity_type="company",
                legal_registered_name="RoadJet SRL",
            )
            binder = _SessionLocalBinder(self.session)
            with patch.object(supplier_onboarding, "SessionLocal", binder):
                await supplier_onboarding.onboarding_legal_registration_code(message, state)
            self.assertEqual(state.last_state, SupplierOnboardingState.entering_legal_registered_name)
            self.assertEqual(state.data.get("legal_registered_name"), "RoadJet SRL")
            self.assertEqual(state.data.get("display_name"), "RoadJet")

        self._run(body())

    def test_onboarding_home_clears_state_and_returns_feedback(self) -> None:
        async def body() -> None:
            message = _private_message(telegram_user_id=811_052)
            message.text = "Acasă"
            state = _DictFSMState()
            await state.set_state(SupplierOnboardingState.entering_permit_license_type)
            await state.update_data(display_name="RoadJet", contact_info="+401")
            binder = _SessionLocalBinder(self.session)
            with patch.object(supplier_onboarding, "SessionLocal", binder):
                await supplier_onboarding.onboarding_permit_license_type(message, state)
            self.assertIsNone(state.last_state)
            self.assertEqual(state.data, {})
            all_text = "\n".join(c.args[0].lower() for c in message.answer.call_args_list if c.args)
            self.assertIn("cancelled", all_text)

        self._run(body())

    def test_onboarding_choice_step_supports_nav_callbacks(self) -> None:
        async def body() -> None:
            state = _DictFSMState()
            await state.set_state(SupplierOnboardingState.choosing_legal_entity_type)
            await state.update_data(display_name="RoadJet", contact_info="+401", region="RO")
            message = _private_message(telegram_user_id=811_053)
            cb_back = _callback(
                telegram_user_id=811_053,
                data=SUPPLIER_ONBOARDING_NAV_BACK_CALLBACK,
                message=message,
            )
            binder = _SessionLocalBinder(self.session)
            with patch.object(supplier_onboarding, "SessionLocal", binder):
                await supplier_onboarding.onboarding_nav_callback(cb_back, state)
            self.assertEqual(state.last_state, SupplierOnboardingState.entering_region)
            self.assertEqual(state.data.get("display_name"), "RoadJet")
            cb_home = _callback(
                telegram_user_id=811_053,
                data=SUPPLIER_ONBOARDING_NAV_HOME_CALLBACK,
                message=message,
            )
            with patch.object(supplier_onboarding, "SessionLocal", binder):
                await supplier_onboarding.onboarding_nav_callback(cb_home, state)
            self.assertIsNone(state.last_state)
            self.assertEqual(state.data, {})

        self._run(body())

    def test_onboarding_finish_submit_path_still_works(self) -> None:
        async def body() -> None:
            state = _DictFSMState()
            await state.set_state(SupplierOnboardingState.entering_fleet_summary)
            await state.update_data(
                display_name="Finish Co",
                contact_info="+40777 @finish",
                region="RO West",
                legal_entity_type="company",
                legal_registered_name="Finish Co SRL",
                legal_registration_code="ROFIN777",
                permit_license_type="Road transport permit",
                permit_license_number="RTP-777",
                service_composition="transport_only",
            )
            message = _private_message(telegram_user_id=811_054)
            message.text = "2 buses"
            binder = _SessionLocalBinder(self.session)
            with patch.object(supplier_onboarding, "SessionLocal", binder):
                await supplier_onboarding.onboarding_finish(message, state)
            supplier = SupplierOnboardingService().get_by_telegram_user_id(self.session, telegram_user_id=811_054)
            self.assertIsNotNone(supplier)
            assert supplier is not None
            self.assertEqual(supplier.onboarding_status, SupplierOnboardingStatus.PENDING_REVIEW)
            self.assertEqual(supplier.legal_registration_code, "ROFIN777")
            self.assertIsNone(state.last_state)
            self.assertEqual(state.data, {})

        self._run(body())

    def test_supplier_command_pending_user_gets_status_message(self) -> None:
        SupplierOnboardingService().submit_from_telegram(
            self.session,
            telegram_user_id=811_010,
            display_name="Pending Bot Co",
            contact_info="+4010",
            region="RO",
            legal_entity_type=SupplierLegalEntityType.COMPANY,
            legal_registered_name="Pending Bot Co SRL",
            legal_registration_code="RO123456",
            permit_license_type="Transport license",
            permit_license_number="TL-100",
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
            legal_entity_type=SupplierLegalEntityType.COMPANY,
            legal_registered_name="RoadJet SRL",
            legal_registration_code="RO555001",
            permit_license_type="Road carrier license",
            permit_license_number="RC-2026-01",
            service_composition=SupplierServiceComposition.TRANSPORT_GUIDE,
            fleet_summary="2 buses",
        )
        self.session.commit()
        self.assertEqual(result, "submitted")
        self.assertEqual(supplier.primary_telegram_user_id, 811_002)
        self.assertEqual(supplier.onboarding_status, SupplierOnboardingStatus.PENDING_REVIEW)
        self.assertEqual(supplier.onboarding_service_composition, SupplierServiceComposition.TRANSPORT_GUIDE)
        self.assertEqual(supplier.legal_entity_type, SupplierLegalEntityType.COMPANY)
        self.assertEqual(supplier.legal_registration_code, "RO555001")
        self.assertFalse(supplier.is_active)

    def test_pending_supplier_is_not_approved(self) -> None:
        svc = SupplierOnboardingService()
        supplier, _ = svc.submit_from_telegram(
            self.session,
            telegram_user_id=811_003,
            display_name="Pending Co",
            contact_info="+4000000",
            region="RO",
            legal_entity_type=SupplierLegalEntityType.INDIVIDUAL_ENTREPRENEUR,
            legal_registered_name="Pending Co PFA",
            legal_registration_code="ROPFA777",
            permit_license_type="Local permit",
            permit_license_number="LP-777",
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
            legal_entity_type=SupplierLegalEntityType.AUTHORIZED_CARRIER,
            legal_registered_name="Gate Carrier SA",
            legal_registration_code="ROGATE444",
            permit_license_type="Carrier authorization",
            permit_license_number="CA-444",
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
        self.assertEqual(approve.json()["legal_registration_code"], "ROGATE444")
        self.assertTrue(approve.json()["is_active"])

    def test_admin_supplier_read_includes_legal_identity_fields(self) -> None:
        svc = SupplierOnboardingService()
        supplier, _ = svc.submit_from_telegram(
            self.session,
            telegram_user_id=811_006,
            display_name="Legal View Co",
            contact_info="+40666",
            region="RO North",
            legal_entity_type=SupplierLegalEntityType.COMPANY,
            legal_registered_name="Legal View SRL",
            legal_registration_code="ROVIEW666",
            permit_license_type="Tour transport permit",
            permit_license_number="TTP-666",
            service_composition=SupplierServiceComposition.TRANSPORT_ONLY,
            fleet_summary=None,
        )
        self.session.commit()
        headers = {"Authorization": "Bearer test-admin-secret"}
        resp = self.client.get(f"/admin/suppliers/{supplier.id}", headers=headers)
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body["legal_entity_type"], "company")
        self.assertEqual(body["legal_registered_name"], "Legal View SRL")
        self.assertEqual(body["legal_registration_code"], "ROVIEW666")
        self.assertEqual(body["permit_license_type"], "Tour transport permit")
        self.assertEqual(body["permit_license_number"], "TTP-666")

    def test_rejected_supplier_resubmission_returns_pending(self) -> None:
        svc = SupplierOnboardingService()
        supplier, _ = svc.submit_from_telegram(
            self.session,
            telegram_user_id=811_005,
            display_name="Retry Co",
            contact_info="+40555",
            region="RO East",
            legal_entity_type=SupplierLegalEntityType.COMPANY,
            legal_registered_name="Retry Co SRL",
            legal_registration_code="RORETRY1",
            permit_license_type="Transport license",
            permit_license_number="TRL-1",
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
            legal_entity_type=SupplierLegalEntityType.AUTHORIZED_CARRIER,
            legal_registered_name="Retry Co Updated SA",
            legal_registration_code="RORETRY2",
            permit_license_type="Carrier permit",
            permit_license_number="CP-2",
            service_composition=SupplierServiceComposition.TRANSPORT_GUIDE_WATER,
            fleet_summary="4 vehicles",
        )
        self.session.commit()
        self.assertEqual(result, "resubmitted")
        self.assertEqual(again.onboarding_status, SupplierOnboardingStatus.PENDING_REVIEW)
        self.assertEqual(again.display_name, "Retry Co Updated")
        self.assertEqual(again.legal_registration_code, "RORETRY2")
        self.assertEqual(again.onboarding_service_composition, SupplierServiceComposition.TRANSPORT_GUIDE_WATER)

    def test_admin_approve_requires_legal_identity_for_pending_supplier(self) -> None:
        supplier = self.create_supplier(
            code="Y21A-MISS",
            display_name="Missing Legal",
            is_active=False,
            onboarding_status=SupplierOnboardingStatus.PENDING_REVIEW,
            primary_telegram_user_id=811_099,
        )
        self.session.commit()
        with self.assertRaises(SupplierOnboardingApprovalValidationError):
            SupplierOnboardingService().admin_approve(self.session, supplier_id=supplier.id)


if __name__ == "__main__":
    unittest.main()
