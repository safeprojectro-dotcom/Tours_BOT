from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.media_storage_types import MediaStorageBackend


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
    #: BotFather Mini App short name (second path segment) for direct open: ``t.me/{bot}/{short}?startapp=…`` (B15C5).
    telegram_mini_app_short_name: str | None = Field(default=None, alias="TELEGRAM_MINI_APP_SHORT_NAME")
    #: Channel ID (e.g. -1001234567890) for moderated supplier-offer showcase posts (Track 3). Optional until publishing.
    telegram_offer_showcase_channel_id: str | None = Field(default=None, alias="TELEGRAM_OFFER_SHOWCASE_CHANNEL_ID")
    #: Comma-separated Telegram user IDs allowed to access admin bot workspace (Y28.1, fail-closed).
    telegram_admin_allowlist_user_ids: str = Field(default="", alias="TELEGRAM_ADMIN_ALLOWLIST_USER_IDS")
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
    #: Shared secret for read-only admin API (`GET /admin/...`). If unset, admin routes stay disabled.
    admin_api_token: str | None = Field(default=None, alias="ADMIN_API_TOKEN")
    #: S1D-1: predeparture operational sales-push window — departure within N whole-day deltas from ``now``.
    predeparture_sales_push_days_before: int = Field(default=2, alias="PREDEPARTURE_SALES_PUSH_DAYS_BEFORE")
    #: S1D-1: low-availability trigger when remaining seats are in ``1..N`` inclusive.
    low_availability_seats_threshold: int = Field(default=2, alias="LOW_AVAILABILITY_SEATS_THRESHOLD")

    #: B7.4C: durable media ingestion foundation (no real S3 in this slice). Unknown values treated as ``disabled``.
    media_storage_backend: str = Field(default=MediaStorageBackend.DISABLED.value, alias="MEDIA_STORAGE_BACKEND")
    media_storage_bucket: str | None = Field(default=None, alias="MEDIA_STORAGE_BUCKET")
    media_storage_endpoint_url: str | None = Field(default=None, alias="MEDIA_STORAGE_ENDPOINT_URL")
    media_storage_public_base_url: str | None = Field(default=None, alias="MEDIA_STORAGE_PUBLIC_BASE_URL")
    media_storage_region: str | None = Field(default=None, alias="MEDIA_STORAGE_REGION")
    media_storage_access_key_id: str | None = Field(default=None, alias="MEDIA_STORAGE_ACCESS_KEY_ID")
    media_storage_secret_access_key: str | None = Field(default=None, alias="MEDIA_STORAGE_SECRET_ACCESS_KEY")
    media_storage_max_bytes: int = Field(default=15_000_000, alias="MEDIA_STORAGE_MAX_BYTES")
    #: When False, HTTPS cover URLs fail eligibility until policy enables outbound fetch (B7.4B).
    media_storage_allow_https_fetch: bool = Field(default=False, alias="MEDIA_STORAGE_ALLOW_HTTPS_FETCH")

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

    @field_validator("media_storage_backend", mode="before")
    @classmethod
    def _coerce_media_storage_backend(cls, v: object) -> str:
        if v is None or (isinstance(v, str) and not str(v).strip()):
            return MediaStorageBackend.DISABLED.value
        s = str(v).strip().lower()
        allowed = {m.value for m in MediaStorageBackend}
        return s if s in allowed else MediaStorageBackend.DISABLED.value

    @field_validator("media_storage_max_bytes", mode="before")
    @classmethod
    def _coerce_media_storage_max_bytes(cls, v: object) -> int:
        if v is None or v == "":
            return 15_000_000
        try:
            n = int(v)
        except (TypeError, ValueError):
            return 15_000_000
        #: ~1 KiB .. ~500 MB; clamp invalid env to default.
        if n < 1024 or n > 500_000_000:
            return 15_000_000
        return n

    @field_validator(
        "media_storage_bucket",
        "media_storage_endpoint_url",
        "media_storage_public_base_url",
        "media_storage_region",
        "media_storage_access_key_id",
        "media_storage_secret_access_key",
        mode="before",
    )
    @classmethod
    def _empty_media_storage_str_none(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        s = str(v).strip()
        return s or None

    @field_validator("predeparture_sales_push_days_before", mode="before")
    @classmethod
    def _coerce_predeparture_sales_push_days_before(cls, v: object) -> int:
        if v is None or v == "":
            return 2
        try:
            n = int(v)
        except (TypeError, ValueError):
            return 2
        return max(1, min(30, n))

    @field_validator("low_availability_seats_threshold", mode="before")
    @classmethod
    def _coerce_low_availability_seats_threshold(cls, v: object) -> int:
        if v is None or v == "":
            return 2
        try:
            n = int(v)
        except (TypeError, ValueError):
            return 2
        return max(1, min(500, n))

    @field_validator("media_storage_allow_https_fetch", mode="before")
    @classmethod
    def _coerce_media_storage_allow_https_fetch(cls, v: object) -> bool:
        if v is None or v == "":
            return False
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        return s in {"1", "true", "yes", "on"}

    @property
    def media_storage_backend_parsed(self) -> MediaStorageBackend:
        return MediaStorageBackend(self.media_storage_backend)

    @property
    def telegram_supported_language_codes(self) -> tuple[str, ...]:
        codes = [code.strip().lower() for code in self.telegram_supported_languages.split(",")]
        return tuple(code for code in codes if code)

    @property
    def telegram_admin_allowlist_ids(self) -> tuple[int, ...]:
        out: list[int] = []
        for raw in self.telegram_admin_allowlist_user_ids.split(","):
            txt = raw.strip()
            if not txt:
                continue
            try:
                out.append(int(txt))
            except ValueError:
                continue
        return tuple(out)


@lru_cache
def get_settings() -> Settings:
    return Settings()
