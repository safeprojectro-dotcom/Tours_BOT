"""Y28.1: Telegram admin moderation workspace (allowlist + queue/actions)."""

from __future__ import annotations

import asyncio
import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.bot.constants import (
    ADMIN_OFFERS_ACTION_APPROVE,
    ADMIN_OFFERS_ACTION_CALLBACK_PREFIX,
    ADMIN_OFFERS_ACTION_CLOSE_LINK,
    ADMIN_OFFERS_ACTION_CONFIRM_CREATE_LINK,
    ADMIN_OFFERS_ACTION_CONFIRM_REPLACE_LINK,
    ADMIN_OFFERS_ACTION_CREATE_LINK,
    ADMIN_OFFERS_ACTION_LINK_STATUS,
    ADMIN_OFFERS_ACTION_PUBLISH,
    ADMIN_OFFERS_ACTION_REJECT,
    ADMIN_OFFERS_ACTION_REPLACE_LINK,
    ADMIN_OFFERS_ACTION_RETRACT,
)
from app.bot.handlers import admin_moderation
from app.core.config import get_settings
from app.models.enums import SupplierOfferLifecycle, SupplierOfferPaymentMode, TourSalesMode
from app.models.supplier import SupplierOfferExecutionLink
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
    message.chat.id = 777_000
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


