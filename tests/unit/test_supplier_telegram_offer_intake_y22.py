"""Y2.2a: supplier Telegram offer intake polish (navigation, validation, submit boundary)."""

from __future__ import annotations

import asyncio
import unittest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.bot.constants import SUPPLIER_OFFER_PAYMENT_MODE_CALLBACK_PREFIX, SUPPLIER_OFFER_SUBMIT_CALLBACK_PREFIX
from app.bot.handlers import supplier_offer_intake
from app.bot.state import SupplierOfferIntakeState
from app.models.enums import (
    SupplierOfferLifecycle,
    SupplierOfferPaymentMode,
    SupplierOnboardingStatus,
    SupplierServiceComposition,
    TourSalesMode,
)
from app.services.supplier_offer_service import SupplierOfferService
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
    message.from_user.username = "supplier_user"
    message.from_user.first_name = "Sup"
    message.from_user.last_name = "User"
    message.from_user.language_code = "en"
    message.chat = MagicMock()
    message.chat.type = "private"
    message.chat.id = 888_000
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


class SupplierTelegramOfferIntakeY22Tests(FoundationDBTestCase):
    @staticmethod
    def _run(coro) -> None:
        asyncio.run(coro)

    def test_approved_supplier_can_enter_offer_intake(self) -> None:
        self.create_supplier(
            code="Y22-APP",
            display_name="Approved",
            is_active=True,
            primary_telegram_user_id=912_001,
            onboarding_status=SupplierOnboardingStatus.APPROVED,
            onboarding_service_composition=SupplierServiceComposition.TRANSPORT_ONLY,
            onboarding_submitted_at=datetime.now(UTC),
            onboarding_reviewed_at=datetime.now(UTC),
        )
        self.session.commit()

        async def body() -> None:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=912_001)
            with patch.object(supplier_offer_intake, "SessionLocal", _SessionLocalBinder(self.session)):
                await supplier_offer_intake.cmd_supplier_offer(message, state)
            all_texts = [c.args[0].lower() for c in message.answer.call_args_list]
            self.assertTrue(any("supplier offer intake" in t for t in all_texts))
            self.assertIsNotNone(state.last_state)

        self._run(body())

    def test_pending_or_rejected_supplier_cannot_enter_approved_offer_flow(self) -> None:
        self.create_supplier(
            code="Y22-PEN",
            display_name="Pending",
            is_active=False,
            primary_telegram_user_id=912_002,
            onboarding_status=SupplierOnboardingStatus.PENDING_REVIEW,
        )
        self.create_supplier(
            code="Y22-REJ",
            display_name="Rejected",
            is_active=False,
            primary_telegram_user_id=912_003,
            onboarding_status=SupplierOnboardingStatus.REJECTED,
        )
        self.session.commit()

        async def body(tg: int) -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=tg)
            with patch.object(supplier_offer_intake, "SessionLocal", _SessionLocalBinder(self.session)):
                await supplier_offer_intake.cmd_supplier_offer(message, state)
            return message.answer.call_args[0][0].lower()

        txt_pending = asyncio.run(body(912_002))
        txt_rejected = asyncio.run(body(912_003))
        self.assertIn("pending", txt_pending)
        self.assertIn("rejected", txt_rejected)

    def test_not_onboarded_user_is_gated_from_offer_intake(self) -> None:
        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=912_009)
            with patch.object(supplier_offer_intake, "SessionLocal", _SessionLocalBinder(self.session)):
                await supplier_offer_intake.cmd_supplier_offer(message, state)
            return message.answer.call_args[0][0].lower()

        text = asyncio.run(body())
        self.assertIn("onboarding", text)

    def test_back_navigation_works_safely(self) -> None:
        async def body() -> None:
            state = _DictFSMState()
            await state.set_state(SupplierOfferIntakeState.entering_description)
            message = _private_message(telegram_user_id=912_010)
            message.text = "inapoi"
            with patch.object(supplier_offer_intake, "SessionLocal", _SessionLocalBinder(self.session)):
                await supplier_offer_intake.intake_description(message, state)
            self.assertEqual(state.last_state, SupplierOfferIntakeState.entering_title)

        self._run(body())

    def test_home_navigation_resets_flow_safely(self) -> None:
        async def body() -> None:
            state = _DictFSMState()
            await state.set_state(SupplierOfferIntakeState.entering_departure_point)
            await state.update_data(title="Draft title")
            message = _private_message(telegram_user_id=912_011)
            message.text = "Acasă"
            with patch.object(supplier_offer_intake, "SessionLocal", _SessionLocalBinder(self.session)):
                await supplier_offer_intake.intake_departure_point(message, state)
            self.assertIsNone(state.last_state)
            self.assertEqual(state.data, {})

        self._run(body())

    def test_invalid_datetime_is_rejected_clearly(self) -> None:
        async def body() -> None:
            state = _DictFSMState()
            await state.set_state(SupplierOfferIntakeState.entering_departure_datetime)
            message = _private_message(telegram_user_id=912_012)
            message.text = "2026-12-01"
            with patch.object(supplier_offer_intake, "SessionLocal", _SessionLocalBinder(self.session)):
                await supplier_offer_intake.intake_departure(message, state)
            text = message.answer.call_args[0][0].lower()
            self.assertIn("date/time", text)
            self.assertEqual(state.last_state, SupplierOfferIntakeState.entering_departure_datetime)

        self._run(body())

    def test_invalid_currency_is_rejected_clearly(self) -> None:
        async def body() -> None:
            state = _DictFSMState()
            await state.set_state(SupplierOfferIntakeState.entering_currency)
            message = _private_message(telegram_user_id=912_013)
            message.text = "EURO"
            with patch.object(supplier_offer_intake, "SessionLocal", _SessionLocalBinder(self.session)):
                await supplier_offer_intake.intake_currency(message, state)
            text = message.answer.call_args[0][0].lower()
            self.assertIn("3-letter", text)
            self.assertEqual(state.last_state, SupplierOfferIntakeState.entering_currency)

        self._run(body())

    def test_price_prompt_changes_based_on_sales_mode(self) -> None:
        async def body(sales_mode: TourSalesMode) -> str:
            state = _DictFSMState()
            await state.set_state(SupplierOfferIntakeState.choosing_payment_mode)
            await state.update_data(sales_mode=sales_mode.value)
            message = _private_message(telegram_user_id=912_014)
            cb = _callback(
                telegram_user_id=912_014,
                data=f"{SUPPLIER_OFFER_PAYMENT_MODE_CALLBACK_PREFIX}{SupplierOfferPaymentMode.PLATFORM_CHECKOUT.value}",
                message=message,
            )
            with patch.object(supplier_offer_intake, "SessionLocal", _SessionLocalBinder(self.session)):
                await supplier_offer_intake.intake_payment_mode(cb, state)
            return message.answer.call_args[0][0].lower()

        per_seat = asyncio.run(body(TourSalesMode.PER_SEAT))
        full_bus = asyncio.run(body(TourSalesMode.FULL_BUS))
        self.assertIn("per seat", per_seat)
        self.assertIn("full-bus", full_bus)

    def test_draft_persists_and_submit_moves_to_moderation_ready(self) -> None:
        supplier = self.create_supplier(
            code="Y22-SUB",
            display_name="Submit Co",
            is_active=True,
            primary_telegram_user_id=912_004,
            onboarding_status=SupplierOnboardingStatus.APPROVED,
            onboarding_service_composition=SupplierServiceComposition.TRANSPORT_GUIDE,
            onboarding_submitted_at=datetime.now(UTC),
            onboarding_reviewed_at=datetime.now(UTC),
        )
        self.session.commit()
        supplier_id = supplier.id

        async def body() -> None:
            state = _DictFSMState()
            await state.update_data(
                title="Telegram Offer",
                description="Short route description",
                departure_point="Chisinau",
                departure_datetime="2026-10-01T08:00:00+00:00",
                return_datetime="2026-10-02T18:00:00+00:00",
                seats_total=40,
                sales_mode="per_seat",
                payment_mode="platform_checkout",
                base_price="120.00",
                currency="EUR",
                program_text="Program details",
            )
            message = _private_message(telegram_user_id=912_004)
            message.text = "Coach 50"
            with patch.object(supplier_offer_intake, "SessionLocal", _SessionLocalBinder(self.session)):
                await supplier_offer_intake.intake_vehicle_or_notes(message, state)
            offers = SupplierOfferService().list_offers(self.session, supplier_id=supplier_id, limit=20, offset=0)
            self.assertEqual(len(offers), 1)
            self.assertEqual(offers[0].lifecycle_status, SupplierOfferLifecycle.DRAFT)
            offer_id = offers[0].id
            cb = _callback(
                telegram_user_id=912_004,
                data=f"{SUPPLIER_OFFER_SUBMIT_CALLBACK_PREFIX}{offer_id}",
                message=message,
            )
            with patch.object(supplier_offer_intake, "SessionLocal", _SessionLocalBinder(self.session)):
                await supplier_offer_intake.submit_offer_to_moderation(cb, state)
            after = SupplierOfferService().list_offers(self.session, supplier_id=supplier_id, limit=20, offset=0)
            self.assertEqual(after[0].lifecycle_status, SupplierOfferLifecycle.READY_FOR_MODERATION)

        self._run(body())

    def test_repeat_reentry_updates_existing_draft_instead_of_creating_duplicates(self) -> None:
        supplier = self.create_supplier(
            code="Y22-REP",
            display_name="Repeat Co",
            is_active=True,
            primary_telegram_user_id=912_005,
            onboarding_status=SupplierOnboardingStatus.APPROVED,
            onboarding_service_composition=SupplierServiceComposition.TRANSPORT_ONLY,
            onboarding_submitted_at=datetime.now(UTC),
            onboarding_reviewed_at=datetime.now(UTC),
        )
        self.session.commit()
        supplier_id = supplier.id

        async def persist_one(title: str) -> None:
            state = _DictFSMState()
            await state.update_data(
                title=title,
                description="Desc",
                departure_point="Iasi",
                departure_datetime="2026-11-01T09:00:00+00:00",
                return_datetime="2026-11-02T20:00:00+00:00",
                seats_total=30,
                sales_mode="per_seat",
                payment_mode="platform_checkout",
                base_price="99.00",
                currency="EUR",
                program_text="Program",
            )
            message = _private_message(telegram_user_id=912_005)
            message.text = "Vehicle Label"
            with patch.object(supplier_offer_intake, "SessionLocal", _SessionLocalBinder(self.session)):
                await supplier_offer_intake.intake_vehicle_or_notes(message, state)

        self._run(persist_one("Draft one"))
        self._run(persist_one("Draft updated"))
        offers = SupplierOfferService().list_offers(self.session, supplier_id=supplier_id, limit=20, offset=0)
        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0].title, "Draft updated")
        self.assertEqual(offers[0].lifecycle_status, SupplierOfferLifecycle.DRAFT)


if __name__ == "__main__":
    unittest.main()
