"""Reusable aiogram filters for private chat routing."""

from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import Message


class NotSlashCommandFilter(BaseFilter):
    """
    True for messages that are not a slash command (text missing, or text does not start with /).

    Lets explicit /command handlers run while FSM states would otherwise repeat prompts for any text.
    """

    async def __call__(self, message: Message) -> bool:
        text = message.text
        if text is None:
            return True
        return not text.lstrip().startswith("/")
