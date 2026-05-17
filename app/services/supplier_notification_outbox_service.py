"""S1C-1: build safe supplier-notification payloads and persist outbox rows (no Telegram send)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.supplier import SupplierOffer
from app.repositories.supplier_notification_outbox import SupplierNotificationOutboxRepository
from app.schemas.supplier_notification_outbox import SupplierNotificationOutboxRead
from app.services.admin_supplier_telegram_contact_resolution_service import (
    AdminSupplierTelegramContactResolutionService,
)


class SupplierNotificationOutboxService:
    """Enqueue supplier notification intents — Layer A read-only for payload sourcing."""

    _CHANNEL = "telegram_dm"

    def __init__(
        self,
        *,
        repository: SupplierNotificationOutboxRepository | None = None,
        contact_resolver: AdminSupplierTelegramContactResolutionService | None = None,
    ) -> None:
        self._repo = repository or SupplierNotificationOutboxRepository()
        self._contact = contact_resolver or AdminSupplierTelegramContactResolutionService()

    @staticmethod
    def build_supplier_offer_published_payload_metadata(*, offer: SupplierOffer) -> dict:
        """Facts/marketing title only — no customer PII."""
        return {
            "supplier_offer_id": offer.id,
            "offer_title": offer.title[:512],
            "lifecycle_status": offer.lifecycle_status.value
            if hasattr(offer.lifecycle_status, "value")
            else str(offer.lifecycle_status),
        }

    @staticmethod
    def build_supplier_order_created_payload_metadata(*, order: Order) -> dict:
        """Operational order snapshot — no user/contact fields."""
        return {
            "order_id": order.id,
            "tour_id": order.tour_id,
            "seats_count": order.seats_count,
            "booking_status": order.booking_status.value
            if hasattr(order.booking_status, "value")
            else str(order.booking_status),
            "payment_status": order.payment_status.value
            if hasattr(order.payment_status, "value")
            else str(order.payment_status),
        }

    def enqueue_supplier_offer_published(
        self,
        session: Session,
        *,
        offer_id: int,
        idempotency_key: str | None = None,
        actor_surface: str | None = "s1c1_supplier_offer_published",
    ) -> SupplierNotificationOutboxRead | None:
        offer = session.get(SupplierOffer, offer_id)
        if offer is None:
            return None

        key = idempotency_key or f"s1c1:supplier_offer_published:supplier_offer:{offer_id}"
        existing = self._repo.get_by_idempotency_key(session, idempotency_key=key)
        if existing is not None:
            return SupplierNotificationOutboxRead.model_validate(existing)

        resolution = self._contact.resolve_for_supplier_offer(session, offer_id=offer_id)
        if resolution is None:
            return None
        warnings = list(resolution.readiness_warnings)
        payload = self.build_supplier_offer_published_payload_metadata(offer=offer)

        dispatch_status = "skipped_no_target"
        telegram_user_id = None
        if resolution.resolution_status == "resolved_with_contact" and resolution.telegram_contact_configured:
            dispatch_status = "pending_dispatch"
            telegram_user_id = resolution.primary_telegram_user_id

        title = "Supplier showcase notification"
        message = (
            f"Queued supplier_offer_published intent for supplier_offer_id={offer.id}. "
            f"dispatch_status={dispatch_status}."
        )

        row = self._repo.create(
            session,
            data={
                "idempotency_key": key,
                "event_type": "supplier_offer_published",
                "channel": self._CHANNEL,
                "supplier_id": resolution.supplier_id,
                "supplier_offer_id": offer.id,
                "tour_id": None,
                "order_id": None,
                "telegram_user_id": telegram_user_id,
                "contact_resolution_status": resolution.resolution_status,
                "title": title[:255],
                "message": message,
                "payload_metadata": payload,
                "readiness_warnings": warnings or None,
                "dispatch_status": dispatch_status,
                "actor_surface": actor_surface,
            },
        )
        return SupplierNotificationOutboxRead.model_validate(row)

    def enqueue_supplier_order_created(
        self,
        session: Session,
        *,
        order_id: int,
        idempotency_key: str | None = None,
        actor_surface: str | None = "s1c1_supplier_order_created",
    ) -> SupplierNotificationOutboxRead | None:
        order = session.get(Order, order_id)
        if order is None:
            return None

        key = idempotency_key or f"s1c1:supplier_order_created:order:{order_id}"
        existing = self._repo.get_by_idempotency_key(session, idempotency_key=key)
        if existing is not None:
            return SupplierNotificationOutboxRead.model_validate(existing)

        resolution = self._contact.resolve_for_order(session, order_id=order_id)
        if resolution is None:
            return None
        warnings = list(resolution.readiness_warnings)
        payload = self.build_supplier_order_created_payload_metadata(order=order)

        dispatch_status = "skipped_no_target"
        telegram_user_id = None
        if resolution.resolution_status == "resolved_with_contact" and resolution.telegram_contact_configured:
            dispatch_status = "pending_dispatch"
            telegram_user_id = resolution.primary_telegram_user_id

        title = "Booking activity notification"
        message = (
            f"Queued supplier_order_created intent for order_id={order.id}. dispatch_status={dispatch_status}."
        )

        row = self._repo.create(
            session,
            data={
                "idempotency_key": key,
                "event_type": "supplier_order_created",
                "channel": self._CHANNEL,
                "supplier_id": resolution.supplier_id,
                "supplier_offer_id": None,
                "tour_id": order.tour_id,
                "order_id": order.id,
                "telegram_user_id": telegram_user_id,
                "contact_resolution_status": resolution.resolution_status,
                "title": title[:255],
                "message": message,
                "payload_metadata": payload,
                "readiness_warnings": warnings or None,
                "dispatch_status": dispatch_status,
                "actor_surface": actor_surface,
            },
        )
        return SupplierNotificationOutboxRead.model_validate(row)
