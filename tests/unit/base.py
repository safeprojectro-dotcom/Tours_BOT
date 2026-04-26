from __future__ import annotations

import itertools
import unittest
from datetime import UTC, datetime, timedelta, time
from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.content_item import ContentItem
from app.api.supplier_admin_auth import hash_supplier_api_token
from app.models.enums import (
    BookingStatus,
    PaymentStatus,
    SupplierOfferLifecycle,
    SupplierOfferPackagingStatus,
    SupplierOfferPaymentMode,
    SupplierServiceComposition,
    TourSalesMode,
    TourStatus,
)
from app.models.handoff import Handoff
from app.models.knowledge_base import KnowledgeBaseEntry
from app.models.message import Message
from app.models.order import Order
from app.models.supplier import Supplier, SupplierApiCredential, SupplierOffer
from app.models.payment import Payment
from app.models.tour import BoardingPoint, Tour, TourTranslation
from app.models.user import User
from app.models.waitlist import WaitlistEntry


class FoundationDBTestCase(unittest.TestCase):
    _counter = itertools.count(1)

    @classmethod
    def tearDownClass(cls) -> None:
        engine.dispose()
        super().tearDownClass()

    def setUp(self) -> None:
        self.connection = engine.connect()
        self.transaction = self.connection.begin()
        self.session = Session(bind=self.connection)

    def tearDown(self) -> None:
        self.session.close()
        self.transaction.rollback()
        self.connection.close()

    def _next(self) -> int:
        return next(self._counter)

    def create_user(self, **overrides) -> User:
        index = self._next()
        user = User(
            telegram_user_id=overrides.pop("telegram_user_id", 10_000 + index),
            username=overrides.pop("username", f"user_{index}"),
            first_name=overrides.pop("first_name", "Test"),
            last_name=overrides.pop("last_name", "User"),
            phone=overrides.pop("phone", f"+100000{index:04d}"),
            preferred_language=overrides.pop("preferred_language", "en"),
            home_city=overrides.pop("home_city", "Timisoara"),
            source_channel=overrides.pop("source_channel", "private"),
            **overrides,
        )
        self.session.add(user)
        self.session.flush()
        return user

    def create_tour(self, **overrides) -> Tour:
        index = self._next()
        departure = overrides.pop("departure_datetime", datetime.now(UTC) + timedelta(days=7))
        tour = Tour(
            code=overrides.pop("code", f"TOUR-{index}"),
            title_default=overrides.pop("title_default", f"Tour {index}"),
            short_description_default=overrides.pop("short_description_default", "Default short description"),
            full_description_default=overrides.pop("full_description_default", "Default full description"),
            duration_days=overrides.pop("duration_days", 2),
            departure_datetime=departure,
            return_datetime=overrides.pop("return_datetime", departure + timedelta(days=2)),
            base_price=overrides.pop("base_price", Decimal("99.99")),
            currency=overrides.pop("currency", "EUR"),
            seats_total=overrides.pop("seats_total", 40),
            seats_available=overrides.pop("seats_available", 12),
            sales_deadline=overrides.pop("sales_deadline", departure - timedelta(days=1)),
            status=overrides.pop("status", TourStatus.OPEN_FOR_SALE),
            guaranteed_flag=overrides.pop("guaranteed_flag", False),
            **overrides,
        )
        self.session.add(tour)
        self.session.flush()
        return tour

    def create_translation(self, tour: Tour, **overrides) -> TourTranslation:
        translation = TourTranslation(
            tour_id=tour.id,
            language_code=overrides.pop("language_code", "ro"),
            title=overrides.pop("title", "Titlu tradus"),
            short_description=overrides.pop("short_description", "Descriere scurta"),
            full_description=overrides.pop("full_description", "Descriere completa"),
            program_text=overrides.pop("program_text", "Program"),
            included_text=overrides.pop("included_text", "Inclus"),
            excluded_text=overrides.pop("excluded_text", "Exclus"),
            **overrides,
        )
        self.session.add(translation)
        self.session.flush()
        return translation

    def create_boarding_point(self, tour: Tour, **overrides) -> BoardingPoint:
        index = self._next()
        point = BoardingPoint(
            tour_id=tour.id,
            city=overrides.pop("city", "Timisoara"),
            address=overrides.pop("address", f"Address {index}"),
            time=overrides.pop("time", time(hour=6, minute=index % 50)),
            notes=overrides.pop("notes", "Main boarding point"),
            **overrides,
        )
        self.session.add(point)
        self.session.flush()
        return point

    def create_order(self, user: User, tour: Tour, boarding_point: BoardingPoint, **overrides) -> Order:
        order = Order(
            user_id=user.id,
            tour_id=tour.id,
            boarding_point_id=boarding_point.id,
            seats_count=overrides.pop("seats_count", 2),
            booking_status=overrides.pop("booking_status", BookingStatus.NEW),
            payment_status=overrides.pop("payment_status", PaymentStatus.UNPAID),
            total_amount=overrides.pop("total_amount", Decimal("199.98")),
            currency=overrides.pop("currency", "EUR"),
            source_channel=overrides.pop("source_channel", "private"),
            **overrides,
        )
        self.session.add(order)
        self.session.flush()
        return order

    def create_supplier(self, **overrides) -> Supplier:
        index = self._next()
        supplier = Supplier(
            code=overrides.pop("code", f"SUP-{index}"),
            display_name=overrides.pop("display_name", f"Supplier {index}"),
            is_active=overrides.pop("is_active", True),
            **overrides,
        )
        self.session.add(supplier)
        self.session.flush()
        return supplier

    def create_supplier_credential(self, supplier: Supplier, plaintext_token: str, **overrides) -> SupplierApiCredential:
        cred = SupplierApiCredential(
            supplier_id=supplier.id,
            token_hash=hash_supplier_api_token(plaintext_token),
            label=overrides.pop("label", None),
            created_at=overrides.pop("created_at", datetime.now(UTC)),
            revoked_at=overrides.pop("revoked_at", None),
            **overrides,
        )
        self.session.add(cred)
        self.session.flush()
        return cred

    def create_supplier_offer(self, supplier: Supplier, **overrides) -> SupplierOffer:
        index = self._next()
        departure = overrides.pop("departure_datetime", datetime.now(UTC) + timedelta(days=7))
        ret = overrides.pop("return_datetime", departure + timedelta(days=1))
        offer = SupplierOffer(
            supplier_id=supplier.id,
            supplier_reference=overrides.pop("supplier_reference", None),
            title=overrides.pop("title", f"Offer {index}"),
            description=overrides.pop("description", "Description"),
            program_text=overrides.pop("program_text", "Program"),
            departure_datetime=departure,
            return_datetime=ret,
            transport_notes=overrides.pop("transport_notes", "Bus details"),
            vehicle_label=overrides.pop("vehicle_label", "Coach 50"),
            seats_total=overrides.pop("seats_total", 50),
            base_price=overrides.pop("base_price", Decimal("120.00")),
            currency=overrides.pop("currency", "EUR"),
            service_composition=overrides.pop("service_composition", SupplierServiceComposition.TRANSPORT_ONLY),
            sales_mode=overrides.pop("sales_mode", TourSalesMode.PER_SEAT),
            payment_mode=overrides.pop("payment_mode", SupplierOfferPaymentMode.PLATFORM_CHECKOUT),
            lifecycle_status=overrides.pop("lifecycle_status", SupplierOfferLifecycle.DRAFT),
            packaging_status=overrides.pop("packaging_status", SupplierOfferPackagingStatus.NONE),
            **overrides,
        )
        self.session.add(offer)
        self.session.flush()
        return offer

    def create_payment(self, order: Order, **overrides) -> Payment:
        index = self._next()
        payment = Payment(
            order_id=order.id,
            provider=overrides.pop("provider", "mockpay"),
            external_payment_id=overrides.pop("external_payment_id", f"pay-{index}"),
            amount=overrides.pop("amount", order.total_amount),
            currency=overrides.pop("currency", order.currency),
            status=overrides.pop("status", PaymentStatus.UNPAID),
            raw_payload=overrides.pop("raw_payload", {"payment": index}),
            **overrides,
        )
        self.session.add(payment)
        self.session.flush()
        return payment

    def create_knowledge_base_entry(self, **overrides) -> KnowledgeBaseEntry:
        index = self._next()
        entry = KnowledgeBaseEntry(
            category=overrides.pop("category", "faq"),
            language_code=overrides.pop("language_code", "en"),
            title=overrides.pop("title", f"KB {index}"),
            content=overrides.pop("content", "Knowledge base content"),
            is_active=overrides.pop("is_active", True),
            **overrides,
        )
        self.session.add(entry)
        self.session.flush()
        return entry
