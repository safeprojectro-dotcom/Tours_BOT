"""B3.1: Telegram cover photo in supplier offer intake (file_id, no download)."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from app.bot.constants import SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX
from app.bot.handlers import supplier_offer_intake
from app.bot.state import SupplierOfferIntakeState


def _ps(file_id: str, *, w: int, h: int, fsize: int, uid: str = "UQ") -> MagicMock:
    p = MagicMock()
    p.file_id = file_id
    p.file_unique_id = uid
    p.width = w
    p.height = h
    p.file_size = fsize
    return p


def _msg_photo(telegram_user_id: int, photos: list, *, media_group_id: int | None = None) -> MagicMock:
    message = MagicMock()
    message.from_user = MagicMock()
    message.from_user.id = telegram_user_id
    message.from_user.language_code = "en"
    message.text = None
    message.caption = None
    message.photo = photos
    message.media_group_id = media_group_id
    message.document = None
    message.video = None
    message.answer = AsyncMock(return_value=MagicMock(message_id=1))
    return message


class _DictFSM:
    def __init__(self) -> None:
        self.data: dict = {}
        self.last_state = None

    async def update_data(self, data: dict | None = None, **kwargs: object) -> dict:
        if data:
            self.data.update(dict(data))
        if kwargs:
            self.data.update(kwargs)
        return dict(self.data)

    async def get_data(self) -> dict:
        return dict(self.data)

    async def set_state(self, value) -> None:
        self.last_state = value


class B31CoverPhotoIntakeTests(unittest.TestCase):
    @staticmethod
    def _run(coro) -> None:
        asyncio.run(coro)

    def test_accepts_largest_telegram_photo_stores_file_id(self) -> None:
        small = _ps("small", w=200, h=200, fsize=1000, uid="a")
        large = _ps("LARGE_ID", w=1000, h=800, fsize=90_000, uid="b")
        m = _msg_photo(9_201_100, [small, large])
        st = _DictFSM()
        st.data["mock"] = 1
        st.last_state = SupplierOfferIntakeState.choosing_cover_media

        async def body() -> None:
            await supplier_offer_intake.intake_cover_photo_choosing(m, st)  # type: ignore[arg-type]
            self.assertEqual(st.data.get("cover_step"), "telegram")
            self.assertEqual(st.data.get("cover_media_reference"), f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}LARGE_ID")
            self.assertEqual(st.data.get("cover_media_meta", {}).get("file_id"), "LARGE_ID")
            self.assertEqual(st.data.get("cover_media_meta", {}).get("width"), 1000)
            self.assertEqual(st.data.get("cover_media_meta", {}).get("source"), "telegram_photo")
            self.assertEqual(st.last_state, SupplierOfferIntakeState.entering_vehicle_or_notes)
            m.answer.assert_awaited()

        self._run(body())

    def test_rejects_below_minimum_pixels(self) -> None:
        small = _ps("x", w=700, h=400, fsize=5000, uid="s")
        m = _msg_photo(9_201_101, [small])
        st = _DictFSM()
        st.last_state = SupplierOfferIntakeState.choosing_cover_media

        async def body() -> None:
            await supplier_offer_intake.intake_cover_photo_choosing(m, st)  # type: ignore[arg-type]
            self.assertIsNone(st.data.get("cover_step"))
            self.assertEqual(st.last_state, SupplierOfferIntakeState.choosing_cover_media)
            out = m.answer.call_args[0][0]
            self.assertIn("800", out)
            self.assertIn("500", out)

        self._run(body())

    def test_rejects_album_media_group(self) -> None:
        p = _ps("a", w=1000, h=800, fsize=10_000)
        m = _msg_photo(9_201_102, [p], media_group_id=42)
        st = _DictFSM()
        st.last_state = SupplierOfferIntakeState.choosing_cover_media

        async def body() -> None:
            await supplier_offer_intake.intake_cover_photo_choosing(m, st)  # type: ignore[arg-type]
            self.assertEqual(st.last_state, SupplierOfferIntakeState.choosing_cover_media)
            self.assertIn("one image", m.answer.call_args[0][0].lower())

        self._run(body())

    def test_rejects_document_not_photo_choosing(self) -> None:
        m = MagicMock()
        m.from_user = MagicMock()
        m.from_user.id = 9_201_103
        m.from_user.language_code = "en"
        m.text = None
        m.document = MagicMock()
        m.photo = None
        m.answer = AsyncMock()
        st = _DictFSM()
        st.last_state = SupplierOfferIntakeState.choosing_cover_media

        async def body() -> None:
            await supplier_offer_intake.intake_cover_reject_unsupported_choosing(m, st)  # type: ignore[arg-type]
            self.assertIn("photo", m.answer.call_args[0][0].lower())
            st.last_state = SupplierOfferIntakeState.choosing_cover_media

        self._run(body())

    def test_rejects_document_in_entering_url_state(self) -> None:
        m = MagicMock()
        m.from_user = MagicMock()
        m.from_user.id = 9_201_104
        m.from_user.language_code = "en"
        m.text = None
        m.document = MagicMock()
        m.photo = None
        m.answer = AsyncMock()
        st = _DictFSM()
        st.last_state = SupplierOfferIntakeState.entering_cover_url
        st.data = {"cover_intake_path": "url"}

        async def body() -> None:
            await supplier_offer_intake.intake_cover_reject_unsupported_url_state(m, st)  # type: ignore[arg-type]
            self.assertIn("photo", m.answer.call_args[0][0].lower())
            self.assertEqual(st.last_state, SupplierOfferIntakeState.entering_cover_url)

        self._run(body())

    def test_accepts_photo_from_entering_cover_url_state(self) -> None:
        p = _ps("from_url", w=1000, h=800, fsize=20_000)
        m = _msg_photo(9_201_105, [p])
        st = _DictFSM()
        st.last_state = SupplierOfferIntakeState.entering_cover_url
        st.data = {"cover_intake_path": "url", "cover_step": "url"}

        async def body() -> None:
            await supplier_offer_intake.intake_cover_photo_url_state(m, st)  # type: ignore[arg-type]
            self.assertEqual(st.data.get("cover_step"), "telegram")
            self.assertTrue(str(st.data.get("cover_media_reference", "")).startswith(SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX + "from_url"))
            self.assertEqual(st.last_state, SupplierOfferIntakeState.entering_vehicle_or_notes)
            m.answer.assert_awaited()

        self._run(body())

    def test_paste_https_url_in_entering_cover_url_still_works(self) -> None:
        m = MagicMock()
        m.from_user = MagicMock()
        m.from_user.id = 9_201_106
        m.from_user.language_code = "en"
        m.text = "https://example.com/cover.jpg"
        m.answer = AsyncMock()
        st = _DictFSM()
        st.last_state = SupplierOfferIntakeState.entering_cover_url
        st.data = {"cover_intake_path": "url"}

        async def body() -> None:
            await supplier_offer_intake.intake_cover_url(m, st)  # type: ignore[arg-type]
            self.assertEqual(st.data.get("cover_media_reference"), "https://example.com/cover.jpg")
            self.assertEqual(st.data.get("cover_step"), "url")
            self.assertEqual(st.data.get("cover_intake_path"), "url")
            self.assertEqual(st.last_state, SupplierOfferIntakeState.entering_vehicle_or_notes)

        self._run(body())

    def test_cover_display_hides_telegram_file_id(self) -> None:
        d = {
            "cover_step": "telegram",
            "cover_media_reference": f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}abc123",
        }
        t = supplier_offer_intake._cover_display(d, "en")
        self.assertNotIn("abc123", t)
        self.assertNotIn("telegram_photo:", t.lower())
        self.assertIn("Photo uploaded", t)

    def test_build_create_payload_telegram_media_references(self) -> None:
        from app.models.supplier import Supplier
        from app.models.enums import SupplierServiceComposition

        sup = MagicMock(spec=Supplier)
        sup.onboarding_service_composition = SupplierServiceComposition.TRANSPORT_ONLY
        data = {
            "title": "T",
            "description": "D",
            "departure_datetime": "2026-10-01T10:00:00+00:00",
            "return_datetime": "2026-10-02T18:00:00+00:00",
            "seats_total": 10,
            "base_price": "1",
            "currency": "EUR",
            "sales_mode": "per_seat",
            "payment_mode": "platform_checkout",
            "program_text": "p",
            "schedule_kind": "one_trip",
            "cover_step": "telegram",
            "cover_media_reference": f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}F",
            "cover_media_meta": {
                "source": "telegram_photo",
                "file_id": "F",
                "file_unique_id": "U",
                "width": 1000,
                "height": 800,
            },
        }
        p = supplier_offer_intake._build_create_payload(sup, data)  # type: ignore[arg-type]
        self.assertIsNotNone(p.media_references)
        assert p.media_references is not None
        self.assertEqual(len(p.media_references), 1)
        m0 = p.media_references[0]
        self.assertEqual(m0.get("role"), "cover")
        self.assertEqual(m0.get("source"), "telegram_photo")
        self.assertEqual(m0.get("file_id"), "F")
        self.assertIn("ref", m0)
