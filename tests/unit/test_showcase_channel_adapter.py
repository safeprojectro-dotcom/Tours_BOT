"""B13B: showcase channel adapter wraps Telegram send with no semantic change."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.core.config import Settings
from app.services.showcase_channel_adapter import (
    TELEGRAM_SHOWCASE_PROVIDER,
    ShowcaseChannelPublishRequest,
    TelegramShowcaseChannelAdapter,
)
from app.services.supplier_offer_showcase_message import ShowcasePublication


class TestShowcaseChannelAdapter(unittest.TestCase):
    def test_telegram_adapter_delegates_to_send_showcase_publication(self) -> None:
        cfg = Settings(telegram_bot_token="t")
        adapter = TelegramShowcaseChannelAdapter(settings=cfg)
        pub = ShowcasePublication(caption_html="<b>x</b>", photo_url="https://ex/x.jpg")
        req = ShowcaseChannelPublishRequest(offer_id=3, publication=pub, channel_ref="-1001")
        with patch(
            "app.services.telegram_showcase_client.send_showcase_publication",
            return_value=42,
        ) as m:
            res = adapter.publish(req)
        m.assert_called_once_with(
            bot_token="t",
            chat_id="-1001",
            caption_html="<b>x</b>",
            photo_url="https://ex/x.jpg",
        )
        self.assertEqual(res.provider, TELEGRAM_SHOWCASE_PROVIDER)
        self.assertEqual(res.chat_id, "-1001")
        self.assertEqual(res.message_id, "42")
