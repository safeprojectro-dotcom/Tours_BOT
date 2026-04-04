"""Unit tests for in-memory transient message cleanup (Steps 12A / 12B)."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock

from app.bot import transient_messages as tm
from app.bot.transient_messages import (
    CATALOG_MESSAGE,
    FILTER_STEP,
    HOME_MESSAGE,
    LANGUAGE_PROMPT,
    register_catalog_bundle,
    register_transient,
    send_or_edit_home_catalog_pair,
)


class TransientMessagesTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        tm._store.clear()

    async def test_register_transient_replaces_same_category_and_deletes_old(self) -> None:
        bot = AsyncMock()
        chat_id = 1001
        await register_transient(bot, chat_id, LANGUAGE_PROMPT, 10)
        await register_transient(bot, chat_id, LANGUAGE_PROMPT, 20)
        bot.delete_message.assert_awaited_once_with(chat_id=chat_id, message_id=10)
        self.assertEqual(tm._store[chat_id][LANGUAGE_PROMPT], 20)

    async def test_register_transient_different_categories_kept(self) -> None:
        bot = AsyncMock()
        chat_id = 1002
        await register_transient(bot, chat_id, LANGUAGE_PROMPT, 1)
        await register_transient(bot, chat_id, FILTER_STEP, 2)
        bot.delete_message.assert_not_awaited()
        self.assertEqual(tm._store[chat_id][LANGUAGE_PROMPT], 1)
        self.assertEqual(tm._store[chat_id][FILTER_STEP], 2)

    async def test_register_catalog_bundle_clears_language_filter_and_old_pair(self) -> None:
        bot = AsyncMock()
        chat_id = 1003
        await register_transient(bot, chat_id, LANGUAGE_PROMPT, 11)
        await register_transient(bot, chat_id, FILTER_STEP, 22)
        await register_catalog_bundle(bot, chat_id, 30, 31)
        # language + filter + no prior catalog → 2 deletes
        self.assertEqual(bot.delete_message.await_count, 2)
        await register_catalog_bundle(bot, chat_id, 40, 41)
        # prior welcome + list → 2 more deletes
        self.assertEqual(bot.delete_message.await_count, 4)
        self.assertEqual(tm._store[chat_id][HOME_MESSAGE], 40)
        self.assertEqual(tm._store[chat_id][CATALOG_MESSAGE], 41)
        self.assertNotIn(LANGUAGE_PROMPT, tm._store[chat_id])
        self.assertNotIn(FILTER_STEP, tm._store[chat_id])

    async def test_delete_failure_is_ignored(self) -> None:
        bot = AsyncMock()
        bot.delete_message = AsyncMock(side_effect=Exception("telegram says no"))
        chat_id = 1004
        await register_transient(bot, chat_id, LANGUAGE_PROMPT, 5)
        await register_transient(bot, chat_id, LANGUAGE_PROMPT, 6)
        self.assertEqual(tm._store[chat_id][LANGUAGE_PROMPT], 6)

    async def test_send_or_edit_prefers_edit_when_both_ids_present(self) -> None:
        bot = AsyncMock()
        bot.edit_message_text = AsyncMock()
        msg = MagicMock()
        msg.bot = bot
        msg.chat.id = 2001
        msg.answer = AsyncMock()
        tm._store[2001] = {HOME_MESSAGE: 10, CATALOG_MESSAGE: 11}

        await send_or_edit_home_catalog_pair(
            msg,
            welcome_text="w",
            welcome_markup=None,
            catalog_text="c",
            catalog_markup=None,
            prefer_edit=True,
        )

        self.assertEqual(bot.edit_message_text.await_count, 2)
        msg.answer.assert_not_awaited()
        self.assertEqual(tm._store[2001][HOME_MESSAGE], 10)
        self.assertEqual(tm._store[2001][CATALOG_MESSAGE], 11)

    async def test_send_or_edit_without_prior_ids_sends_two(self) -> None:
        bot = AsyncMock()
        msg = MagicMock()
        msg.bot = bot
        msg.chat.id = 2002
        sw = MagicMock()
        sw.message_id = 50
        sc = MagicMock()
        sc.message_id = 51
        msg.answer = AsyncMock(side_effect=[sw, sc])

        await send_or_edit_home_catalog_pair(
            msg,
            welcome_text="w",
            welcome_markup=None,
            catalog_text="c",
            catalog_markup=None,
            prefer_edit=True,
        )

        bot.edit_message_text.assert_not_awaited()
        self.assertEqual(msg.answer.await_count, 2)
        self.assertEqual(tm._store[2002][HOME_MESSAGE], 50)
        self.assertEqual(tm._store[2002][CATALOG_MESSAGE], 51)

    async def test_send_or_edit_edit_failure_falls_back_to_send(self) -> None:
        bot = AsyncMock()
        bot.edit_message_text = AsyncMock(side_effect=Exception("cannot edit"))
        msg = MagicMock()
        msg.bot = bot
        msg.chat.id = 2003
        sw = MagicMock()
        sw.message_id = 60
        sc = MagicMock()
        sc.message_id = 61
        msg.answer = AsyncMock(side_effect=[sw, sc])
        tm._store[2003] = {HOME_MESSAGE: 10, CATALOG_MESSAGE: 11}

        await send_or_edit_home_catalog_pair(
            msg,
            welcome_text="w",
            welcome_markup=None,
            catalog_text="c",
            catalog_markup=None,
            prefer_edit=True,
        )

        bot.delete_message.assert_awaited()
        self.assertEqual(msg.answer.await_count, 2)
        self.assertEqual(tm._store[2003][HOME_MESSAGE], 60)
        self.assertEqual(tm._store[2003][CATALOG_MESSAGE], 61)

    async def test_send_or_edit_prefer_edit_false_always_sends(self) -> None:
        bot = AsyncMock()
        msg = MagicMock()
        msg.bot = bot
        msg.chat.id = 2004
        sw = MagicMock()
        sw.message_id = 70
        sc = MagicMock()
        sc.message_id = 71
        msg.answer = AsyncMock(side_effect=[sw, sc])
        tm._store[2004] = {HOME_MESSAGE: 1, CATALOG_MESSAGE: 2}

        await send_or_edit_home_catalog_pair(
            msg,
            welcome_text="w",
            welcome_markup=None,
            catalog_text="c",
            catalog_markup=None,
            prefer_edit=False,
        )

        bot.edit_message_text.assert_not_awaited()
        self.assertEqual(msg.answer.await_count, 2)
        self.assertEqual(tm._store[2004][HOME_MESSAGE], 70)
        self.assertEqual(tm._store[2004][CATALOG_MESSAGE], 71)


if __name__ == "__main__":
    unittest.main()