class TelegramAdminModerationY281Tests(FoundationDBTestCase):
    @staticmethod
    def _run(coro) -> None:
        asyncio.run(coro)

    def setUp(self) -> None:
        super().setUp()
        self._orig_allowlist = get_settings().telegram_admin_allowlist_user_ids
        get_settings().telegram_admin_allowlist_user_ids = "990001"

    def tearDown(self) -> None:
        get_settings().telegram_admin_allowlist_user_ids = self._orig_allowlist
        super().tearDown()

    def _create_offer(self, *, lifecycle: SupplierOfferLifecycle) -> int:
        idx = self._next()
        supplier = self.create_supplier(
            code=f"Y281-{lifecycle.value}-{idx}",
            display_name="Moderation Supplier",
            is_active=True,
        )
        offer = self.create_supplier_offer(
            supplier,
            title=f"Offer {lifecycle.value}",
            description="Route text",
            lifecycle_status=lifecycle,
            payment_mode=SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
            sales_mode=TourSalesMode.PER_SEAT,
            departure_datetime=datetime.now(UTC).replace(second=0, microsecond=0),
            return_datetime=datetime.now(UTC).replace(second=0, microsecond=0),
        )
        self.session.commit()
        return offer.id

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

    def test_non_allowlisted_telegram_user_is_denied(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.READY_FOR_MODERATION)
        self.assertGreater(offer_id, 0)

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990099)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_offers(message, state)
            return message.answer.call_args[0][0].lower()

        text = asyncio.run(body())
        self.assertIn("not available", text)

    def test_allowlisted_admin_can_open_queue(self) -> None:
        self._create_offer(lifecycle=SupplierOfferLifecycle.READY_FOR_MODERATION)

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_offers(message, state)
            all_text = "\n".join(c.args[0].lower() for c in message.answer.call_args_list if c.args)
            return all_text

        text = asyncio.run(body())
        self.assertIn("admin moderation queue", text)
        self.assertIn("offer #", text)

    def test_admin_queue_shows_ready_for_moderation_only(self) -> None:
        ready_id = self._create_offer(lifecycle=SupplierOfferLifecycle.READY_FOR_MODERATION)
        approved_id = self._create_offer(lifecycle=SupplierOfferLifecycle.APPROVED)
        published_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_offers(message, state)
            return self._all_answer_texts(message)

        text = asyncio.run(body())
        self.assertIn(f"#{ready_id}", text)
        self.assertNotIn(f"#{approved_id}", text)
        self.assertNotIn(f"#{published_id}", text)

    def test_admin_approved_shows_approved_unpublished_offers(self) -> None:
        ready_id = self._create_offer(lifecycle=SupplierOfferLifecycle.READY_FOR_MODERATION)
        approved_id = self._create_offer(lifecycle=SupplierOfferLifecycle.APPROVED)
        published_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_approved(message, state)
            return self._all_answer_texts(message)

        text = asyncio.run(body())
        self.assertIn("approved / unpublished queue", text)
        self.assertIn(f"#{approved_id}", text)
        self.assertNotIn(f"#{ready_id}", text)
        self.assertNotIn(f"#{published_id}", text)

    def test_admin_published_shows_published_offers(self) -> None:
        ready_id = self._create_offer(lifecycle=SupplierOfferLifecycle.READY_FOR_MODERATION)
        approved_id = self._create_offer(lifecycle=SupplierOfferLifecycle.APPROVED)
        published_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_published(message, state)
            return self._all_answer_texts(message)

        text = asyncio.run(body())
        self.assertIn("published queue", text)
        self.assertIn(f"#{published_id}", text)
        self.assertNotIn(f"#{ready_id}", text)
        self.assertNotIn(f"#{approved_id}", text)

    def test_publish_action_available_only_in_approved_unpublished_view(self) -> None:
        approved_id = self._create_offer(lifecycle=SupplierOfferLifecycle.APPROVED)
        published_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)

        async def body_approved() -> list[str]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_approved(message, state)
            return self._inline_button_texts(message)

        async def body_published() -> list[str]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_published(message, state)
            return self._inline_button_texts(message)

        approved_buttons = asyncio.run(body_approved())
        published_buttons = asyncio.run(body_published())
        self.assertGreater(approved_id, 0)
        self.assertGreater(published_id, 0)
        self.assertIn("publish", approved_buttons)
        self.assertNotIn("retract", approved_buttons)
        self.assertIn("retract", published_buttons)
        self.assertIn("execution link", published_buttons)
        self.assertNotIn("publish", published_buttons)

    def test_admin_can_view_execution_link_status_and_history(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        tour = self.create_tour(code="TG-LINK-STATUS", sales_mode=TourSalesMode.PER_SEAT)
        self.session.add(SupplierOfferExecutionLink(supplier_offer_id=offer_id, tour_id=tour.id, link_status="active"))
        self.session.commit()

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            cb = _callback(
                telegram_user_id=990001,
                data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_LINK_STATUS}:{offer_id}",
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(cb, state)
            return self._all_answer_texts(message), self._inline_button_texts(message)

        text, buttons = asyncio.run(body())
        self.assertIn("execution link status", text)
        self.assertIn("active link", text)
        self.assertIn("tg-link-status", text)
        self.assertIn("link history", text)
        self.assertIn("replace execution link", buttons)
        self.assertIn("close active link", buttons)

    def test_admin_can_create_execution_link_from_explicit_tour_input(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        tour = self.create_tour(code="TG-LINK-CREATE", sales_mode=TourSalesMode.PER_SEAT)
        self.session.commit()

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            start_cb = _callback(
                telegram_user_id=990001,
                data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_CREATE_LINK}:{offer_id}",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = str(tour.id)
            confirm_cb = _callback(
                telegram_user_id=990001,
                data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_CONFIRM_CREATE_LINK}:{offer_id}",
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(start_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_input(input_message, state)
                await admin_moderation.admin_offer_action(confirm_cb, state)
            return "\n".join(
                [self._all_answer_texts(message), self._all_answer_texts(input_message)]
            )

        text = asyncio.run(body())
        self.assertIn("send existing tour_id", text)
        self.assertIn("confirm execution link target", text)
        self.assertIn("mini app cta appears only", text)
        self.assertIn("execution link created", text)
        links = self.session.query(SupplierOfferExecutionLink).filter_by(supplier_offer_id=offer_id).all()
        active = [link for link in links if link.link_status == "active"]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].tour_id, tour.id)

    def test_admin_can_replace_execution_link_and_old_link_is_closed(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        old_tour = self.create_tour(code="TG-LINK-OLD", sales_mode=TourSalesMode.PER_SEAT)
        new_tour = self.create_tour(code="TG-LINK-NEW", sales_mode=TourSalesMode.PER_SEAT)
        old_tour_id = old_tour.id
        new_tour_id = new_tour.id
        new_tour_code = new_tour.code
        self.session.add(SupplierOfferExecutionLink(supplier_offer_id=offer_id, tour_id=old_tour.id, link_status="active"))
        self.session.commit()

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            start_cb = _callback(
                telegram_user_id=990001,
                data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_REPLACE_LINK}:{offer_id}",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = new_tour_code
            confirm_cb = _callback(
                telegram_user_id=990001,
                data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_CONFIRM_REPLACE_LINK}:{offer_id}",
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(start_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_input(input_message, state)
                await admin_moderation.admin_offer_action(confirm_cb, state)
            return "\n".join(
                [self._all_answer_texts(message), self._all_answer_texts(input_message)]
            )

        text = asyncio.run(body())
        self.assertIn("confirm execution link target", text)
        self.assertIn("execution link replaced", text)
        links = self.session.query(SupplierOfferExecutionLink).filter_by(supplier_offer_id=offer_id).all()
        active = [link for link in links if link.link_status == "active"]
        closed = [link for link in links if link.link_status == "closed"]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].tour_id, new_tour_id)
        self.assertEqual(len(closed), 1)
        self.assertEqual(closed[0].tour_id, old_tour_id)
        self.assertEqual(closed[0].close_reason, "replaced")

    def test_admin_execution_link_tour_input_blocks_sales_mode_mismatch(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        mismatched_tour = self.create_tour(code="TG-LINK-MISMATCH", sales_mode=TourSalesMode.FULL_BUS)
        self.session.commit()

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            start_cb = _callback(
                telegram_user_id=990001,
                data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_CREATE_LINK}:{offer_id}",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = str(mismatched_tour.id)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(start_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_input(input_message, state)
            return "\n".join(
                [self._all_answer_texts(message), self._all_answer_texts(input_message)]
            )

        text = asyncio.run(body())
        self.assertIn("sales_mode must match", text)
        links = self.session.query(SupplierOfferExecutionLink).filter_by(supplier_offer_id=offer_id).all()
        self.assertEqual(links, [])

    def test_admin_can_close_active_execution_link_from_status_screen(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        tour = self.create_tour(code="TG-LINK-CLOSE", sales_mode=TourSalesMode.PER_SEAT)
        self.session.add(SupplierOfferExecutionLink(supplier_offer_id=offer_id, tour_id=tour.id, link_status="active"))
        self.session.commit()

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            cb = _callback(
                telegram_user_id=990001,
                data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_CLOSE_LINK}:{offer_id}",
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(cb, state)
            return self._all_answer_texts(message)

        text = asyncio.run(body())
        self.assertIn("closed", text)
        self.assertIn("no active execution link", text)
        links = self.session.query(SupplierOfferExecutionLink).filter_by(supplier_offer_id=offer_id).all()
        self.assertEqual([link for link in links if link.link_status == "active"], [])
        self.assertEqual(links[0].close_reason, "unlinked")

    def test_admin_can_approve_from_allowed_state(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.READY_FOR_MODERATION)

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            cb = _callback(
                telegram_user_id=990001,
                data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_APPROVE}:{offer_id}",
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(cb, state)
            row = admin_moderation.SupplierOfferModerationService()._offers.get_any(self.session, offer_id=offer_id)
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row.lifecycle_status, SupplierOfferLifecycle.APPROVED)
            return "\n".join(c.args[0].lower() for c in message.answer.call_args_list if c.args)

        text = asyncio.run(body())
        self.assertIn("approved", text)

    def test_admin_can_reject_with_reason(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.READY_FOR_MODERATION)

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            cb = _callback(
                telegram_user_id=990001,
                data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_REJECT}:{offer_id}",
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(cb, state)
            reason_msg = _private_message(telegram_user_id=990001)
            reason_msg.text = "Need clearer schedule"
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_reject_reason(reason_msg, state)
            row = admin_moderation.SupplierOfferModerationService()._offers.get_any(self.session, offer_id=offer_id)
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row.lifecycle_status, SupplierOfferLifecycle.REJECTED)
            self.assertEqual(row.moderation_rejection_reason, "Need clearer schedule")
            return "\n".join(c.args[0].lower() for c in reason_msg.answer.call_args_list if c.args)

        text = asyncio.run(body())
        self.assertIn("rejected", text)

    def test_admin_can_publish_only_from_valid_state(self) -> None:
        invalid_offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.READY_FOR_MODERATION)
        valid_offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.APPROVED)
        mock_cfg = SimpleNamespace(
            telegram_bot_token="dummy-token",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
        )

        async def body(offer_id: int) -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            cb = _callback(
                telegram_user_id=990001,
                data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_PUBLISH}:{offer_id}",
                message=message,
            )
            with (
                patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)),
                patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
                patch("app.services.supplier_offer_moderation_service.send_showcase_publication", return_value=501),
            ):
                await admin_moderation.admin_offer_action(cb, state)
            return "\n".join(c.args[0].lower() for c in message.answer.call_args_list if c.args)

        invalid_text = asyncio.run(body(invalid_offer_id))
        valid_text = asyncio.run(body(valid_offer_id))
        invalid_row = admin_moderation.SupplierOfferModerationService()._offers.get_any(self.session, offer_id=invalid_offer_id)
        valid_row = admin_moderation.SupplierOfferModerationService()._offers.get_any(self.session, offer_id=valid_offer_id)
        self.assertIsNotNone(invalid_row)
        self.assertIsNotNone(valid_row)
        assert invalid_row is not None
        assert valid_row is not None
        self.assertEqual(invalid_row.lifecycle_status, SupplierOfferLifecycle.READY_FOR_MODERATION)
        self.assertEqual(valid_row.lifecycle_status, SupplierOfferLifecycle.PUBLISHED)
        self.assertIn("unavailable", invalid_text)
        self.assertIn("published", valid_text)

    def test_admin_can_retract_only_from_valid_state(self) -> None:
        invalid_offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.APPROVED)
        valid_offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        mock_cfg = SimpleNamespace(
            telegram_bot_token="dummy-token",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
        )

        async def body(offer_id: int) -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            cb = _callback(
                telegram_user_id=990001,
                data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_RETRACT}:{offer_id}",
                message=message,
            )
            with (
                patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)),
                patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
                patch("app.services.supplier_offer_moderation_service.delete_channel_message", return_value=True),
            ):
                await admin_moderation.admin_offer_action(cb, state)
            return "\n".join(c.args[0].lower() for c in message.answer.call_args_list if c.args)

        invalid_text = asyncio.run(body(invalid_offer_id))
        valid_text = asyncio.run(body(valid_offer_id))
        invalid_row = admin_moderation.SupplierOfferModerationService()._offers.get_any(self.session, offer_id=invalid_offer_id)
        valid_row = admin_moderation.SupplierOfferModerationService()._offers.get_any(self.session, offer_id=valid_offer_id)
        self.assertIsNotNone(invalid_row)
        self.assertIsNotNone(valid_row)
        assert invalid_row is not None
        assert valid_row is not None
        self.assertEqual(invalid_row.lifecycle_status, SupplierOfferLifecycle.APPROVED)
        self.assertEqual(valid_row.lifecycle_status, SupplierOfferLifecycle.APPROVED)
        self.assertIn("unavailable", invalid_text)
        self.assertIn("retracted", valid_text)

    def test_moderation_queue_approve_reject_remain_unchanged(self) -> None:
        offer_approve_id = self._create_offer(lifecycle=SupplierOfferLifecycle.READY_FOR_MODERATION)
        offer_reject_id = self._create_offer(lifecycle=SupplierOfferLifecycle.READY_FOR_MODERATION)

        async def body() -> None:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            approve_cb = _callback(
                telegram_user_id=990001,
                data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_APPROVE}:{offer_approve_id}",
                message=message,
            )
            reject_cb = _callback(
                telegram_user_id=990001,
                data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_REJECT}:{offer_reject_id}",
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(approve_cb, state)
                await admin_moderation.admin_offer_action(reject_cb, state)
            reason_message = _private_message(telegram_user_id=990001)
            reason_message.text = "Needs clearer route"
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_reject_reason(reason_message, state)

        self._run(body())
        row_approve = admin_moderation.SupplierOfferModerationService()._offers.get_any(self.session, offer_id=offer_approve_id)
        row_reject = admin_moderation.SupplierOfferModerationService()._offers.get_any(self.session, offer_id=offer_reject_id)
        self.assertIsNotNone(row_approve)
        self.assertIsNotNone(row_reject)
        assert row_approve is not None
        assert row_reject is not None
        self.assertEqual(row_approve.lifecycle_status, SupplierOfferLifecycle.APPROVED)
        self.assertEqual(row_reject.lifecycle_status, SupplierOfferLifecycle.REJECTED)
        self.assertEqual(row_reject.moderation_rejection_reason, "Needs clearer route")

    def test_approve_publish_remain_separate(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.READY_FOR_MODERATION)

        async def body() -> None:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            approve_cb = _callback(
                telegram_user_id=990001,
                data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_APPROVE}:{offer_id}",
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(approve_cb, state)

        self._run(body())
        row = admin_moderation.SupplierOfferModerationService()._offers.get_any(self.session, offer_id=offer_id)
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.lifecycle_status, SupplierOfferLifecycle.APPROVED)
        self.assertIsNone(row.published_at)

    def test_no_admin_content_editing_path_exists(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.READY_FOR_MODERATION)
        row = admin_moderation.SupplierOfferModerationService()._offers.get_any(self.session, offer_id=offer_id)
        self.assertIsNotNone(row)
        assert row is not None
        offer = admin_moderation.SupplierOfferModerationService()._to_read(row)
        actions = [payload for _, payload in admin_moderation._action_button_rows("en", offer)]
        self.assertIn(f"admin:offers:action:approve:{offer_id}", actions)
        self.assertIn(f"admin:offers:action:reject:{offer_id}", actions)
        self.assertNotIn(f"admin:offers:action:edit:{offer_id}", actions)

    def test_unknown_action_gives_explicit_feedback(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.READY_FOR_MODERATION)

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            cb = _callback(
                telegram_user_id=990001,
                data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}unknown:{offer_id}",
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(cb, state)
            return "\n".join(c.args[0].lower() for c in message.answer.call_args_list if c.args)

        text = asyncio.run(body())
        self.assertIn("action is unavailable", text)
        self.assertIn("unknown action", text)


if __name__ == "__main__":
    unittest.main()
