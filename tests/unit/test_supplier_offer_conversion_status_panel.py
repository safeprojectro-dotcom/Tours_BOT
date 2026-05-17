"""C2B11A conversion status panel — formatting and schema wiring."""

from __future__ import annotations

import unittest

from app.bot.messages import translate
from app.bot.supplier_offer_conversion_status_panel_telegram import (
    format_conversion_status_panel_for_telegram,
)
from app.schemas.supplier_admin import (
    AdminSupplierOfferConversionStatusPanelLayerRead,
    AdminSupplierOfferConversionStatusPanelRead,
)


class ConversionStatusPanelTelegramFormatTests(unittest.TestCase):
    def test_panel_lines_use_i18n_keys(self) -> None:
        panel = AdminSupplierOfferConversionStatusPanelRead(
            showcase=AdminSupplierOfferConversionStatusPanelLayerRead(
                status="published",
                summary="Showcase: published (offer lifecycle is published).",
            ),
            tour_bridge=AdminSupplierOfferConversionStatusPanelLayerRead(
                status="linked",
                summary="Tour bridge: linked.",
            ),
            catalog=AdminSupplierOfferConversionStatusPanelLayerRead(
                status="listed_for_sale",
                summary="Catalog: listed.",
            ),
            booking_link=AdminSupplierOfferConversionStatusPanelLayerRead(
                status="active",
                summary="Booking link: active.",
            ),
            customer_action=AdminSupplierOfferConversionStatusPanelLayerRead(
                status="open_exact_mini_app_tour",
                summary="Customer: open tour.",
                detail="tour_code=X",
            ),
        )
        text = format_conversion_status_panel_for_telegram(panel, language_code="en", translate_fn=translate)
        self.assertIn("Conversion status", text)
        self.assertIn("Showcase: Published", text)
        self.assertNotIn("tour_code=X", text)
        self.assertIn("Requires internal verification", text)

    def test_ro_panel_header(self) -> None:
        panel = AdminSupplierOfferConversionStatusPanelRead(
            showcase=AdminSupplierOfferConversionStatusPanelLayerRead(status="not_published", summary="…"),
            tour_bridge=AdminSupplierOfferConversionStatusPanelLayerRead(status="missing", summary="…"),
            catalog=AdminSupplierOfferConversionStatusPanelLayerRead(status="not_listed", summary="…"),
            booking_link=AdminSupplierOfferConversionStatusPanelLayerRead(status="missing", summary="…"),
            customer_action=AdminSupplierOfferConversionStatusPanelLayerRead(status="not_bookable_yet", summary="…"),
        )
        text = format_conversion_status_panel_for_telegram(panel, language_code="ro", translate_fn=translate)
        self.assertIn("conversie", text.lower())


if __name__ == "__main__":
    unittest.main()
