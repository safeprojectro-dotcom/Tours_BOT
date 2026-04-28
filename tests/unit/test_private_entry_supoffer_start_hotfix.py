"""Hotfix: channel deep-link ``/start supoffer_<id>`` + safe supplier-offer intro (title / deferred language)."""

from __future__ import annotations

import asyncio
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.filters.command import CommandObject

from app.bot.constants import LANGUAGE_CALLBACK_PREFIX
from app.bot.handlers import private_entry
from app.models.enums import SupplierOfferLifecycle, TourStatus
from app.models.supplier import SupplierOfferExecutionLink
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
    message.from_user.username = "u"
    message.from_user.first_name = "T"
    message.from_user.last_name = "U"
    message.from_user.language_code = "en"
    message.chat = MagicMock()
    message.chat.type = "private"
    message.chat.id = 880_000
    message.answer = AsyncMock(return_value=MagicMock(message_id=1))
    message.bot = MagicMock()
    return message


class _DictFSMState:
    """Minimal FSM stand-in for pending start + clear semantics."""

    def __init__(self) -> None:
        self.data: dict = {}

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

    async def set_state(self, *_a: object, **_kw: object) -> None:
        return None


class PrivateEntrySupofferStartHotfixTests(FoundationDBTestCase):
    @staticmethod
    def _run(coro) -> None:
        asyncio.run(coro)

    def test_start_supoffer_published_intro_contains_offer_title(self) -> None:
        self.create_user(telegram_user_id=77_101, preferred_language="en")
        sup = self.create_supplier()
        offer = self.create_supplier_offer(
            sup,
            title="Channel Promo Trip",
            lifecycle_status=SupplierOfferLifecycle.PUBLISHED,
        )
        self.session.commit()
        oid = offer.id

        async def body() -> None:
            message = _private_message(telegram_user_id=77_101)
            state = MagicMock()
            state.clear = AsyncMock()
            cmd = CommandObject(prefix="/", command="start", mention=None, args=f"supoffer_{oid}")
            binder = _SessionLocalBinder(self.session)
            with patch.object(private_entry, "SessionLocal", binder):
                with patch.object(private_entry, "_send_catalog_overview", new_callable=AsyncMock):
                    await private_entry.handle_start(message, state, cmd)

            message.answer.assert_called()
            intro = message.answer.call_args[0][0]
            self.assertIn("Channel Promo Trip", intro)
            self.assertIn("featured offer", intro.lower())

        self._run(body())

    def test_start_supoffer_empty_title_uses_fallback_no_crash(self) -> None:
        self.create_user(telegram_user_id=77_102, preferred_language="en")
        sup = self.create_supplier()
        offer = self.create_supplier_offer(
            sup,
            title="",
            lifecycle_status=SupplierOfferLifecycle.PUBLISHED,
        )
        self.session.commit()
        oid = offer.id

        async def body() -> None:
            message = _private_message(telegram_user_id=77_102)
            state = MagicMock()
            state.clear = AsyncMock()
            cmd = CommandObject(prefix="/", command="start", mention=None, args=f"supoffer_{oid}")
            binder = _SessionLocalBinder(self.session)
            with patch.object(private_entry, "SessionLocal", binder):
                with patch.object(private_entry, "_send_catalog_overview", new_callable=AsyncMock):
                    await private_entry.handle_start(message, state, cmd)

            intro = message.answer.call_args[0][0]
            self.assertIn("Featured offer", intro)

        self._run(body())

    def test_start_supoffer_invalid_or_unpublished_fallback_no_crash(self) -> None:
        self.create_user(telegram_user_id=77_103, preferred_language="en")
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=77_103)
            state = MagicMock()
            state.clear = AsyncMock()
            cmd = CommandObject(prefix="/", command="start", mention=None, args="supoffer_999999")
            binder = _SessionLocalBinder(self.session)
            with patch.object(private_entry, "SessionLocal", binder):
                with patch.object(private_entry, "_send_catalog_overview", new_callable=AsyncMock) as cat:
                    await private_entry.handle_start(message, state, cmd)

            fallback = message.answer.call_args[0][0]
            self.assertIn("not available", fallback.lower())
            cat.assert_awaited_once()

        self._run(body())

    def test_start_without_payload_still_sends_catalog(self) -> None:
        self.create_user(telegram_user_id=77_104, preferred_language="en")
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=77_104)
            state = MagicMock()
            state.clear = AsyncMock()
            cmd = CommandObject(prefix="/", command="start", mention=None, args=None)
            binder = _SessionLocalBinder(self.session)
            with patch.object(private_entry, "SessionLocal", binder):
                with patch.object(private_entry, "_send_catalog_overview", new_callable=AsyncMock) as cat:
                    await private_entry.handle_start(message, state, cmd)

            cat.assert_awaited_once()

        self._run(body())

    def test_start_supoffer_deferred_until_language_selected(self) -> None:
        self.create_user(telegram_user_id=77_105, preferred_language=None)
        sup = self.create_supplier()
        offer = self.create_supplier_offer(
            sup,
            title="Deferred Offer",
            lifecycle_status=SupplierOfferLifecycle.PUBLISHED,
        )
        self.session.commit()
        oid = offer.id

        async def body() -> None:
            message = _private_message(telegram_user_id=77_105)
            # Unsupported Telegram UI language so ``sync_private_user`` does not infer ``preferred_language``.
            message.from_user.language_code = "zz"
            state = _DictFSMState()
            cmd = CommandObject(prefix="/", command="start", mention=None, args=f"supoffer_{oid}")
            binder = _SessionLocalBinder(self.session)
            with patch.object(private_entry, "SessionLocal", binder):
                with patch.object(private_entry, "_send_catalog_overview", new_callable=AsyncMock) as cat:
                    with patch.object(private_entry, "answer_and_register_language_prompt", new_callable=AsyncMock):
                        await private_entry.handle_start(message, state, cmd)

            self.assertEqual(state.data.get(private_entry.PENDING_PRIVATE_START_ARGS_KEY), f"supoffer_{oid}")
            cat.assert_not_awaited()

            cb = MagicMock()
            cb.from_user = message.from_user
            cb.data = f"{LANGUAGE_CALLBACK_PREFIX}en"
            cb.message = message
            cb.answer = AsyncMock()
            with patch.object(private_entry, "SessionLocal", binder):
                with patch.object(private_entry, "_send_catalog_overview", new_callable=AsyncMock) as cat2:
                    await private_entry.handle_language_selected(cb, state)

            texts = [c[0][0] for c in message.answer.call_args_list]
            joined = " ".join(texts)
            self.assertIn("Deferred Offer", joined)
            self.assertGreaterEqual(message.answer.call_count, 2)
            cat2.assert_awaited()

        self._run(body())

    def test_start_supoffer_exact_tour_skips_generic_catalog_overview(self) -> None:
        """B11: active execution link + OPEN_FOR_SALE visible tour — no `_send_catalog_overview` spam."""
        self.create_user(telegram_user_id=77_200, preferred_language="en")
        sup = self.create_supplier()
        departure = datetime.now(UTC) + timedelta(days=21)
        tour = self.create_tour(
            code="B11-SKIP-CAT",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=departure,
            return_datetime=departure + timedelta(days=1),
            sales_deadline=departure - timedelta(days=1),
            seats_available=8,
        )
        offer = self.create_supplier_offer(
            sup,
            title="Router To Tour",
            lifecycle_status=SupplierOfferLifecycle.PUBLISHED,
        )
        self.session.add(
            SupplierOfferExecutionLink(supplier_offer_id=offer.id, tour_id=tour.id, link_status="active")
        )
        self.session.commit()
        oid = offer.id

        async def body() -> None:
            message = _private_message(telegram_user_id=77_200)
            state = MagicMock()
            state.clear = AsyncMock()
            cmd = CommandObject(prefix="/", command="start", mention=None, args=f"supoffer_{oid}")
            binder = _SessionLocalBinder(self.session)
            mock_settings = MagicMock()
            mock_settings.telegram_mini_app_url = "https://mini.example/app"
            mock_settings.telegram_default_language = "en"
            mock_settings.telegram_supported_language_codes = ("en", "ro")
            with patch.object(private_entry, "get_settings", return_value=mock_settings):
                with patch.object(private_entry, "SessionLocal", binder):
                    with patch.object(private_entry, "_send_catalog_overview", new_callable=AsyncMock) as cat:
                        await private_entry.handle_start(message, state, cmd)

            cat.assert_not_awaited()
            intro = message.answer.call_args[0][0]
            self.assertIn("B11-SKIP-CAT", intro)

        self._run(body())


if __name__ == "__main__":
    unittest.main()
