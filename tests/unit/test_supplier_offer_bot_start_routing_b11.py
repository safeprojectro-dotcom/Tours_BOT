"""B11: execution-link gated Mini App tour URL for `/start supoffer_<id>`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.models.enums import SupplierOfferLifecycle, TourSalesMode, TourStatus
from app.models.supplier import SupplierOfferExecutionLink
from app.services.supplier_offer_bot_start_routing import resolve_sup_offer_start_mini_app_routing
from tests.unit.base import FoundationDBTestCase


class SupplierOfferBotStartRoutingB11Tests(FoundationDBTestCase):
    def test_exact_tour_url_when_active_link_open_visible(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(
            supplier,
            lifecycle_status=SupplierOfferLifecycle.PUBLISHED,
            title="Promo Trip",
            sales_mode=TourSalesMode.PER_SEAT,
        )
        departure = datetime.now(UTC) + timedelta(days=14)
        tour = self.create_tour(
            code="B11-LINKED-OK",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=departure,
            return_datetime=departure + timedelta(days=1),
            sales_deadline=departure - timedelta(days=1),
            seats_available=10,
            sales_mode=TourSalesMode.PER_SEAT,
        )
        self.session.add(
            SupplierOfferExecutionLink(
                supplier_offer_id=offer.id,
                tour_id=tour.id,
                link_status="active",
            )
        )
        self.session.commit()
        self.session.refresh(offer)

        r = resolve_sup_offer_start_mini_app_routing(
            self.session,
            offer=offer,
            mini_app_base_url="https://example.com/webapp/",
        )
        self.assertEqual(r.exact_tour_mini_app_url, "https://example.com/webapp/tours/B11-LINKED-OK")
        self.assertEqual(r.linked_tour_code, "B11-LINKED-OK")
        self.assertFalse(r.linked_is_full_bus)

    def test_no_exact_url_when_no_execution_link(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier, lifecycle_status=SupplierOfferLifecycle.PUBLISHED)
        self.session.commit()

        r = resolve_sup_offer_start_mini_app_routing(
            self.session,
            offer=offer,
            mini_app_base_url="https://example.com/",
        )
        self.assertIsNone(r.exact_tour_mini_app_url)

    def test_no_exact_url_when_linked_tour_draft(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(
            supplier,
            lifecycle_status=SupplierOfferLifecycle.PUBLISHED,
            sales_mode=TourSalesMode.PER_SEAT,
        )
        departure = datetime.now(UTC) + timedelta(days=14)
        tour = self.create_tour(
            code="B11-DRAFT",
            status=TourStatus.DRAFT,
            departure_datetime=departure,
            return_datetime=departure + timedelta(days=1),
            sales_mode=TourSalesMode.PER_SEAT,
        )
        self.session.add(
            SupplierOfferExecutionLink(
                supplier_offer_id=offer.id,
                tour_id=tour.id,
                link_status="active",
            )
        )
        self.session.commit()
        self.session.refresh(offer)

        r = resolve_sup_offer_start_mini_app_routing(self.session, offer=offer, mini_app_base_url="https://x.com/")
        self.assertIsNone(r.exact_tour_mini_app_url)

    def test_no_exact_url_when_visibility_window_closed(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier, lifecycle_status=SupplierOfferLifecycle.PUBLISHED)
        departure = datetime.now(UTC) + timedelta(days=14)
        tour = self.create_tour(
            code="B11-SLATE",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=departure,
            return_datetime=departure + timedelta(days=1),
            sales_deadline=datetime.now(UTC) - timedelta(days=1),
            seats_available=5,
            sales_mode=TourSalesMode.PER_SEAT,
        )
        self.session.add(
            SupplierOfferExecutionLink(
                supplier_offer_id=offer.id,
                tour_id=tour.id,
                link_status="active",
            )
        )
        self.session.commit()
        self.session.refresh(offer)

        r = resolve_sup_offer_start_mini_app_routing(self.session, offer=offer, mini_app_base_url="https://x.com/")
        self.assertIsNone(r.exact_tour_mini_app_url)

    def test_full_bus_flag_set_for_linked_full_bus_open(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(
            supplier,
            lifecycle_status=SupplierOfferLifecycle.PUBLISHED,
            sales_mode=TourSalesMode.FULL_BUS,
        )
        departure = datetime.now(UTC) + timedelta(days=14)
        tour = self.create_tour(
            code="B11-FB",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=departure,
            return_datetime=departure + timedelta(days=1),
            sales_deadline=departure - timedelta(days=1),
            sales_mode=TourSalesMode.FULL_BUS,
        )
        self.session.add(
            SupplierOfferExecutionLink(
                supplier_offer_id=offer.id,
                tour_id=tour.id,
                link_status="active",
            )
        )
        self.session.commit()
        self.session.refresh(offer)

        r = resolve_sup_offer_start_mini_app_routing(self.session, offer=offer, mini_app_base_url="https://a.com/")
        self.assertIsNotNone(r.exact_tour_mini_app_url)
        self.assertTrue(r.linked_is_full_bus)
