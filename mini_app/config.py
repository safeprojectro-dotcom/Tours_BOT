from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MiniAppSettings(BaseSettings):
    app_env: str = Field(default="local", alias="APP_ENV")
    mini_app_title: str = Field(default="Tours_BOT Mini App", alias="MINI_APP_TITLE")
    mini_app_api_base_url: str = Field(default="http://127.0.0.1:8000", alias="MINI_APP_API_BASE_URL")
    mini_app_default_language: str = Field(default="en", alias="MINI_APP_DEFAULT_LANGUAGE")
    # Until Mini App Telegram init-data auth exists, API calls use this Telegram user id (local/dev).
    mini_app_dev_telegram_user_id: int = Field(default=100_001, alias="MINI_APP_DEV_TELEGRAM_USER_ID")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def normalized_api_base_url(self) -> str:
        return self.mini_app_api_base_url.rstrip("/")


@lru_cache
def get_mini_app_settings() -> MiniAppSettings:
    return MiniAppSettings()
