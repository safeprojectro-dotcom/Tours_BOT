"""Y28.1: Telegram admin moderation workspace (allowlist + queue/actions)."""

from __future__ import annotations

import asyncio
import unittest
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.bot.constants import (
    ADMIN_OPS_REQUEST_MARK_UNDER_REVIEW_PREFIX,
    ADMIN_OPS_REQUEST_OP_INTENT_MANUAL_PREFIX,
    ADMIN_OPS_REQUEST_OP_INTENT_SUPPLIER_PREFIX,
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
from app.models.custom_marketplace_request import CustomMarketplaceRequest
from app.models.enums import (
    BookingStatus,
    CustomMarketplaceRequestSource,
    CustomMarketplaceRequestStatus,
    CustomMarketplaceRequestType,
    OperatorWorkflowIntent,
    PaymentStatus,
    SupplierOfferLifecycle,
    SupplierOfferPaymentMode,
    TourSalesMode,
    TourStatus,
)
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


def _action_data(action: str, offer_id: int, *parts: object) -> str:
    suffix = ":".join([action, str(offer_id), *(str(part) for part in parts)])
    return f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{suffix}"


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

    @staticmethod
    def _inline_callback_data(message: MagicMock) -> list[str]:
        callbacks: list[str] = []
        for call in message.answer.call_args_list:
            markup = call.kwargs.get("reply_markup")
            if markup is None:
                continue
            inline_rows = getattr(markup, "inline_keyboard", None) or []
            for row in inline_rows:
                for btn in row:
                    callback_data = getattr(btn, "callback_data", None)
                    if isinstance(callback_data, str):
                        callbacks.append(callback_data)
        return callbacks

    @staticmethod
    def _last_reply_button_texts_lower(message: MagicMock) -> list[str]:
        if not message.answer.call_args_list:
            return []
        call = message.answer.call_args_list[-1]
        markup = call.kwargs.get("reply_markup")
        if markup is None:
            return []
        texts: list[str] = []
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

    def test_admin_workspace_includes_read_only_orders_and_requests_buttons(self) -> None:
        self._create_offer(lifecycle=SupplierOfferLifecycle.READY_FOR_MODERATION)

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_offers(message, state)
            return self._all_answer_texts(message), self._inline_button_texts(message)

        text, buttons = asyncio.run(body())
        self.assertIn("admin moderation queue", text)
        self.assertIn("📦 orders", buttons)
        self.assertIn("📨 requests", buttons)

    def test_non_allowlisted_admin_ops_orders_is_denied(self) -> None:
        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990099)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_orders(message, state)
            return message.answer.call_args[0][0].lower()

        text = asyncio.run(body())
        self.assertIn("not available", text)

    def test_admin_ops_orders_pagination_and_detail_are_read_only(self) -> None:
        user = self.create_user(telegram_user_id=353_001)
        tour = self.create_tour(code="TG-ADM-ORDER-UI", title_default="Telegram Admin Orders")
        point = self.create_boarding_point(tour)
        orders = [
            self.create_order(
                user,
                tour,
                point,
                booking_status=BookingStatus.RESERVED,
                payment_status=PaymentStatus.AWAITING_PAYMENT,
            )
            for _ in range(6)
        ]
        target = orders[-1]
        target_id = target.id
        self.session.commit()

        async def body() -> tuple[str, list[str], list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            next_cb = _callback(
                telegram_user_id=990001,
                data="ao:o:1",
                message=message,
            )
            detail_cb = _callback(
                telegram_user_id=990001,
                data=f"ao:od:{target_id}:0",
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_orders(message, state)
                await admin_moderation.admin_ops_read_navigation(next_cb, state)
                await admin_moderation.admin_ops_read_navigation(detail_cb, state)
            return self._all_answer_texts(message), self._inline_button_texts(message), self._inline_callback_data(message)

        text, buttons, callbacks = asyncio.run(body())
        self.assertIn("admin orders", text)
        self.assertIn("page 1", text)
        self.assertIn("page 2", text)
        self.assertIn("view order #", "\n".join(buttons))
        self.assertIn("order #", text)
        self.assertIn("telegram admin orders", text)
        low = text.lower()
        self.assertIn("telegram id: 353001", low)
        self.assertIn("customer: test user", low)
        self.assertIn("back", buttons)
        self.assertIn("ao:o:1", callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))

    def test_admin_ops_requests_pagination_and_detail_are_read_only(self) -> None:
        user = self.create_user(telegram_user_id=353_101)
        rows: list[CustomMarketplaceRequest] = []
        for idx in range(6):
            row = CustomMarketplaceRequest(
                user_id=user.id,
                request_type=CustomMarketplaceRequestType.CUSTOM_ROUTE,
                travel_date_start=date(2026, 10, min(idx + 1, 28)),
                route_notes=f"Telegram admin request route {idx}",
                group_size=idx + 1,
                source_channel=CustomMarketplaceRequestSource.MINI_APP,
                status=CustomMarketplaceRequestStatus.OPEN,
            )
            self.session.add(row)
            self.session.flush()
            rows.append(row)
        target = rows[-1]
        target_id = target.id
        self.session.commit()

        async def body() -> tuple[str, list[str], list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            next_cb = _callback(
                telegram_user_id=990001,
                data="ao:r:1",
                message=message,
            )
            detail_cb = _callback(
                telegram_user_id=990001,
                data=f"ao:rd:{target_id}:0",
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_requests(message, state)
                await admin_moderation.admin_ops_read_navigation(next_cb, state)
                await admin_moderation.admin_ops_read_navigation(detail_cb, state)
            return self._all_answer_texts(message), self._inline_button_texts(message), self._inline_callback_data(message)

        text, buttons, callbacks = asyncio.run(body())
        self.assertIn("admin requests", text)
        self.assertIn("page 1", text)
        self.assertIn("page 2", text)
        self.assertIn("view request #", "\n".join(buttons))
        self.assertIn("request #", text)
        low = text.lower()
        self.assertIn("telegram id: 353101", low)
        self.assertIn("customer: test user", low)
        self.assertIn("telegram admin request route", text)
        self.assertIn("back", buttons)
        self.assertIn("ao:r:1", callbacks)
        self.assertIn("owner", text.lower())
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))

    def test_admin_ops_request_assign_to_me_telegram(self) -> None:
        self.create_user(telegram_user_id=990001)
        cust = self.create_user(telegram_user_id=353_300)
        row = CustomMarketplaceRequest(
            user_id=cust.id,
            request_type=CustomMarketplaceRequestType.CUSTOM_ROUTE,
            travel_date_start=date(2026, 11, 1),
            route_notes="Assign callback test",
            group_size=2,
            source_channel=CustomMarketplaceRequestSource.MINI_APP,
            status=CustomMarketplaceRequestStatus.OPEN,
        )
        self.session.add(row)
        self.session.commit()
        rid = row.id

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            assign_cb = _callback(
                telegram_user_id=990001,
                data=f"ao:am:{rid}:0",
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_ops_request_assign_to_me_handler(assign_cb, state)
            return self._all_answer_texts(message), self._inline_callback_data(message)

        text, callbacks = asyncio.run(body())
        self.assertIn("assigned to you", text.lower())
        self.assertNotIn("ao:am:", " ".join(callbacks))

    def test_admin_ops_list_shows_compact_owner_em_dash_when_unassigned(self) -> None:
        user = self.create_user(telegram_user_id=353_501)
        row = CustomMarketplaceRequest(
            user_id=user.id,
            request_type=CustomMarketplaceRequestType.CUSTOM_ROUTE,
            travel_date_start=date(2026, 10, 5),
            route_notes="Owner dash list",
            group_size=2,
            source_channel=CustomMarketplaceRequestSource.MINI_APP,
            status=CustomMarketplaceRequestStatus.OPEN,
        )
        self.session.add(row)
        self.session.commit()

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_requests(message, state)
            return self._all_answer_texts(message)

        text = asyncio.run(body())
        self.assertIn("owner: \u2014", text)

    def test_admin_ops_detail_unassigned_shows_assign_to_me_and_callbacks_within_limit(self) -> None:
        user = self.create_user(telegram_user_id=353_502)
        row = CustomMarketplaceRequest(
            user_id=user.id,
            request_type=CustomMarketplaceRequestType.CUSTOM_ROUTE,
            travel_date_start=date(2026, 10, 6),
            route_notes="Detail unassigned",
            group_size=2,
            source_channel=CustomMarketplaceRequestSource.MINI_APP,
            status=CustomMarketplaceRequestStatus.OPEN,
        )
        self.session.add(row)
        self.session.commit()
        rid = row.id

        async def body() -> tuple[list[str], list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            detail_cb = _callback(
                telegram_user_id=990001,
                data=f"ao:rd:{rid}:0",
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_requests(message, state)
                await admin_moderation.admin_ops_read_navigation(detail_cb, state)
            return self._last_reply_button_texts_lower(message), self._inline_callback_data(message)

        buttons, callbacks = asyncio.run(body())
        self.assertIn("assign to me", buttons)
        self.assertTrue(all(len(c.encode("utf-8")) <= 64 for c in callbacks))

    def test_admin_ops_assigned_to_me_hides_assign_shows_list_you(self) -> None:
        viewer = self.create_user(telegram_user_id=990001, first_name="V", last_name="iewer")
        cust = self.create_user(telegram_user_id=353_503)
        row = CustomMarketplaceRequest(
            user_id=cust.id,
            request_type=CustomMarketplaceRequestType.CUSTOM_ROUTE,
            travel_date_start=date(2026, 10, 7),
            route_notes="Y36 me",
            group_size=1,
            source_channel=CustomMarketplaceRequestSource.MINI_APP,
            status=CustomMarketplaceRequestStatus.OPEN,
            assigned_operator_id=viewer.id,
        )
        self.session.add(row)
        self.session.commit()
        rid = row.id

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            detail_cb = _callback(telegram_user_id=990001, data=f"ao:rd:{rid}:0", message=message)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_requests(message, state)
                await admin_moderation.admin_ops_read_navigation(detail_cb, state)
            t = self._all_answer_texts(message)
            b = self._last_reply_button_texts_lower(message)
            return t, b

        text, detail_buttons = asyncio.run(body())
        self.assertIn("owner: you", text)
        self.assertIn("assigned to you", text)
        self.assertNotIn("assign to me", detail_buttons)
        self.assertIn("mark under review", detail_buttons)

    def test_admin_ops_assigned_to_me_open_mark_under_review_callback_refreshes_detail(self) -> None:
        viewer = self.create_user(telegram_user_id=990_001, first_name="V", last_name="iewer")
        cust = self.create_user(telegram_user_id=353_510)
        row = CustomMarketplaceRequest(
            user_id=cust.id,
            request_type=CustomMarketplaceRequestType.CUSTOM_ROUTE,
            travel_date_start=date(2026, 10, 20),
            route_notes="Y37 mark UR",
            group_size=1,
            source_channel=CustomMarketplaceRequestSource.MINI_APP,
            status=CustomMarketplaceRequestStatus.OPEN,
            assigned_operator_id=viewer.id,
        )
        self.session.add(row)
        self.session.commit()
        rid = row.id

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990_001)
            mark_cb = _callback(
                telegram_user_id=990_001,
                data=f"{ADMIN_OPS_REQUEST_MARK_UNDER_REVIEW_PREFIX}{rid}:0",
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_ops_request_mark_under_review_handler(mark_cb, state)
            t = self._all_answer_texts(message)
            c = self._inline_callback_data(message)
            return t, c

        text, callbacks = asyncio.run(body())
        self.assertIn("status: under_review", text.lower())
        self.assertNotIn(f"{ADMIN_OPS_REQUEST_MARK_UNDER_REVIEW_PREFIX}", " ".join(callbacks))

    def test_admin_ops_assigned_to_me_under_review_hides_mark_button(self) -> None:
        viewer = self.create_user(telegram_user_id=990_001, first_name="V2", last_name="iewer")
        cust = self.create_user(telegram_user_id=353_511)
        row = CustomMarketplaceRequest(
            user_id=cust.id,
            request_type=CustomMarketplaceRequestType.CUSTOM_ROUTE,
            travel_date_start=date(2026, 10, 21),
            route_notes="Y37 no dup",
            group_size=1,
            source_channel=CustomMarketplaceRequestSource.MINI_APP,
            status=CustomMarketplaceRequestStatus.UNDER_REVIEW,
            assigned_operator_id=viewer.id,
        )
        self.session.add(row)
        self.session.commit()
        rid = row.id

        async def body() -> list[str]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990_001)
            detail_cb = _callback(telegram_user_id=990_001, data=f"ao:rd:{rid}:0", message=message)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_requests(message, state)
                await admin_moderation.admin_ops_read_navigation(detail_cb, state)
            return self._last_reply_button_texts_lower(message)

        detail_buttons = asyncio.run(body())
        self.assertNotIn("mark under review", detail_buttons)
        self.assertIn("need manual follow-up", detail_buttons)
        self.assertIn("need supplier offer", detail_buttons)

    def test_admin_ops_under_review_with_intent_hides_need_manual_button(self) -> None:
        viewer = self.create_user(telegram_user_id=990_001, first_name="V3", last_name="iewer")
        cust = self.create_user(telegram_user_id=353_512)
        row = CustomMarketplaceRequest(
            user_id=cust.id,
            request_type=CustomMarketplaceRequestType.CUSTOM_ROUTE,
            travel_date_start=date(2026, 10, 22),
            route_notes="Y37.4 intent set",
            group_size=1,
            source_channel=CustomMarketplaceRequestSource.MINI_APP,
            status=CustomMarketplaceRequestStatus.UNDER_REVIEW,
            assigned_operator_id=viewer.id,
            operator_workflow_intent=OperatorWorkflowIntent.NEED_MANUAL_FOLLOWUP,
        )
        self.session.add(row)
        self.session.commit()
        rid = row.id

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990_001)
            detail_cb = _callback(telegram_user_id=990_001, data=f"ao:rd:{rid}:0", message=message)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_requests(message, state)
                await admin_moderation.admin_ops_read_navigation(detail_cb, state)
            t = self._all_answer_texts(message)
            b = self._last_reply_button_texts_lower(message)
            return t, b

        text, detail_buttons = asyncio.run(body())
        self.assertIn("next step: need manual follow-up", text.lower())
        self.assertNotIn("need manual follow-up", detail_buttons)
        self.assertNotIn("need supplier offer", detail_buttons)

    def test_admin_ops_under_review_with_supplier_intent_hides_both_intent_buttons(self) -> None:
        viewer = self.create_user(telegram_user_id=990_001, first_name="V5", last_name="iewer")
        cust = self.create_user(telegram_user_id=353_515)
        row = CustomMarketplaceRequest(
            user_id=cust.id,
            request_type=CustomMarketplaceRequestType.CUSTOM_ROUTE,
            travel_date_start=date(2026, 10, 24),
            route_notes="Y37.5 sup intent",
            group_size=1,
            source_channel=CustomMarketplaceRequestSource.MINI_APP,
            status=CustomMarketplaceRequestStatus.UNDER_REVIEW,
            assigned_operator_id=viewer.id,
            operator_workflow_intent=OperatorWorkflowIntent.NEED_SUPPLIER_OFFER,
        )
        self.session.add(row)
        self.session.commit()
        rid = row.id

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990_001)
            detail_cb = _callback(telegram_user_id=990_001, data=f"ao:rd:{rid}:0", message=message)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_requests(message, state)
                await admin_moderation.admin_ops_read_navigation(detail_cb, state)
            t = self._all_answer_texts(message)
            b = self._last_reply_button_texts_lower(message)
            return t, b

        text, detail_buttons = asyncio.run(body())
        self.assertIn("next step: need supplier offer", text.lower())
        self.assertNotIn("need manual follow-up", detail_buttons)
        self.assertNotIn("need supplier offer", detail_buttons)

    def test_admin_ops_operator_decision_callback_refreshes_detail(self) -> None:
        viewer = self.create_user(telegram_user_id=990_001, first_name="V4", last_name="iewer")
        cust = self.create_user(telegram_user_id=353_513)
        row = CustomMarketplaceRequest(
            user_id=cust.id,
            request_type=CustomMarketplaceRequestType.CUSTOM_ROUTE,
            travel_date_start=date(2026, 10, 23),
            route_notes="Y37.4 od callback",
            group_size=1,
            source_channel=CustomMarketplaceRequestSource.MINI_APP,
            status=CustomMarketplaceRequestStatus.UNDER_REVIEW,
            assigned_operator_id=viewer.id,
        )
        self.session.add(row)
        self.session.commit()
        rid = row.id
        short_m = f"{ADMIN_OPS_REQUEST_OP_INTENT_MANUAL_PREFIX}{rid}:0"
        short_s = f"{ADMIN_OPS_REQUEST_OP_INTENT_SUPPLIER_PREFIX}{rid}:0"
        self.assertTrue(len(short_m.encode("utf-8")) <= 64, short_m)
        self.assertTrue(len(short_s.encode("utf-8")) <= 64, short_s)

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990_001)
            od_cb = _callback(telegram_user_id=990_001, data=short_m, message=message)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_ops_request_operator_decision_handler(od_cb, state)
            t = self._all_answer_texts(message)
            c = self._inline_callback_data(message)
            return t, c

        text, callbacks = asyncio.run(body())
        self.assertIn("next step: need manual follow-up", text.lower())
        self.assertNotIn(ADMIN_OPS_REQUEST_OP_INTENT_MANUAL_PREFIX, " ".join(callbacks))
        self.assertNotIn(ADMIN_OPS_REQUEST_OP_INTENT_SUPPLIER_PREFIX, " ".join(callbacks))

    def test_admin_ops_assigned_to_other_hides_assign_shows_operator_in_list(self) -> None:
        self.create_user(telegram_user_id=990001)
        other = self.create_user(telegram_user_id=990002, first_name="Alice", last_name="Otherop")
        cust = self.create_user(telegram_user_id=353_504)
        row = CustomMarketplaceRequest(
            user_id=cust.id,
            request_type=CustomMarketplaceRequestType.CUSTOM_ROUTE,
            travel_date_start=date(2026, 10, 8),
            route_notes="Y36 other",
            group_size=1,
            source_channel=CustomMarketplaceRequestSource.MINI_APP,
            status=CustomMarketplaceRequestStatus.OPEN,
            assigned_operator_id=other.id,
        )
        self.session.add(row)
        self.session.commit()
        rid = row.id

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            detail_cb = _callback(telegram_user_id=990001, data=f"ao:rd:{rid}:0", message=message)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.cmd_admin_requests(message, state)
                await admin_moderation.admin_ops_read_navigation(detail_cb, state)
            t = self._all_answer_texts(message)
            b = self._last_reply_button_texts_lower(message)
            return t, b

        text, detail_buttons = asyncio.run(body())
        self.assertIn("owner: alice", text)
        self.assertNotIn("assign to me", detail_buttons)
        self.assertNotIn("assigned to you", text)
        self.assertIn("owner: customer", text)

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
        tour_id = tour.id
        self.session.commit()

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            start_cb = _callback(
                telegram_user_id=990001,
                data=_action_data(ADMIN_OFFERS_ACTION_CREATE_LINK, offer_id),
                message=message,
            )
            manual_cb = _callback(
                telegram_user_id=990001,
                data=f"el:manual:{offer_id}:create",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = str(tour_id)
            confirm_cb = _callback(
                telegram_user_id=990001,
                data=_action_data(ADMIN_OFFERS_ACTION_CONFIRM_CREATE_LINK, offer_id),
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(start_cb, state)
                await admin_moderation.admin_offer_action(manual_cb, state)
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
        self.assertEqual(active[0].tour_id, tour_id)

    def test_admin_link_candidate_list_filters_same_sales_mode(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        compatible = self.create_tour(code="TG-CANDIDATE-OK", title_default="Compatible", sales_mode=TourSalesMode.PER_SEAT)
        mismatch = self.create_tour(code="TG-CANDIDATE-BAD", title_default="Mismatch", sales_mode=TourSalesMode.FULL_BUS)
        self.session.commit()
        self.assertGreater(compatible.id, 0)
        self.assertGreater(mismatch.id, 0)

        async def body() -> tuple[str, list[str], list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            start_cb = _callback(
                telegram_user_id=990001,
                data=_action_data(ADMIN_OFFERS_ACTION_CREATE_LINK, offer_id),
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(start_cb, state)
            return self._all_answer_texts(message), self._inline_button_texts(message), self._inline_callback_data(message)

        text, buttons, callbacks = asyncio.run(body())
        self.assertIn("compatible execution tours", text)
        self.assertIn("tg-candidate-ok", text)
        self.assertIn("compatible", text)
        self.assertIn("open_for_sale", text)
        self.assertIn("per_seat", text)
        self.assertIn("seats:", text)
        self.assertNotIn("tg-candidate-bad", text)
        self.assertIn(f"select tour #{compatible.id} (tg-candidate-ok)", buttons)
        self.assertIn("search compatible tours", buttons)
        self.assertIn("manual tour_id/code input", buttons)
        self.assertIn(f"el:pick:{offer_id}:create:{compatible.id}", callbacks)
        self.assertIn(f"el:search:{offer_id}:create", callbacks)
        self.assertIn(f"el:manual:{offer_id}:create", callbacks)
        self.assertTrue(callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))

    def test_admin_link_candidate_list_empty_keeps_no_state_change(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        self.session.query(admin_moderation.Tour).filter(
            admin_moderation.Tour.sales_mode == TourSalesMode.PER_SEAT
        ).update({admin_moderation.Tour.status: TourStatus.CANCELLED})
        self.create_tour(code="TG-NO-CANDIDATE", sales_mode=TourSalesMode.FULL_BUS)
        self.session.commit()

        async def body() -> tuple[str, list[str], list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            start_cb = _callback(
                telegram_user_id=990001,
                data=_action_data(ADMIN_OFFERS_ACTION_CREATE_LINK, offer_id),
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(start_cb, state)
            return self._all_answer_texts(message), self._inline_button_texts(message), self._inline_callback_data(message)

        text, buttons, callbacks = asyncio.run(body())
        self.assertIn("no compatible existing tours", text)
        self.assertIn("no link was changed", text)
        self.assertIn("search compatible tours", buttons)
        self.assertIn("manual tour_id/code input", buttons)
        self.assertIn(f"el:search:{offer_id}:create", callbacks)
        self.assertIn(f"el:manual:{offer_id}:create", callbacks)
        self.assertTrue(callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))
        links = self.session.query(SupplierOfferExecutionLink).filter_by(supplier_offer_id=offer_id).all()
        self.assertEqual(links, [])

    def test_admin_link_code_search_button_enters_search_state(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        self.create_tour(code="TG-SEARCH-ENTRY", sales_mode=TourSalesMode.PER_SEAT)
        self.session.commit()

        async def body() -> tuple[str, object, dict]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            start_cb = _callback(
                telegram_user_id=990001,
                data=_action_data(ADMIN_OFFERS_ACTION_CREATE_LINK, offer_id),
                message=message,
            )
            search_cb = _callback(
                telegram_user_id=990001,
                data=f"el:search:{offer_id}:create",
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(start_cb, state)
                await admin_moderation.admin_offer_action(search_cb, state)
            return self._all_answer_texts(message), state.last_state, state.data

        text, last_state, data = asyncio.run(body())
        self.assertIn("send tour code or title", text)
        self.assertIn("you can also add date", text)
        self.assertIn("yyyy-mm-dd", text)
        self.assertIn(f"compatible tours for offer #{offer_id}", text)
        self.assertEqual(last_state, admin_moderation.AdminModerationState.awaiting_execution_link_tour_code_search)
        self.assertEqual(data["pending_link_offer_id"], offer_id)
        self.assertEqual(data["pending_link_mode"], "create")

    def test_admin_link_code_search_exact_match_filters_same_sales_mode(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        compatible = self.create_tour(code="TG-CODE-EXACT", sales_mode=TourSalesMode.PER_SEAT)
        mismatch = self.create_tour(code="TG-CODE-EXACT-BUS", sales_mode=TourSalesMode.FULL_BUS)
        compatible_id = compatible.id
        mismatch_id = mismatch.id
        self.session.commit()

        async def body() -> tuple[str, list[str], list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            start_cb = _callback(
                telegram_user_id=990001,
                data=_action_data(ADMIN_OFFERS_ACTION_CREATE_LINK, offer_id),
                message=message,
            )
            search_cb = _callback(
                telegram_user_id=990001,
                data=f"el:search:{offer_id}:create",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = "TG-CODE-EXACT"
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(start_cb, state)
                await admin_moderation.admin_offer_action(search_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_code_search_input(input_message, state)
            return (
                "\n".join([self._all_answer_texts(message), self._all_answer_texts(input_message)]),
                self._inline_button_texts(input_message),
                self._inline_callback_data(input_message),
            )

        text, buttons, callbacks = asyncio.run(body())
        self.assertIn(f"search results for offer #{offer_id}", text)
        self.assertIn("mode: create", text)
        self.assertIn("query: tg-code-exact", text)
        self.assertIn("date: -", text)
        self.assertIn("tg-code-exact", text)
        self.assertNotIn("tg-code-exact-bus", text)
        self.assertIn(f"select tour #{compatible_id} (tg-code-exact)", buttons)
        self.assertIn("new search", buttons)
        self.assertIn("back to compatible list", buttons)
        self.assertIn("manual tour_id/code input", buttons)
        self.assertIn(f"el:pick:{offer_id}:create:{compatible_id}", callbacks)
        self.assertIn(f"el:search:{offer_id}:create", callbacks)
        self.assertIn(f"el:list:{offer_id}:create:0", callbacks)
        self.assertIn(f"el:manual:{offer_id}:create", callbacks)
        self.assertNotIn(f"el:pick:{offer_id}:create:{mismatch_id}", callbacks)
        self.assertTrue(callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))

    def test_admin_link_code_search_partial_match_returns_compatible_tour(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        target = self.create_tour(code="TG-PARTIAL-CODE-777", sales_mode=TourSalesMode.PER_SEAT)
        other = self.create_tour(code="TG-OTHER-CODE-888", sales_mode=TourSalesMode.PER_SEAT)
        target_id = target.id
        other_id = other.id
        self.session.commit()

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            start_cb = _callback(
                telegram_user_id=990001,
                data=_action_data(ADMIN_OFFERS_ACTION_CREATE_LINK, offer_id),
                message=message,
            )
            search_cb = _callback(
                telegram_user_id=990001,
                data=f"el:search:{offer_id}:create",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = "partial-code"
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(start_cb, state)
                await admin_moderation.admin_offer_action(search_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_code_search_input(input_message, state)
            return self._all_answer_texts(input_message), self._inline_callback_data(input_message)

        text, callbacks = asyncio.run(body())
        self.assertIn("tg-partial-code-777", text)
        self.assertNotIn("tg-other-code-888", text)
        self.assertIn(f"el:pick:{offer_id}:create:{target_id}", callbacks)
        self.assertNotIn(f"el:pick:{offer_id}:create:{other_id}", callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))

    def test_admin_link_title_search_returns_compatible_tour(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        target = self.create_tour(
            code="TG-TITLE-SEARCH-OK",
            title_default="Weekend Danube Escape",
            sales_mode=TourSalesMode.PER_SEAT,
        )
        other = self.create_tour(
            code="TG-TITLE-SEARCH-OTHER",
            title_default="Mountain Morning",
            sales_mode=TourSalesMode.PER_SEAT,
        )
        target_id = target.id
        other_id = other.id
        self.session.commit()

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            search_cb = _callback(
                telegram_user_id=990001,
                data=f"el:search:{offer_id}:create",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = "danube"
            await state.update_data(pending_link_offer_id=offer_id, pending_link_mode="create")
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(search_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_code_search_input(input_message, state)
            return self._all_answer_texts(input_message), self._inline_callback_data(input_message)

        text, callbacks = asyncio.run(body())
        self.assertIn(f"search results for offer #{offer_id}", text)
        self.assertIn("query: danube", text)
        self.assertIn("date: -", text)
        self.assertIn("weekend danube escape", text)
        self.assertNotIn("mountain morning", text)
        self.assertIn(f"el:pick:{offer_id}:create:{target_id}", callbacks)
        self.assertNotIn(f"el:pick:{offer_id}:create:{other_id}", callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))

    def test_admin_link_title_search_excludes_wrong_sales_mode(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        compatible = self.create_tour(
            code="TG-TITLE-SM-OK",
            title_default="Shared City Weekend",
            sales_mode=TourSalesMode.PER_SEAT,
        )
        mismatch = self.create_tour(
            code="TG-TITLE-SM-BAD",
            title_default="Private City Weekend",
            sales_mode=TourSalesMode.FULL_BUS,
        )
        compatible_id = compatible.id
        mismatch_id = mismatch.id
        self.session.commit()

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            search_cb = _callback(
                telegram_user_id=990001,
                data=f"el:search:{offer_id}:create",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = "city weekend"
            await state.update_data(pending_link_offer_id=offer_id, pending_link_mode="create")
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(search_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_code_search_input(input_message, state)
            return self._all_answer_texts(input_message), self._inline_callback_data(input_message)

        text, callbacks = asyncio.run(body())
        self.assertIn("shared city weekend", text)
        self.assertNotIn("private city weekend", text)
        self.assertIn(f"el:pick:{offer_id}:create:{compatible_id}", callbacks)
        self.assertNotIn(f"el:pick:{offer_id}:create:{mismatch_id}", callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))

    def test_admin_link_search_date_only_returns_compatible_tours_on_date(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        target_departure = datetime.now(UTC).replace(second=0, microsecond=0) + timedelta(days=45)
        other_departure = target_departure + timedelta(days=1)
        target = self.create_tour(
            code="TG-DATE-ONLY-OK",
            title_default="Date Only Match",
            sales_mode=TourSalesMode.PER_SEAT,
            departure_datetime=target_departure,
        )
        other = self.create_tour(
            code="TG-DATE-ONLY-OTHER",
            title_default="Date Only Other",
            sales_mode=TourSalesMode.PER_SEAT,
            departure_datetime=other_departure,
        )
        target_id = target.id
        other_id = other.id
        date_text = target_departure.date().isoformat()
        self.session.commit()

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            search_cb = _callback(
                telegram_user_id=990001,
                data=f"el:search:{offer_id}:create",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = date_text
            await state.update_data(pending_link_offer_id=offer_id, pending_link_mode="create")
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(search_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_code_search_input(input_message, state)
            return self._all_answer_texts(input_message), self._inline_callback_data(input_message)

        text, callbacks = asyncio.run(body())
        self.assertIn(date_text, text)
        self.assertIn("tg-date-only-ok", text)
        self.assertNotIn("tg-date-only-other", text)
        self.assertIn(f"el:pick:{offer_id}:create:{target_id}", callbacks)
        self.assertNotIn(f"el:pick:{offer_id}:create:{other_id}", callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))

    def test_admin_link_search_code_and_date_apply_both_filters(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        target_departure = datetime.now(UTC).replace(second=0, microsecond=0) + timedelta(days=50)
        other_departure = target_departure + timedelta(days=1)
        target = self.create_tour(
            code="TG-SMOKE-DATE",
            sales_mode=TourSalesMode.PER_SEAT,
            departure_datetime=target_departure,
        )
        same_code_wrong_date = self.create_tour(
            code="TG-SMOKE-DATE-OTHER",
            sales_mode=TourSalesMode.PER_SEAT,
            departure_datetime=other_departure,
        )
        wrong_mode = self.create_tour(
            code="TG-SMOKE-DATE-BUS",
            sales_mode=TourSalesMode.FULL_BUS,
            departure_datetime=target_departure,
        )
        target_id = target.id
        wrong_date_id = same_code_wrong_date.id
        wrong_mode_id = wrong_mode.id
        date_text = target_departure.date().isoformat()
        self.session.commit()

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            search_cb = _callback(
                telegram_user_id=990001,
                data=f"el:search:{offer_id}:create",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = f"SMOKE {date_text}"
            await state.update_data(pending_link_offer_id=offer_id, pending_link_mode="create")
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(search_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_code_search_input(input_message, state)
            return self._all_answer_texts(input_message), self._inline_callback_data(input_message)

        text, callbacks = asyncio.run(body())
        self.assertIn("query: smoke", text)
        self.assertIn(f"date: {date_text}", text)
        self.assertIn("tg-smoke-date", text)
        self.assertNotIn("tg-smoke-date-other", text)
        self.assertNotIn("tg-smoke-date-bus", text)
        self.assertIn(f"el:pick:{offer_id}:create:{target_id}", callbacks)
        self.assertNotIn(f"el:pick:{offer_id}:create:{wrong_date_id}", callbacks)
        self.assertNotIn(f"el:pick:{offer_id}:create:{wrong_mode_id}", callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))

    def test_admin_link_search_title_and_date_apply_both_filters(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        target_departure = datetime.now(UTC).replace(second=0, microsecond=0) + timedelta(days=55)
        other_departure = target_departure + timedelta(days=1)
        target = self.create_tour(
            code="TG-TITLE-DATE-OK",
            title_default="Full Bus Riverside",
            sales_mode=TourSalesMode.PER_SEAT,
            departure_datetime=target_departure,
        )
        wrong_date = self.create_tour(
            code="TG-TITLE-DATE-WRONG",
            title_default="Full Bus Riverside",
            sales_mode=TourSalesMode.PER_SEAT,
            departure_datetime=other_departure,
        )
        target_id = target.id
        wrong_date_id = wrong_date.id
        date_text = target_departure.date().isoformat()
        self.session.commit()

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            search_cb = _callback(
                telegram_user_id=990001,
                data=f"el:search:{offer_id}:create",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = f"full bus {date_text}"
            await state.update_data(pending_link_offer_id=offer_id, pending_link_mode="create")
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(search_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_code_search_input(input_message, state)
            return self._all_answer_texts(input_message), self._inline_callback_data(input_message)

        text, callbacks = asyncio.run(body())
        self.assertIn("query: full bus", text)
        self.assertIn(f"date: {date_text}", text)
        self.assertIn("tg-title-date-ok", text)
        self.assertNotIn("tg-title-date-wrong", text)
        self.assertIn(f"el:pick:{offer_id}:create:{target_id}", callbacks)
        self.assertNotIn(f"el:pick:{offer_id}:create:{wrong_date_id}", callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))

    def test_admin_link_search_invalid_date_is_ignored(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        target_departure = datetime.now(UTC).replace(second=0, microsecond=0) + timedelta(days=60)
        target = self.create_tour(
            code="TG-INVALID-DATE",
            title_default="Invalid Date Smoke",
            sales_mode=TourSalesMode.PER_SEAT,
            departure_datetime=target_departure,
        )
        target_id = target.id
        self.session.commit()

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            search_cb = _callback(
                telegram_user_id=990001,
                data=f"el:search:{offer_id}:create",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = "INVALID-DATE 2026-99-99"
            await state.update_data(pending_link_offer_id=offer_id, pending_link_mode="create")
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(search_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_code_search_input(input_message, state)
            return self._all_answer_texts(input_message), self._inline_callback_data(input_message)

        text, callbacks = asyncio.run(body())
        self.assertIn("invalid-date", text)
        self.assertNotIn("2026-99-99", text)
        self.assertIn(f"el:pick:{offer_id}:create:{target_id}", callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))

    def test_admin_link_code_search_no_results_keeps_no_state_change(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        self.create_tour(code="TG-SEARCH-NOMATCH", sales_mode=TourSalesMode.PER_SEAT)
        self.session.commit()

        async def body() -> tuple[str, list[str], list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            search_cb = _callback(
                telegram_user_id=990001,
                data=f"el:search:{offer_id}:create",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = "DOES-NOT-EXIST"
            await state.update_data(pending_link_offer_id=offer_id, pending_link_mode="create")
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(search_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_code_search_input(input_message, state)
            return (
                self._all_answer_texts(input_message),
                self._inline_button_texts(input_message),
                self._inline_callback_data(input_message),
            )

        text, buttons, callbacks = asyncio.run(body())
        self.assertIn("no compatible tours found.", text)
        self.assertIn('search: "does-not-exist"', text)
        self.assertIn("no link was changed", text)
        self.assertIn("try removing the date", text)
        self.assertIn("using a shorter query", text)
        self.assertIn("manual tour_id/code input", text)
        self.assertIn("new search", buttons)
        self.assertIn("back to compatible list", buttons)
        self.assertIn("manual tour_id/code input", buttons)
        self.assertIn("back", buttons)
        self.assertIn(f"el:search:{offer_id}:create", callbacks)
        self.assertIn(f"el:list:{offer_id}:create:0", callbacks)
        self.assertIn(f"el:manual:{offer_id}:create", callbacks)
        self.assertIn("admin:offers:nav:back", callbacks)
        self.assertTrue(callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))
        links = self.session.query(SupplierOfferExecutionLink).filter_by(supplier_offer_id=offer_id).all()
        self.assertEqual(links, [])

    def test_admin_link_search_result_new_search_reenters_prompt(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        self.create_tour(code="TG-NEW-SEARCH", sales_mode=TourSalesMode.PER_SEAT)
        self.session.commit()

        async def body() -> tuple[str, list[str], object, dict]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            search_cb = _callback(
                telegram_user_id=990001,
                data=f"el:search:{offer_id}:create",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = "NEW-SEARCH"
            new_search_cb = _callback(
                telegram_user_id=990001,
                data=f"el:search:{offer_id}:create",
                message=input_message,
            )
            await state.update_data(pending_link_offer_id=offer_id, pending_link_mode="create")
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(search_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_code_search_input(input_message, state)
                result_buttons = self._inline_button_texts(input_message)
                await admin_moderation.admin_offer_action(new_search_cb, state)
            return self._all_answer_texts(input_message), result_buttons, state.last_state, state.data

        text, result_buttons, last_state, data = asyncio.run(body())
        self.assertIn("new search", result_buttons)
        self.assertIn("send tour code or title", text)
        self.assertIn(f"compatible tours for offer #{offer_id}", text)
        self.assertEqual(last_state, admin_moderation.AdminModerationState.awaiting_execution_link_tour_code_search)
        self.assertEqual(data["pending_link_offer_id"], offer_id)
        self.assertEqual(data["pending_link_mode"], "create")

    def test_admin_link_code_search_pagination_preserves_query_in_state(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        base_departure = datetime.now(UTC) + timedelta(days=10)
        tours = [
            self.create_tour(
                code=f"TG-SEARCH-PAGE-{idx}",
                sales_mode=TourSalesMode.PER_SEAT,
                departure_datetime=base_departure + timedelta(days=idx),
            )
            for idx in range(6)
        ]
        target_id = tours[-1].id
        self.session.commit()

        async def body() -> tuple[str, list[str], list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            search_cb = _callback(
                telegram_user_id=990001,
                data=f"el:search:{offer_id}:create",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = "SEARCH-PAGE"
            page_two_cb = _callback(
                telegram_user_id=990001,
                data=f"el:slist:{offer_id}:create:1",
                message=message,
            )
            await state.update_data(pending_link_offer_id=offer_id, pending_link_mode="create")
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(search_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_code_search_input(input_message, state)
                await admin_moderation.admin_offer_action(page_two_cb, state)
            return (
                "\n".join([self._all_answer_texts(message), self._all_answer_texts(input_message)]),
                self._inline_button_texts(message) + self._inline_button_texts(input_message),
                self._inline_callback_data(message) + self._inline_callback_data(input_message),
            )

        text, buttons, callbacks = asyncio.run(body())
        self.assertIn("page: 1", text)
        self.assertIn("page: 2", text)
        self.assertIn("tg-search-page-5", text)
        self.assertIn("next", buttons)
        self.assertIn("prev", buttons)
        self.assertIn(f"el:slist:{offer_id}:create:1", callbacks)
        self.assertIn(f"el:pick:{offer_id}:create:{target_id}", callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))

    def test_admin_selects_code_search_result_and_opens_confirmation(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        tour = self.create_tour(code="TG-SEARCH-CONFIRM", sales_mode=TourSalesMode.PER_SEAT)
        tour_id = tour.id
        self.session.commit()

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            search_cb = _callback(
                telegram_user_id=990001,
                data=f"el:search:{offer_id}:create",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = "SEARCH-CONFIRM"
            select_cb = _callback(
                telegram_user_id=990001,
                data=f"el:pick:{offer_id}:create:{tour_id}",
                message=message,
            )
            await state.update_data(pending_link_offer_id=offer_id, pending_link_mode="create")
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(search_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_code_search_input(input_message, state)
                await admin_moderation.admin_offer_action(select_cb, state)
            return (
                "\n".join([self._all_answer_texts(message), self._all_answer_texts(input_message)]),
                self._inline_callback_data(message) + self._inline_callback_data(input_message),
            )

        text, callbacks = asyncio.run(body())
        self.assertIn(f"search results for offer #{offer_id}", text)
        self.assertIn("confirm execution link target", text)
        self.assertIn("mini app cta appears only", text)
        self.assertIn(f"el:pick:{offer_id}:create:{tour_id}", callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))

    def test_admin_selects_date_search_result_and_opens_confirmation(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        target_departure = datetime.now(UTC).replace(second=0, microsecond=0) + timedelta(days=65)
        tour = self.create_tour(
            code="TG-DATE-CONFIRM",
            title_default="Date Confirmation Trip",
            sales_mode=TourSalesMode.PER_SEAT,
            departure_datetime=target_departure,
        )
        tour_id = tour.id
        date_text = target_departure.date().isoformat()
        self.session.commit()

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            search_cb = _callback(
                telegram_user_id=990001,
                data=f"el:search:{offer_id}:create",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = date_text
            select_cb = _callback(
                telegram_user_id=990001,
                data=f"el:pick:{offer_id}:create:{tour_id}",
                message=message,
            )
            await state.update_data(pending_link_offer_id=offer_id, pending_link_mode="create")
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(search_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_code_search_input(input_message, state)
                await admin_moderation.admin_offer_action(select_cb, state)
            return (
                "\n".join([self._all_answer_texts(message), self._all_answer_texts(input_message)]),
                self._inline_callback_data(message) + self._inline_callback_data(input_message),
            )

        text, callbacks = asyncio.run(body())
        self.assertIn(f"search results for offer #{offer_id}", text)
        self.assertIn("confirm execution link target", text)
        self.assertIn("mini app cta appears only", text)
        self.assertIn(f"el:pick:{offer_id}:create:{tour_id}", callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))

    def test_admin_selects_title_search_result_and_opens_confirmation(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        tour = self.create_tour(
            code="TG-TITLE-CONFIRM",
            title_default="Forest Confirmation Trip",
            sales_mode=TourSalesMode.PER_SEAT,
        )
        tour_id = tour.id
        self.session.commit()

        async def body() -> tuple[str, list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            search_cb = _callback(
                telegram_user_id=990001,
                data=f"el:search:{offer_id}:create",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = "forest confirmation"
            select_cb = _callback(
                telegram_user_id=990001,
                data=f"el:pick:{offer_id}:create:{tour_id}",
                message=message,
            )
            await state.update_data(pending_link_offer_id=offer_id, pending_link_mode="create")
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(search_cb, state)
                await admin_moderation.admin_offer_execution_link_tour_code_search_input(input_message, state)
                await admin_moderation.admin_offer_action(select_cb, state)
            return (
                "\n".join([self._all_answer_texts(message), self._all_answer_texts(input_message)]),
                self._inline_callback_data(message) + self._inline_callback_data(input_message),
            )

        text, callbacks = asyncio.run(body())
        self.assertIn(f"search results for offer #{offer_id}", text)
        self.assertIn("confirm execution link target", text)
        self.assertIn("mini app cta appears only", text)
        self.assertIn(f"el:pick:{offer_id}:create:{tour_id}", callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))

    def test_admin_selects_candidate_and_creates_execution_link(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        tour = self.create_tour(code="TG-LINK-CANDIDATE", sales_mode=TourSalesMode.PER_SEAT)
        tour_id = tour.id
        self.session.commit()

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            start_cb = _callback(
                telegram_user_id=990001,
                data=_action_data(ADMIN_OFFERS_ACTION_CREATE_LINK, offer_id),
                message=message,
            )
            select_cb = _callback(
                telegram_user_id=990001,
                data=f"el:pick:{offer_id}:create:{tour_id}",
                message=message,
            )
            confirm_cb = _callback(
                telegram_user_id=990001,
                data=_action_data(ADMIN_OFFERS_ACTION_CONFIRM_CREATE_LINK, offer_id),
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(start_cb, state)
                await admin_moderation.admin_offer_action(select_cb, state)
                await admin_moderation.admin_offer_action(confirm_cb, state)
            return self._all_answer_texts(message)

        text = asyncio.run(body())
        self.assertIn("compatible execution tours", text)
        self.assertIn("confirm execution link target", text)
        self.assertIn("execution link created", text)
        active = [
            link
            for link in self.session.query(SupplierOfferExecutionLink).filter_by(supplier_offer_id=offer_id).all()
            if link.link_status == "active"
        ]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].tour_id, tour_id)

    def test_admin_link_candidate_pagination_preserves_mode_and_selects_page_two(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        base_departure = datetime.now(UTC) + timedelta(days=10)
        tours = [
            self.create_tour(
                code=f"TG-PAGE-{idx}",
                sales_mode=TourSalesMode.PER_SEAT,
                departure_datetime=base_departure + timedelta(days=idx),
            )
            for idx in range(6)
        ]
        target_id = tours[-1].id
        self.session.commit()

        async def body() -> tuple[str, list[str], list[str]]:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            page_one_cb = _callback(
                telegram_user_id=990001,
                data=_action_data(ADMIN_OFFERS_ACTION_CREATE_LINK, offer_id),
                message=message,
            )
            page_two_cb = _callback(
                telegram_user_id=990001,
                data=f"el:list:{offer_id}:create:1",
                message=message,
            )
            select_cb = _callback(
                telegram_user_id=990001,
                data=f"el:pick:{offer_id}:create:{target_id}",
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(page_one_cb, state)
                await admin_moderation.admin_offer_action(page_two_cb, state)
                await admin_moderation.admin_offer_action(select_cb, state)
            return self._all_answer_texts(message), self._inline_button_texts(message), self._inline_callback_data(message)

        text, buttons, callbacks = asyncio.run(body())
        self.assertIn("page 1", text)
        self.assertIn("page 2", text)
        self.assertIn("tg-page-5", text)
        self.assertIn("confirm execution link target", text)
        self.assertIn("next", buttons)
        self.assertIn("prev", buttons)
        self.assertIn(f"el:list:{offer_id}:create:1", callbacks)
        self.assertIn(f"el:pick:{offer_id}:create:{target_id}", callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))

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
                data=_action_data(ADMIN_OFFERS_ACTION_REPLACE_LINK, offer_id),
                message=message,
            )
            manual_cb = _callback(
                telegram_user_id=990001,
                data=f"el:manual:{offer_id}:replace",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = new_tour_code
            confirm_cb = _callback(
                telegram_user_id=990001,
                data=_action_data(ADMIN_OFFERS_ACTION_CONFIRM_REPLACE_LINK, offer_id),
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(start_cb, state)
                await admin_moderation.admin_offer_action(manual_cb, state)
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

    def test_admin_selects_candidate_and_replaces_execution_link(self) -> None:
        offer_id = self._create_offer(lifecycle=SupplierOfferLifecycle.PUBLISHED)
        old_tour = self.create_tour(code="TG-CAND-OLD", sales_mode=TourSalesMode.PER_SEAT)
        new_tour = self.create_tour(code="TG-CAND-NEW", sales_mode=TourSalesMode.PER_SEAT)
        old_tour_id = old_tour.id
        new_tour_id = new_tour.id
        self.session.add(SupplierOfferExecutionLink(supplier_offer_id=offer_id, tour_id=old_tour_id, link_status="active"))
        self.session.commit()

        async def body() -> str:
            state = _DictFSMState()
            message = _private_message(telegram_user_id=990001)
            start_cb = _callback(
                telegram_user_id=990001,
                data=_action_data(ADMIN_OFFERS_ACTION_REPLACE_LINK, offer_id),
                message=message,
            )
            select_cb = _callback(
                telegram_user_id=990001,
                data=f"el:pick:{offer_id}:replace:{new_tour_id}",
                message=message,
            )
            confirm_cb = _callback(
                telegram_user_id=990001,
                data=_action_data(ADMIN_OFFERS_ACTION_CONFIRM_REPLACE_LINK, offer_id),
                message=message,
            )
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(start_cb, state)
                await admin_moderation.admin_offer_action(select_cb, state)
                await admin_moderation.admin_offer_action(confirm_cb, state)
            return self._all_answer_texts(message), self._inline_callback_data(message)

        text, callbacks = asyncio.run(body())
        self.assertIn("compatible execution tours", text)
        self.assertIn("confirm execution link target", text)
        self.assertIn("execution link replaced", text)
        self.assertIn(f"el:pick:{offer_id}:replace:{new_tour_id}", callbacks)
        self.assertIn(f"el:manual:{offer_id}:replace", callbacks)
        self.assertTrue(all(len(callback.encode("utf-8")) <= 64 for callback in callbacks))
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
                data=_action_data(ADMIN_OFFERS_ACTION_CREATE_LINK, offer_id),
                message=message,
            )
            manual_cb = _callback(
                telegram_user_id=990001,
                data=f"el:manual:{offer_id}:create",
                message=message,
            )
            input_message = _private_message(telegram_user_id=990001)
            input_message.text = str(mismatched_tour.id)
            with patch.object(admin_moderation, "SessionLocal", _SessionLocalBinder(self.session)):
                await admin_moderation.admin_offer_action(start_cb, state)
                await admin_moderation.admin_offer_action(manual_cb, state)
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
