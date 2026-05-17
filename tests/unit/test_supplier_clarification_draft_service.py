"""A3/A3B: supplier clarification drafts — whitelist only, technical routing internal."""

from __future__ import annotations

from unittest import TestCase

from app.schemas.supplier_offer_intake_validation import SupplierOfferIntakeValidationRead
from app.services.supplier_clarification_draft_service import SupplierClarificationDraftService


class SupplierClarificationDraftServiceTests(TestCase):
    def test_technical_signals_never_in_supplier_copy(self) -> None:
        intake = SupplierOfferIntakeValidationRead(
            supplier_offer_id=7,
            headline="test",
            facts_missing_required=["preview_customer_body"],
            facts_weak_or_unclear=[],
            blocks_publication=[
                "gate:showcase_media:media_review_replacement_requested",
                "publish_readiness:blocked",
            ],
            blocks_catalog_conversion=["prepare_chain:blocked:create_tour_bridge"],
            suggested_supplier_requests=[
                "CTA target not verified.",
                "Touch the Mini App once.",
                "Wire payment instructions",
            ],
        )
        d = SupplierClarificationDraftService.build_from_intake_validation(intake)
        self.assertEqual(d.draft_version, "a3b_v1")
        joined_supplier = "\n".join(d.supplier_facing_asks).lower()
        msg = (d.supplier_facing_message_ro or "").lower()
        for bad in (
            "prepare_chain",
            "gate:",
            "cta",
            "mini app",
            "publish_readiness",
            "execution",
            "wire payment",
            "showcase_media",
        ):
            self.assertNotIn(bad, joined_supplier, bad)
            self.assertNotIn(bad, msg, bad)
        self.assertTrue(all(x in _WHITELIST for x in d.supplier_facing_asks), d.supplier_facing_asks)
        self.assertIn("descriere", (d.supplier_facing_message_ro or "").lower())
        self.assertIn("bună ziua", (d.supplier_facing_message_ro or "").lower())
        self.assertIn("mulțumim", (d.supplier_facing_message_ro or "").lower())
        internal_joined = " ".join(d.internal_admin_tasks).lower()
        self.assertIn("prepare_chain", internal_joined)

    def test_packaging_weak_maps_to_description_ask_only(self) -> None:
        intake = SupplierOfferIntakeValidationRead(
            supplier_offer_id=1,
            headline="x",
            facts_missing_required=[],
            facts_weak_or_unclear=["packaging:needs_admin_review"],
            blocks_publication=[],
            blocks_catalog_conversion=[],
            suggested_supplier_requests=[],
        )
        d = SupplierClarificationDraftService.build_from_intake_validation(intake)
        self.assertEqual(len(d.supplier_facing_asks), 1)
        self.assertIn("descriere scurtă", d.supplier_facing_asks[0].lower())
        self.assertTrue(any("packaging" in x.lower() for x in d.internal_admin_tasks))


_WHITELIST = frozenset(
    (
        "Vă rugăm să trimiteți o fotografie clară pentru ofertă.",
        "Vă rugăm să confirmați prețul pentru această ofertă.",
        "Vă rugăm să confirmați moneda prețului.",
        "Vă rugăm să confirmați data și ora plecării.",
        "Vă rugăm să confirmați data și ora întoarcerii.",
        "Vă rugăm să confirmați ruta și destinația.",
        "Vă rugăm să confirmați locul de îmbarcare.",
        "Vă rugăm să confirmați durata aproximativă a drumului.",
        "Vă rugăm să confirmați câte locuri sunt disponibile.",
        "Vă rugăm să confirmați tipul vehiculului.",
        "Vă rugăm să confirmați ce este inclus în preț.",
        "Vă rugăm să confirmați ce nu este inclus în preț.",
        "Vă rugăm să trimiteți o descriere scurtă a excursiei.",
        "Vă rugăm să confirmați dacă există reducere pentru această ofertă.",
        "Dacă există reducere, vă rugăm să confirmați valoarea, perioada și condițiile reducerii.",
        "Vă rugăm să confirmați condițiile de plată.",
        "Vă rugăm să confirmați condițiile de anulare.",
    )
)
