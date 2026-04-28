"""B10.6B: generic ``/start`` and ``/tours`` router-first (no automatic in-chat tour cards)."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.filters.command import CommandObject

from app.bot.handlers import private_entry
from app.models.enums import SupplierOfferLifecycle, TourStatus
from app.models.supplier import SupplierOfferExecutionLink
from tests.unit.base import FoundationDBTestCase


def _run(coro: object) -> None:
    asyncio.run(coro)  # type: ignore[arg-type]


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
    message.chat.id = 901_000
    message.answer = AsyncMock(return_value=MagicMock(message_id=1))
    message.bot = MagicMock()
    message.bot.delete_message = AsyncMock()
    return message


class _SessionLocalBinder:
    def __init__(self, session: object) -> None:
        self._session = session

    def __call__(self) -> object:
        return self._session


class RouterFirstB106BTests(FoundationDBTestCase):
    def test_generic_start_calls_router_home_not_catalog_overview(self) -> None:
        self.create_user(telegram_user_id=661_001, preferred_language="en")
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=661_001)
            state = MagicMock()
            state.clear = AsyncMock()
            cmd = CommandObject(prefix="/", command="start", mention=None, args=None)
            binder = _SessionLocalBinder(self.session)
            router_home = AsyncMock()
            catalog = AsyncMock()
            with patch.object(private_entry, "SessionLocal", binder):
                with patch.object(private_entry, "_send_router_home", router_home):
                    with patch.object(private_entry, "_send_catalog_overview", catalog):
                        await private_entry.handle_start(message, state, cmd)

            router_home.assert_awaited_once()
            catalog.assert_not_awaited()

        _run(body())

    def test_tours_command_calls_router_home_not_catalog(self) -> None:
        self.create_user(telegram_user_id=661_002, preferred_language="ro")
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=661_002)
            state = MagicMock()
            state.clear = AsyncMock()
            binder = _SessionLocalBinder(self.session)
            router_home = AsyncMock()
            catalog = AsyncMock()
            with patch.object(private_entry, "SessionLocal", binder):
                with patch.object(private_entry, "_send_router_home", router_home):
                    with patch.object(private_entry, "_send_catalog_overview", catalog):
                        await private_entry.handle_tours_command(message, state)

            router_home.assert_awaited_once()
            catalog.assert_not_awaited()

        _run(body())

    def test_generic_start_router_cta_includes_mini_app_catalog_url(self) -> None:
        """Requirement: primary WebApp to catalog root (not automatic tour cards)."""
        self.create_user(telegram_user_id=661_003, preferred_language="en")
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=661_003)
            state = MagicMock()
            state.clear = AsyncMock()
            cmd = CommandObject(prefix="/", command="start", mention=None, args=None)
            binder = _SessionLocalBinder(self.session)
            captures: dict[str, object] = {}

            async def capture_router(
                m: object,
                *,
                text: str,
                reply_markup: object,
                prefer_edit: bool,
            ) -> None:
                captures["text"] = text
                captures["reply_markup"] = reply_markup

            mock_settings = MagicMock()
            mock_settings.telegram_mini_app_url = "https://mini.example/app/"
            mock_settings.telegram_supported_language_codes = ("en", "ro", "ru", "sr", "hu", "it", "de")
            with patch.object(private_entry, "get_settings", return_value=mock_settings):
                with patch.object(private_entry, "SessionLocal", binder):
                    with patch.object(private_entry, "send_or_edit_router_home", capture_router):
                        await private_entry.handle_start(message, state, cmd)

            base = "https://mini.example/app".rstrip("/")
            self.assertIn("Mini App", captures["text"] or "")
            markup = captures["reply_markup"]
            urls = [
                b.web_app.url
                for row in markup.inline_keyboard  # type: ignore[union-attr]
                for b in row
                if b.web_app is not None
            ]
            self.assertTrue(any(u.startswith(base) for u in urls))
            bookings = f"{base}/bookings"
            self.assertTrue(any(u == bookings for u in urls))

        _run(body())

    def test_start_tour_code_calls_detail_not_router_catalog(self) -> None:
        """B10.6 first slice unchanged: exact tour → detail message, no generic router/catalog."""
        self.create_user(telegram_user_id=661_004, preferred_language="en")
        tour = self.create_tour(code="RT-B106B-1", title_default="T", status=TourStatus.OPEN_FOR_SALE)
        self.create_translation(tour, language_code="en", title="Tour detail title")
        self.create_boarding_point(tour)
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=661_004)
            state = MagicMock()
            state.clear = AsyncMock()
            cmd = CommandObject(prefix="/", command="start", mention=None, args="tour_RT-B106B-1")
            binder = _SessionLocalBinder(self.session)
            router_home = AsyncMock()
            catalog = AsyncMock()
            mock_settings = MagicMock()
            mock_settings.telegram_mini_app_url = "https://mini.example/app/"
            mock_settings.telegram_supported_language_codes = ("en", "ro", "ru", "sr", "hu", "it", "de")
            with patch.object(private_entry, "get_settings", return_value=mock_settings):
                with patch.object(private_entry, "SessionLocal", binder):
                    with patch.object(private_entry, "_send_router_home", router_home):
                        with patch.object(private_entry, "_send_catalog_overview", catalog):
                            await private_entry.handle_start(message, state, cmd)

            router_home.assert_not_awaited()
            catalog.assert_not_awaited()
            sent = message.answer.call_args[0][0]
            self.assertIn("Tour detail title", sent)

        _run(body())

    def test_start_supoffer_exact_skips_router_home_and_catalog(self) -> None:
        """B11 unchanged: exact Mini App path — no router spam."""
        from datetime import UTC, datetime, timedelta

        self.create_user(telegram_user_id=661_005, preferred_language="en")
        sup = self.create_supplier()
        departure = datetime.now(UTC) + timedelta(days=21)
        tour = self.create_tour(
            code="B106B-SOFF",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=departure,
            return_datetime=departure + timedelta(days=1),
            sales_deadline=departure - timedelta(days=1),
            seats_available=8,
        )
        offer = self.create_supplier_offer(
            sup,
            title="Featured",
            lifecycle_status=SupplierOfferLifecycle.PUBLISHED,
        )
        self.session.add(
            SupplierOfferExecutionLink(supplier_offer_id=offer.id, tour_id=tour.id, link_status="active")
        )
        self.session.commit()
        oid = offer.id

        async def body() -> None:
            message = _private_message(telegram_user_id=661_005)
            state = MagicMock()
            state.clear = AsyncMock()
            cmd = CommandObject(prefix="/", command="start", mention=None, args=f"supoffer_{oid}")
            binder = _SessionLocalBinder(self.session)
            router_home = AsyncMock()
            catalog = AsyncMock()
            mock_settings = MagicMock()
            mock_settings.telegram_mini_app_url = "https://mini.example/app"
            mock_settings.telegram_default_language = "en"
            mock_settings.telegram_supported_language_codes = ("en", "ro")
            with patch.object(private_entry, "get_settings", return_value=mock_settings):
                with patch.object(private_entry, "SessionLocal", binder):
                    with patch.object(private_entry, "_send_router_home", router_home):
                        with patch.object(private_entry, "_send_catalog_overview", catalog):
                            await private_entry.handle_start(message, state, cmd)

            router_home.assert_not_awaited()
            catalog.assert_not_awaited()

        _run(body())


if __name__ == "__main__":
    unittest.main()
