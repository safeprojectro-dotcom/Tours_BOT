"""Unit tests for in-memory transient message cleanup (Step 12A)."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock

from app.bot import transient_messages as tm
from app.bot.transient_messages import (
    CATALOG_LIST,
    CATALOG_WELCOME,
    FILTER_STEP,
    LANGUAGE_PROMPT,
    register_catalog_bundle,
    register_transient,
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
        self.assertEqual(tm._store[chat_id][CATALOG_WELCOME], 40)
        self.assertEqual(tm._store[chat_id][CATALOG_LIST], 41)
        self.assertNotIn(LANGUAGE_PROMPT, tm._store[chat_id])
        self.assertNotIn(FILTER_STEP, tm._store[chat_id])

    async def test_delete_failure_is_ignored(self) -> None:
        bot = AsyncMock()
        bot.delete_message = AsyncMock(side_effect=Exception("telegram says no"))
        chat_id = 1004
        await register_transient(bot, chat_id, LANGUAGE_PROMPT, 5)
        await register_transient(bot, chat_id, LANGUAGE_PROMPT, 6)
        self.assertEqual(tm._store[chat_id][LANGUAGE_PROMPT], 6)


if __name__ == "__main__":
    unittest.main()
