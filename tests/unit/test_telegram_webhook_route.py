from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


class TelegramWebhookRouteTests(unittest.TestCase):
    def tearDown(self) -> None:
        get_settings.cache_clear()

    def test_webhook_rejects_bad_secret(self) -> None:
        get_settings.cache_clear()
        fake = "123456:AA-" + "x" * 40
        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": fake,
                "TELEGRAM_WEBHOOK_SECRET": "good-secret-token",
            },
        ):
            get_settings.cache_clear()
            app = create_app()
            with TestClient(app) as client:
                response = client.post(
                    "/telegram/webhook",
                    json={"update_id": 1},
                    headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
                )
        self.assertEqual(response.status_code, 401)

    def test_webhook_503_when_bot_token_missing(self) -> None:
        get_settings.cache_clear()
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": ""}):
            get_settings.cache_clear()
            app = create_app()
            with TestClient(app) as client:
                response = client.post("/telegram/webhook", json={"update_id": 1})
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
