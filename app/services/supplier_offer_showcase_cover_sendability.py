"""Deterministic rules for whether a cover reference may be passed to Telegram ``sendPhoto`` (B15C4).

No network I/O — shape/host heuristics only. telegram_photo:file_id and direct HTTPS URLs that are not
known link/share hosts are treated as sendable.
"""

from __future__ import annotations

from urllib.parse import urlparse

from app.bot.constants import SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX

# Host substrings that indicate a web page / share flow, not a direct image asset for sendPhoto (B15C4).
_TELEGRAM_SHOWCASE_COVER_URL_HOST_DENY_SUBSTRINGS: tuple[str, ...] = (
    "share.google",
    "drive.google",
    "docs.google",
    "photos.google",
    "maps.google",
    "mail.google",
    "lens.google",
    "photos.app.goo.gl",
    "youtube.com",
    "youtu.be",
    "facebook.com",
    "fb.watch",
)


def _host_blocked_for_showcase_photo(host: str) -> bool:
    h = (host or "").lower()
    return any(fragment in h for fragment in _TELEGRAM_SHOWCASE_COVER_URL_HOST_DENY_SUBSTRINGS)


def raw_cover_to_telegram_photo_send_argument(ref: str | None) -> str | None:
    """Telegram ``sendPhoto`` ``photo`` argument: ``file_id`` or URL string, or ``None`` if not sendable."""

    s = (ref or "").strip()
    if not s:
        return None
    if s.startswith(SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX):
        fid = s.removeprefix(SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX).strip()
        return fid or None
    low = s.lower()
    if low.startswith(("http://", "https://")):
        parsed = urlparse(s)
        if not parsed.netloc:
            return None
        if _host_blocked_for_showcase_photo(parsed.netloc):
            return None
        return s
    return None


def is_raw_cover_reference_sendable_for_telegram_sendphoto(ref: str | None) -> bool:
    return raw_cover_to_telegram_photo_send_argument(ref) is not None
