"""Phase 7 / Step 8 — focused runtime boundary tests for ``grp_*`` private ``/start`` + ``grp_followup`` handoff chain."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import func, select

from app.bot.handlers import private_entry
from app.models.enums import TourStatus
from app.models.handoff import Handoff
from app.services.handoff_entry import HandoffEntryService
from tests.unit.base import FoundationDBTestCase


class _SessionLocalBinder:
    """Makes ``with SessionLocal() as session`` use the test ``Session`` (same DB transaction)."""

    def __init__(self, session) -> None:
        self._session = session

    def __call__(self):
        return self._session


def _private_message(*, telegram_user_id: int) -> MagicMock:
    message = MagicMock()
    message.from_user = MagicMock()
    message.from_user.id = telegram_user_id
    message.from_user.username = "chain_user"
    message.from_user.first_name = "T"
    message.from_user.last_name = "U"
    message.from_user.language_code = "en"
    message.chat = MagicMock()
    message.chat.type = "private"
    message.chat.id = 990_001
    message.answer = AsyncMock(return_value=MagicMock(message_id=1))
    message.bot = MagicMock()
    return message


class PrivateEntryGrpFollowupChainTests(FoundationDBTestCase):
    """Exercise ``handle_start`` for ``grp_*`` / legacy payloads with patched ``SessionLocal``."""

    @staticmethod
    def _run(coro) -> None:
        asyncio.run(coro)

    def test_grp_followup_reaches_handler_persists_handoff_and_followup_intro(self) -> None:
        user_id = self.create_user(telegram_user_id=88_201, preferred_language="en").id
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=88_201)
            state = MagicMock()
            state.clear = AsyncMock()
            command = MagicMock()
            command.args = "grp_followup"
            binder = _SessionLocalBinder(self.session)
            with patch.object(private_entry, "SessionLocal", binder):
                with patch.object(private_entry, "_send_catalog_overview", new_callable=AsyncMock):
                    await private_entry.handle_start(message, state, command)

            message.answer.assert_called()
            intro_text = message.answer.call_args[0][0]
            self.assertIn("/contact", intro_text)
            self.assertIn("Thanks for continuing", intro_text)

        self._run(body())

        n_open = self.session.scalar(
            select(func.count())
            .select_from(Handoff)
            .where(
                Handoff.user_id == user_id,
                Handoff.reason == HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
                Handoff.status == "open",
            )
        )
        self.assertEqual(n_open, 1)

    def test_grp_followup_second_start_dedupes_open_handoff(self) -> None:
        user_id = self.create_user(telegram_user_id=88_202, preferred_language="en").id
        self.session.commit()
        second_intro: list[str] = []

        async def body() -> None:
            binder = _SessionLocalBinder(self.session)
            for i in range(2):
                message = _private_message(telegram_user_id=88_202)
                state = MagicMock()
                state.clear = AsyncMock()
                command = MagicMock()
                command.args = "grp_followup"
                with patch.object(private_entry, "SessionLocal", binder):
                    with patch.object(private_entry, "_send_catalog_overview", new_callable=AsyncMock):
                        await private_entry.handle_start(message, state, command)
                if i == 1:
                    second_intro.append(message.answer.call_args[0][0])

        self._run(body())

        rows = self.session.scalars(
            select(Handoff).where(
                Handoff.user_id == user_id,
                Handoff.reason == HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
                Handoff.status == "open",
            )
        ).all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(second_intro), 1)
        self.assertIn("already open", second_intro[0].lower())

    def test_grp_private_no_group_followup_handoff_row(self) -> None:
        user_id = self.create_user(telegram_user_id=88_203, preferred_language="en").id
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=88_203)
            state = MagicMock()
            state.clear = AsyncMock()
            command = MagicMock()
            command.args = "grp_private"
            binder = _SessionLocalBinder(self.session)
            with patch.object(private_entry, "SessionLocal", binder):
                with patch.object(private_entry, "_send_catalog_overview", new_callable=AsyncMock):
                    await private_entry.handle_start(message, state, command)

            intro_text = message.answer.call_args[0][0]
            self.assertIn("Thanks for opening this chat from the group", intro_text)

        self._run(body())

        n = self.session.scalar(
            select(func.count())
            .select_from(Handoff)
            .where(
                Handoff.user_id == user_id,
                Handoff.reason == HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            )
        )
        self.assertEqual(n, 0)

    def test_grp_followup_closed_shows_resolved_intro_and_opens_new_row(self) -> None:
        """Phase 7 / Step 16 — resolved group_followup_start triggers closure copy; persist adds new open row."""
        user_id = self.create_user(telegram_user_id=88_210, preferred_language="en").id
        self.session.add(
            Handoff(
                user_id=user_id,
                order_id=None,
                reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
                priority="normal",
                status="closed",
            )
        )
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=88_210)
            state = MagicMock()
            state.clear = AsyncMock()
            command = MagicMock()
            command.args = "grp_followup"
            binder = _SessionLocalBinder(self.session)
            with patch.object(private_entry, "SessionLocal", binder):
                with patch.object(private_entry, "_send_catalog_overview", new_callable=AsyncMock):
                    await private_entry.handle_start(message, state, command)

            intro_text = message.answer.call_args[0][0]
            self.assertIn("resolved", intro_text.lower())

        self._run(body())

        n_open = self.session.scalar(
            select(func.count())
            .select_from(Handoff)
            .where(
                Handoff.user_id == user_id,
                Handoff.reason == HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
                Handoff.status == "open",
            )
        )
        self.assertEqual(n_open, 1)

    def test_grp_followup_in_review_shows_readiness_in_progress(self) -> None:
        user_id = self.create_user(telegram_user_id=88_211, preferred_language="en").id
        op_id = self.create_user(telegram_user_id=88_311).id
        self.session.add(
            Handoff(
                user_id=user_id,
                order_id=None,
                reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
                priority="normal",
                status="in_review",
                assigned_operator_id=op_id,
            )
        )
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=88_211)
            state = MagicMock()
            state.clear = AsyncMock()
            command = MagicMock()
            command.args = "grp_followup"
            binder = _SessionLocalBinder(self.session)
            with patch.object(private_entry, "SessionLocal", binder):
                with patch.object(private_entry, "_send_catalog_overview", new_callable=AsyncMock):
                    await private_entry.handle_start(message, state, command)

            intro_text = message.answer.call_args[0][0]
            self.assertIn("working on", intro_text.lower())
            self.assertNotIn("marked resolved", intro_text.lower())

        self._run(body())

    def test_grp_followup_open_assigned_shows_readiness_assigned(self) -> None:
        user_id = self.create_user(telegram_user_id=88_213, preferred_language="en").id
        op_id = self.create_user(telegram_user_id=88_313).id
        self.session.add(
            Handoff(
                user_id=user_id,
                order_id=None,
                reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
                priority="normal",
                status="open",
                assigned_operator_id=op_id,
            )
        )
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=88_213)
            state = MagicMock()
            state.clear = AsyncMock()
            command = MagicMock()
            command.args = "grp_followup"
            binder = _SessionLocalBinder(self.session)
            with patch.object(private_entry, "SessionLocal", binder):
                with patch.object(private_entry, "_send_catalog_overview", new_callable=AsyncMock):
                    await private_entry.handle_start(message, state, command)

            intro_text = message.answer.call_args[0][0]
            self.assertIn("reviewing", intro_text.lower())
            self.assertNotIn("marked resolved", intro_text.lower())

        self._run(body())

    def test_grp_followup_only_private_contact_closed_uses_generic_intro(self) -> None:
        user_id = self.create_user(telegram_user_id=88_212, preferred_language="en").id
        self.session.add(
            Handoff(
                user_id=user_id,
                order_id=None,
                reason="private_contact",
                priority="normal",
                status="closed",
            )
        )
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=88_212)
            state = MagicMock()
            state.clear = AsyncMock()
            command = MagicMock()
            command.args = "grp_followup"
            binder = _SessionLocalBinder(self.session)
            with patch.object(private_entry, "SessionLocal", binder):
                with patch.object(private_entry, "_send_catalog_overview", new_callable=AsyncMock):
                    await private_entry.handle_start(message, state, command)

            intro_text = message.answer.call_args[0][0]
            self.assertIn("Thanks for continuing", intro_text)

        self._run(body())

    def test_legacy_tour_start_payload_still_reaches_tour_detail(self) -> None:
        tour = self.create_tour(code="CHAIN-LEGACY-1", title_default="Legacy Chain", status=TourStatus.OPEN_FOR_SALE)
        self.create_translation(tour, language_code="en", title="Legacy Title EN")
        self.create_boarding_point(tour, city="CityX")
        user = self.create_user(telegram_user_id=88_204, preferred_language="en")
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=88_204)
            state = MagicMock()
            state.clear = AsyncMock()
            command = MagicMock()
            command.args = "tour_CHAIN-LEGACY-1"
            binder = _SessionLocalBinder(self.session)
            with patch.object(private_entry, "SessionLocal", binder):
                await private_entry.handle_start(message, state, command)

            message.answer.assert_called()
            detail_text = message.answer.call_args[0][0]
            self.assertIn("Legacy Title EN", detail_text)

        self._run(body())


if __name__ == "__main__":
    unittest.main()
