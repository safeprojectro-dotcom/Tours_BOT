from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Tours_BOT", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="APP_LOG_LEVEL")
    database_url: str = Field(alias="DATABASE_URL")
    database_connect_timeout: int = Field(default=5, alias="DATABASE_CONNECT_TIMEOUT")
    payment_webhook_secret: str | None = Field(default=None, alias="PAYMENT_WEBHOOK_SECRET")
    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_bot_username: str | None = Field(default=None, alias="TELEGRAM_BOT_USERNAME")
    telegram_webhook_secret: str | None = Field(default=None, alias="TELEGRAM_WEBHOOK_SECRET")
    telegram_webhook_base_url: str | None = Field(default=None, alias="TELEGRAM_WEBHOOK_BASE_URL")
    telegram_mini_app_url: str | None = Field(default=None, alias="TELEGRAM_MINI_APP_URL")
    telegram_default_language: str = Field(default="en", alias="TELEGRAM_DEFAULT_LANGUAGE")
    telegram_supported_languages: str = Field(
        default="en,ro,ru,sr,hu,it,de",
        alias="TELEGRAM_SUPPORTED_LANGUAGES",
    )
    mini_app_default_language: str = Field(default="en", alias="MINI_APP_DEFAULT_LANGUAGE")
    #: If set, temporary reservation hold length in minutes (staging). If unset, use legacy 6h / 24h rule.
    temp_reservation_ttl_minutes: int | None = Field(default=None, alias="TEMP_RESERVATION_TTL_MINUTES")
    #: When True, Mini App may complete mockpay via POST /mini-app/orders/{id}/mock-payment-complete (staging/local).
    enable_mock_payment_completion: bool = Field(default=False, alias="ENABLE_MOCK_PAYMENT_COMPLETION")
    #: Shared secret for read-only ops queue JSON API (`GET /internal/ops/...`). If unset, those routes stay disabled.
    ops_queue_token: str | None = Field(default=None, alias="OPS_QUEUE_TOKEN")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("temp_reservation_ttl_minutes", mode="before")
    @classmethod
    def _coerce_temp_reservation_ttl_minutes(cls, v: object) -> int | None:
        if v is None or v == "":
            return None
        try:
            n = int(v)
        except (TypeError, ValueError):
            return None
        if n < 1 or n > 10080:
            return None
        return n

    @property
    def telegram_supported_language_codes(self) -> tuple[str, ...]:
        codes = [code.strip().lower() for code in self.telegram_supported_languages.split(",")]
        return tuple(code for code in codes if code)


@lru_cache
def get_settings() -> Settings:
    return Settings()
