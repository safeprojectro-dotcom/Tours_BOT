"""Romanian supplier-offer showcase caption, Bucharest datetimes, media routing."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from app.models.enums import SupplierServiceComposition, TourSalesMode
from app.services.supplier_offer_showcase_message import (
    build_showcase_publication,
    format_datetime_ro_bucharest,
    parse_boarding_places,
)
from app.services.telegram_showcase_client import send_channel_html_message, send_showcase_publication


def _cfg() -> SimpleNamespace:
    return SimpleNamespace(
        telegram_bot_username="mybot",
        telegram_mini_app_url="https://t.me/mybot/miniapp",
    )


def _offer(**kwargs: object) -> SimpleNamespace:
    defaults: dict[str, object] = {
        "id": 7,
        "title": "Excursie demo",
        "description": "O scurtă descriere atrăgătoare.",
        "departure_datetime": datetime(2026, 5, 10, 8, 0, tzinfo=UTC),
        "return_datetime": datetime(2026, 5, 11, 18, 0, tzinfo=UTC),
        "sales_mode": TourSalesMode.PER_SEAT,
        "boarding_places_text": None,
        "vehicle_label": "Autocar",
        "transport_notes": None,
        "seats_total": 48,
        "base_price": Decimal("99.00"),
        "currency": "EUR",
        "service_composition": SupplierServiceComposition.TRANSPORT_ONLY,
        "showcase_photo_url": None,
        "short_hook": None,
        "marketing_summary": None,
        "included_text": None,
        "excluded_text": None,
        "program_text": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class SupplierOfferShowcaseRoTests(unittest.TestCase):
    def test_format_datetime_bucharest_summer(self) -> None:
        s = format_datetime_ro_bucharest(datetime(2026, 5, 10, 8, 0, tzinfo=UTC))
        self.assertEqual(s, "10 mai 2026, 11:00")

    def test_format_datetime_bucharest_winter(self) -> None:
        s = format_datetime_ro_bucharest(datetime(2026, 1, 10, 8, 0, tzinfo=UTC))
        self.assertEqual(s, "10 ianuarie 2026, 10:00")

    def test_parse_boarding_empty(self) -> None:
        self.assertEqual(parse_boarding_places(None), [])
        self.assertEqual(parse_boarding_places("   "), [])

    def test_parse_boarding_single(self) -> None:
        self.assertEqual(parse_boarding_places("Timișoara"), ["Timișoara"])

    def test_parse_boarding_multi_separators(self) -> None:
        raw = "Timișoara | Lugoj\nCaransebeș"
        self.assertEqual(parse_boarding_places(raw), ["Timișoara", "Lugoj", "Caransebeș"])

    def test_caption_romanian_labels_and_no_raw_sales_mode(self) -> None:
        pub = build_showcase_publication(_offer(), _cfg())
        cap = pub.caption_html
        self.assertIn("📅", cap)
        self.assertIn("10–11 mai 2026", cap)
        self.assertIn("<b>Plecare:</b>", cap)
        self.assertIn("<b>Întoarcere:</b>", cap)
        self.assertIn("🚐 <b>Transport:</b>", cap)
        self.assertIn("👥 <b>Capacitate:</b>", cap)
        self.assertIn("💰 <b>Preț:</b>", cap)
        self.assertIn("orientativ", cap)
        self.assertIn("Ai nevoie de alt traseu", cap)
        self.assertIn("Detalii", cap)
        self.assertIn("Rezervă", cap)
        self.assertIn("/supplier-offers/7", cap)
        self.assertIn("Abonează-te la canal", cap)
        self.assertNotIn("full_bus", cap.lower())
        self.assertNotIn("per_seat", cap.lower())
        self.assertNotIn("payment_mode", cap.lower())

    def test_cta_detalii_links_bot_rezerva_links_mini_app(self) -> None:
        pub = build_showcase_publication(_offer(), _cfg())
        cap = pub.caption_html
        self.assertRegex(cap, r'<a href="https://t\.me/mybot\?start=supoffer_7">Detalii</a>')
        self.assertRegex(cap, r'<a href="https://t\.me/mybot/miniapp/supplier-offers/7">Rezervă</a>')

    def test_full_bus_soft_phrase_not_raw_enum(self) -> None:
        pub = build_showcase_publication(_offer(sales_mode=TourSalesMode.FULL_BUS), _cfg())
        cap = pub.caption_html
        self.assertIn("/ grup", cap)
        self.assertIn("🚌 <b>Format:</b>", cap)
        self.assertIn("Locurile individuale nu se vând separat", cap)
        self.assertNotIn("orientativ", cap)
        self.assertNotIn("FULL_BUS", cap)

    def test_boarding_one_place(self) -> None:
        pub = build_showcase_publication(
            _offer(boarding_places_text="Timișoara"),
            _cfg(),
        )
        self.assertIn("<b>Ruta:</b> Timișoara", pub.caption_html)

    def test_boarding_multiple_compact(self) -> None:
        pub = build_showcase_publication(
            _offer(boarding_places_text="Timișoara|Lugoj"),
            _cfg(),
        )
        self.assertIn("<b>Ruta:</b>", pub.caption_html)
        self.assertIn("Timișoara → Lugoj", pub.caption_html)

    def test_no_boarding_omits_line(self) -> None:
        pub = build_showcase_publication(_offer(boarding_places_text=None), _cfg())
        self.assertNotIn("Îmbarcare", pub.caption_html)
        self.assertNotIn("<b>Ruta:", pub.caption_html)

    def test_include_nu_include_from_composition(self) -> None:
        pub = build_showcase_publication(_offer(), _cfg())
        self.assertIn("<b>Include:</b>", pub.caption_html)
        self.assertIn("• transport", pub.caption_html)
        self.assertIn("❌ <b>Nu include:</b>", pub.caption_html)
        self.assertIn("bilete de intrare", pub.caption_html)

    def test_program_section_when_program_text_set(self) -> None:
        pub = build_showcase_publication(
            _offer(program_text="Plecare din X\n• Etapă 2"),
            _cfg(),
        )
        cap = pub.caption_html
        self.assertIn("🗺️ <b>Program:</b>", cap)
        self.assertIn("Plecare din X", cap)
        self.assertIn("Etapă 2", cap)

    def test_photo_url_always_none_text_first_b12(self) -> None:
        """B12/B13: channel send is text-only; showcase_photo_url ignored for publication payload."""
        pub = build_showcase_publication(
            _offer(showcase_photo_url=" https://cdn.example.com/a.jpg "),
            _cfg(),
        )
        self.assertIsNone(pub.photo_url)

    def test_photo_url_none_when_missing(self) -> None:
        pub = build_showcase_publication(_offer(showcase_photo_url=None), _cfg())
        self.assertIsNone(pub.photo_url)

    def test_send_showcase_uses_photo_when_url(self) -> None:
        with patch("app.services.telegram_showcase_client.send_channel_photo", return_value=10) as ph:
            with patch("app.services.telegram_showcase_client.send_channel_html_message") as msg:
                mid = send_showcase_publication(
                    bot_token="t",
                    chat_id="-100",
                    caption_html="<b>x</b>",
                    photo_url="https://ph.example/x.jpg",
                )
        self.assertEqual(mid, 10)
        ph.assert_called_once()
        msg.assert_not_called()
        kw = ph.call_args.kwargs
        self.assertEqual(kw["photo"], "https://ph.example/x.jpg")

    def test_send_showcase_text_fallback_without_photo(self) -> None:
        with patch("app.services.telegram_showcase_client.send_channel_photo") as ph:
            with patch(
                "app.services.telegram_showcase_client.send_channel_html_message",
                return_value=20,
            ) as msg:
                mid = send_showcase_publication(
                    bot_token="t",
                    chat_id="-100",
                    caption_html="cap",
                    photo_url=None,
                )
        self.assertEqual(mid, 20)
        ph.assert_not_called()
        msg.assert_called_once()
        self.assertEqual(msg.call_args.kwargs.get("disable_web_page_preview"), True)
        self.assertEqual(msg.call_args.kwargs.get("text"), "cap")

    def test_send_showcase_publication_preserves_links_in_caption_when_no_preview(self) -> None:
        cap = '<a href="https://t.me/bot?start=supoffer_1">Detalii</a>'
        with patch(
            "app.services.telegram_showcase_client._post_telegram_api",
            return_value=77,
        ) as post:
            mid = send_showcase_publication(
                bot_token="tok",
                chat_id="-100",
                caption_html=cap,
                photo_url=None,
            )
        self.assertEqual(mid, 77)
        payload = post.call_args.kwargs["payload"]
        self.assertEqual(payload["text"], cap)
        self.assertEqual(payload["parse_mode"], "HTML")
        self.assertTrue(payload["disable_web_page_preview"])
        post.assert_called_once()
        kw = post.call_args.kwargs
        self.assertEqual(kw["method"], "sendMessage")

    def test_send_channel_html_message_disables_preview_by_default(self) -> None:
        with patch("app.services.telegram_showcase_client._post_telegram_api", return_value=5) as post:
            send_channel_html_message(bot_token="a", chat_id="x", text="y")
        self.assertTrue(post.call_args.kwargs["payload"]["disable_web_page_preview"])


if __name__ == "__main__":
    unittest.main()
