"""Y2.3: supplier Telegram read-side workspace for own offers/statuses."""

from __future__ import annotations

import asyncio
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.bot.handlers import supplier_offer_workspace
from app.models.enums import (
    BookingStatus,
    CancellationStatus,
    PaymentStatus,
    SupplierOfferLifecycle,
    SupplierOnboardingStatus,
    SupplierServiceComposition,
)
from app.services.supplier_offer_execution_link_service import SupplierOfferExecutionLinkService
from app.services.supplier_offer_service import SupplierOfferService
from tests.unit.base import FoundationDBTestCase


class _SessionLocalBinder:
    def __init__(self, session) -> None:
        self._session = session

    def __call__(self):
        return self._session


def _private_message(*, telegram_user_id: int) -> MagicMock:
    message = MagicMock()
    message.from_user = MagicMock()
    message.from_user.id = telegram_user_id
    message.from_user.username = "supplier_user"
    message.from_user.first_name = "Sup"
    message.from_user.last_name = "User"
    message.from_user.language_code = "en"
    message.chat = MagicMock()
    message.chat.type = "private"
    message.chat.id = 661_001
    message.answer = AsyncMock(return_value=MagicMock(message_id=1))
    return message


class SupplierOfferWorkspaceY23Tests(FoundationDBTestCase):
    @staticmethod
    def _run(coro) -> None:
        asyncio.run(coro)

    def test_approved_supplier_can_view_own_offer_statuses(self) -> None:
        supplier = self.create_supplier(
            code="Y23-W1",
            display_name="Workspace",
            is_active=True,
            primary_telegram_user_id=921_001,
            onboarding_status=SupplierOnboardingStatus.APPROVED,
            onboarding_service_composition=SupplierServiceComposition.TRANSPORT_ONLY,
            onboarding_submitted_at=datetime.now(UTC),
            onboarding_reviewed_at=datetime.now(UTC),
        )
        offer = self.create_supplier_offer(
            supplier,
            title="Workspace Offer",
            description="Desc",
            lifecycle_status=SupplierOfferLifecycle.REJECTED,
            moderation_rejection_reason="Need clearer date",
        )
        self.session.commit()
        self.assertEqual(offer.lifecycle_status, SupplierOfferLifecycle.REJECTED)

        async def body() -> None:
            message = _private_message(telegram_user_id=921_001)
            state = MagicMock()
            state.clear = AsyncMock()
            binder = _SessionLocalBinder(self.session)
            with patch.object(supplier_offer_workspace, "SessionLocal", binder):
                await supplier_offer_workspace.cmd_supplier_offers(message, state)
            all_text = "\n".join(c.args[0].lower() for c in message.answer.call_args_list if c.args)
            self.assertIn("your supplier offers", all_text)
            self.assertIn("rejected", all_text)
            self.assertIn("reason", all_text)
            self.assertIn("declared capacity", all_text)
            self.assertIn("live booking aggregates are not available yet", all_text)

        self._run(body())

    def test_supplier_workspace_shows_only_own_offers(self) -> None:
        supplier_a = self.create_supplier(
            code="Y24-WA",
            display_name="A",
            is_active=True,
            primary_telegram_user_id=921_011,
            onboarding_status=SupplierOnboardingStatus.APPROVED,
            onboarding_service_composition=SupplierServiceComposition.TRANSPORT_ONLY,
            onboarding_submitted_at=datetime.now(UTC),
            onboarding_reviewed_at=datetime.now(UTC),
        )
        supplier_b = self.create_supplier(
            code="Y24-WB",
            display_name="B",
            is_active=True,
            primary_telegram_user_id=921_012,
            onboarding_status=SupplierOnboardingStatus.APPROVED,
            onboarding_service_composition=SupplierServiceComposition.TRANSPORT_ONLY,
            onboarding_submitted_at=datetime.now(UTC),
            onboarding_reviewed_at=datetime.now(UTC),
        )
        self.create_supplier_offer(supplier_a, title="A Offer", description="A Desc")
        self.create_supplier_offer(supplier_b, title="B Secret Offer", description="B Desc")
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=921_011)
            state = MagicMock()
            state.clear = AsyncMock()
            binder = _SessionLocalBinder(self.session)
            with patch.object(supplier_offer_workspace, "SessionLocal", binder):
                await supplier_offer_workspace.cmd_supplier_offers(message, state)
            all_text = "\n".join(c.args[0] for c in message.answer.call_args_list if c.args)
            self.assertIn("A Offer", all_text)
            self.assertNotIn("B Secret Offer", all_text)

        self._run(body())

    def test_unpublished_offer_does_not_claim_live_stats(self) -> None:
        supplier = self.create_supplier(
            code="Y24-WU",
            display_name="Unpub",
            is_active=True,
            primary_telegram_user_id=921_013,
            onboarding_status=SupplierOnboardingStatus.APPROVED,
            onboarding_service_composition=SupplierServiceComposition.TRANSPORT_ONLY,
            onboarding_submitted_at=datetime.now(UTC),
            onboarding_reviewed_at=datetime.now(UTC),
        )
        self.create_supplier_offer(
            supplier,
            title="Draft Offer",
            description="Desc",
            lifecycle_status=SupplierOfferLifecycle.DRAFT,
            seats_total=44,
        )
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=921_013)
            state = MagicMock()
            state.clear = AsyncMock()
            binder = _SessionLocalBinder(self.session)
            with patch.object(supplier_offer_workspace, "SessionLocal", binder):
                await supplier_offer_workspace.cmd_supplier_offers(message, state)
            all_text = "\n".join(c.args[0].lower() for c in message.answer.call_args_list if c.args)
            self.assertIn("publication: not active", all_text)
            self.assertIn("pre-publication stage", all_text)
            self.assertIn("declared capacity: 44 seats", all_text)
            self.assertIn("live booking aggregates are not available yet", all_text)
            self.assertNotIn("alert:", all_text)

        self._run(body())

    def test_published_offer_exposes_safe_aggregate_signals_only(self) -> None:
        supplier = self.create_supplier(
            code="Y24-WP",
            display_name="Pub",
            is_active=True,
            primary_telegram_user_id=921_014,
            onboarding_status=SupplierOnboardingStatus.APPROVED,
            onboarding_service_composition=SupplierServiceComposition.TRANSPORT_ONLY,
            onboarding_submitted_at=datetime.now(UTC),
            onboarding_reviewed_at=datetime.now(UTC),
        )
        self.create_supplier_offer(
            supplier,
            title="Published Offer",
            description="Desc",
            lifecycle_status=SupplierOfferLifecycle.PUBLISHED,
            seats_total=50,
        )
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=921_014)
            state = MagicMock()
            state.clear = AsyncMock()
            binder = _SessionLocalBinder(self.session)
            with patch.object(supplier_offer_workspace, "SessionLocal", binder):
                await supplier_offer_workspace.cmd_supplier_offers(message, state)
            all_text = "\n".join(c.args[0].lower() for c in message.answer.call_args_list if c.args)
            self.assertIn("publication: active", all_text)
            self.assertIn("declared capacity: 50 seats", all_text)
            self.assertIn("waiting linked execution metrics", all_text)
            self.assertNotIn("customer", all_text)
            self.assertNotIn("phone", all_text)
            self.assertNotIn("telegram", all_text)
            self.assertNotIn("payment row", all_text)

        self._run(body())

    def test_published_linked_offer_exposes_booking_aggregates_only(self) -> None:
        supplier = self.create_supplier(
            code="Y27-WL",
            display_name="Linked",
            is_active=True,
            primary_telegram_user_id=921_017,
            onboarding_status=SupplierOnboardingStatus.APPROVED,
            onboarding_service_composition=SupplierServiceComposition.TRANSPORT_ONLY,
            onboarding_submitted_at=datetime.now(UTC),
            onboarding_reviewed_at=datetime.now(UTC),
        )
        offer = self.create_supplier_offer(
            supplier,
            title="Linked Offer",
            description="Desc",
            lifecycle_status=SupplierOfferLifecycle.PUBLISHED,
            seats_total=999,  # should be ignored in favor of linked tour truth
        )
        tour = self.create_tour(seats_total=40, seats_available=32)
        point = self.create_boarding_point(tour)
        user_a = self.create_user()
        self.create_order(
            user_a,
            tour,
            point,
            seats_count=3,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime.now(UTC) + timedelta(hours=2),
        )
        user_b = self.create_user()
        self.create_order(
            user_b,
            tour,
            point,
            seats_count=5,
            booking_status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            cancellation_status=CancellationStatus.ACTIVE,
        )
        SupplierOfferExecutionLinkService().link_offer_to_tour(self.session, offer_id=offer.id, tour_id=tour.id)
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=921_017)
            state = MagicMock()
            state.clear = AsyncMock()
            binder = _SessionLocalBinder(self.session)
            with patch.object(supplier_offer_workspace, "SessionLocal", binder):
                await supplier_offer_workspace.cmd_supplier_offers(message, state)
            all_text = "\n".join(c.args[0].lower() for c in message.answer.call_args_list if c.args)
            self.assertIn("declared capacity: 40 seats", all_text)
            self.assertIn("occupied capacity: 8 seats", all_text)
            self.assertIn("remaining capacity: 32 seats", all_text)
            self.assertIn("active reserved hold seats: 3", all_text)
            self.assertIn("confirmed paid seats: 5", all_text)
            self.assertIn("sold out: no", all_text)
            self.assertNotIn("live booking aggregates are not available yet", all_text)
            self.assertNotIn("customer", all_text)
            self.assertNotIn("phone", all_text)
            self.assertNotIn("telegram", all_text)

        self._run(body())

    def test_published_offer_near_departure_shows_narrow_alert(self) -> None:
        supplier = self.create_supplier(
            code="Y25-AL1",
            display_name="Alerts",
            is_active=True,
            primary_telegram_user_id=921_015,
            onboarding_status=SupplierOnboardingStatus.APPROVED,
            onboarding_service_composition=SupplierServiceComposition.TRANSPORT_ONLY,
            onboarding_submitted_at=datetime.now(UTC),
            onboarding_reviewed_at=datetime.now(UTC),
        )
        dep = datetime.now(UTC) + timedelta(hours=8)
        self.create_supplier_offer(
            supplier,
            title="Soon Offer",
            description="Desc",
            lifecycle_status=SupplierOfferLifecycle.PUBLISHED,
            departure_datetime=dep,
            return_datetime=dep + timedelta(hours=12),
        )
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=921_015)
            state = MagicMock()
            state.clear = AsyncMock()
            binder = _SessionLocalBinder(self.session)
            with patch.object(supplier_offer_workspace, "SessionLocal", binder):
                await supplier_offer_workspace.cmd_supplier_offers(message, state)
            all_text = "\n".join(c.args[0].lower() for c in message.answer.call_args_list if c.args)
            self.assertIn("alert:", all_text)
            self.assertIn("departure is in less than 24 hours", all_text)

        self._run(body())

    def test_retracted_offer_shows_retracted_alert(self) -> None:
        supplier = self.create_supplier(
            code="Y25-AL2",
            display_name="Retracted",
            is_active=True,
            primary_telegram_user_id=921_016,
            onboarding_status=SupplierOnboardingStatus.APPROVED,
            onboarding_service_composition=SupplierServiceComposition.TRANSPORT_ONLY,
            onboarding_submitted_at=datetime.now(UTC),
            onboarding_reviewed_at=datetime.now(UTC),
        )
        self.create_supplier_offer(
            supplier,
            title="Retracted Offer",
            description="Desc",
            lifecycle_status=SupplierOfferLifecycle.APPROVED,
            published_at=datetime.now(UTC) - timedelta(days=1),
        )
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=921_016)
            state = MagicMock()
            state.clear = AsyncMock()
            binder = _SessionLocalBinder(self.session)
            with patch.object(supplier_offer_workspace, "SessionLocal", binder):
                await supplier_offer_workspace.cmd_supplier_offers(message, state)
            all_text = "\n".join(c.args[0].lower() for c in message.answer.call_args_list if c.args)
            self.assertIn("alert:", all_text)
            self.assertIn("publication was retracted", all_text)

        self._run(body())

    def test_pending_supplier_is_gated_from_workspace(self) -> None:
        self.create_supplier(
            code="Y23-W2",
            display_name="Pending",
            is_active=False,
            primary_telegram_user_id=921_002,
            onboarding_status=SupplierOnboardingStatus.PENDING_REVIEW,
        )
        self.session.commit()

        async def body() -> None:
            message = _private_message(telegram_user_id=921_002)
            state = MagicMock()
            state.clear = AsyncMock()
            binder = _SessionLocalBinder(self.session)
            with patch.object(supplier_offer_workspace, "SessionLocal", binder):
                await supplier_offer_workspace.cmd_supplier_offers(message, state)
            text = message.answer.call_args[0][0].lower()
            self.assertIn("pending", text)

        self._run(body())


if __name__ == "__main__":
    unittest.main()
