"""S1C-2: deliver one supplier_notification_outbox row by id (explicit admin/manual entry only).

Uses the same Aiogram Telegram private-chat adapter stack as ``NotificationDeliveryService``.
No scheduler, no hooks, no Layer A mutation.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.supplier import Supplier
from app.models.supplier_notification_outbox import SupplierNotificationOutbox
from app.repositories.supplier_notification_outbox import SupplierNotificationOutboxRepository
from app.schemas.supplier_notification_outbox import (
    SupplierNotificationOutboxDeliveryResultRead,
    SupplierNotificationOutboxRead,
)
from app.services.telegram_private_delivery import (
    AiogramTelegramPrivateDeliveryAdapter,
    TelegramPrivateDeliveryAdapter,
)


class SupplierNotificationOutboxNotFoundError(Exception):
    """Outbox id does not exist."""


class SupplierNotificationOutboxDeliveryStateConflictError(Exception):
    """Row is not in a deliverable lifecycle state."""

    def __init__(self, *, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class SupplierNotificationOutboxDeliveryService:
    """Process at most one ``pending_dispatch`` outbox intent per call."""

    def __init__(
        self,
        *,
        repository: SupplierNotificationOutboxRepository | None = None,
        telegram_private_adapter: TelegramPrivateDeliveryAdapter | None = None,
    ) -> None:
        self._repo = repository or SupplierNotificationOutboxRepository()
        self._telegram_private_adapter = telegram_private_adapter
        self._owns_telegram_private_adapter = telegram_private_adapter is None

    async def close(self) -> None:
        if self._telegram_private_adapter is None or not self._owns_telegram_private_adapter:
            return
        await self._telegram_private_adapter.close()

    def _row(self, session: Session, *, outbox_id: int) -> SupplierNotificationOutbox | None:
        return session.get(SupplierNotificationOutbox, outbox_id)

    @staticmethod
    def _supplier_contact_drift_reason(*, row: SupplierNotificationOutbox, session: Session) -> str | None:
        tg = row.telegram_user_id
        if tg is None:
            return "supplier_notification_outbox_missing_telegram_user_id"

        if row.supplier_id is None:
            return None

        supplier = session.get(Supplier, row.supplier_id)
        if supplier is None:
            return "supplier_row_missing_contact_drift_gate"

        current = supplier.primary_telegram_user_id
        if current is None:
            return "supplier_primary_telegram_cleared_contact_drift_gate"

        if int(current) != int(tg):
            return "supplier_primary_telegram_changed_contact_drift_gate"

        return None

    @staticmethod
    def _render_delivery_text(row: SupplierNotificationOutbox) -> str:
        return f"{row.title}\n\n{row.message}"

    @staticmethod
    def _explain_non_pending_conflict(dispatch_status: str) -> str:
        return {
            "skipped_no_target": "supplier_notification_skipped_no_target_non_deliverable",
            "delivery_in_progress": "supplier_notification_delivery_in_progress_stale_retry_later_or_ops_recover",
            "send_failed": "supplier_notification_send_failed_retry_requires_new_intent_future_slice",
            "pending_dispatch": "supplier_notification_claim_race_retry",
        }.get(dispatch_status, f"supplier_notification_unexpected_dispatch_status:{dispatch_status}")

    async def deliver_one_by_id(self, session: Session, *, outbox_id: int) -> SupplierNotificationOutboxDeliveryResultRead:
        if self._row(session, outbox_id=outbox_id) is None:
            raise SupplierNotificationOutboxNotFoundError(str(outbox_id))

        claimed = self._repo.try_claim_pending_for_delivery(session, outbox_id=outbox_id)

        row = self._row(session, outbox_id=outbox_id)
        if row is None:
            raise SupplierNotificationOutboxNotFoundError(str(outbox_id))

        if not claimed:
            if row.dispatch_status == "delivered":
                return SupplierNotificationOutboxDeliveryResultRead(
                    outcome="already_delivered",
                    supplier_notification_outbox=SupplierNotificationOutboxRead.model_validate(row),
                    error_detail=None,
                )
            raise SupplierNotificationOutboxDeliveryStateConflictError(detail=self._explain_non_pending_conflict(row.dispatch_status))

        drift_reason = self._supplier_contact_drift_reason(row=row, session=session)
        if drift_reason is not None:
            self._repo.finalize_send_failed_from_in_progress(
                session,
                outbox_id=outbox_id,
                error_message=drift_reason,
            )
            session.flush()
            row_ref = self._row(session, outbox_id=outbox_id)
            return SupplierNotificationOutboxDeliveryResultRead(
                outcome="send_failed",
                supplier_notification_outbox=SupplierNotificationOutboxRead.model_validate(row_ref),
                error_detail=drift_reason,
            )

        adapter = self._get_telegram_private_adapter()
        body = self._render_delivery_text(row)

        try:
            provider_message_id = await adapter.send_message(
                telegram_user_id=int(row.telegram_user_id),
                text=body,
            )
        except Exception as exc:
            self._repo.finalize_send_failed_from_in_progress(
                session,
                outbox_id=outbox_id,
                error_message=str(exc),
            )
            session.flush()
            failed = self._row(session, outbox_id=outbox_id)
            return SupplierNotificationOutboxDeliveryResultRead(
                outcome="send_failed",
                supplier_notification_outbox=SupplierNotificationOutboxRead.model_validate(failed),
                error_detail=str(exc),
            )

        self._repo.finalize_delivered_from_in_progress(
            session,
            outbox_id=outbox_id,
            telegram_message_id=provider_message_id or "",
        )
        session.flush()
        refreshed = self._row(session, outbox_id=outbox_id)

        if refreshed is None:
            raise RuntimeError("supplier_notification_outbox_missing_after_finalize_delivered")
        if refreshed.dispatch_status != "delivered":
            raise RuntimeError("supplier_notification_outbox_expected_delivered_after_telegram_send")

        return SupplierNotificationOutboxDeliveryResultRead(
            outcome="delivered",
            supplier_notification_outbox=SupplierNotificationOutboxRead.model_validate(refreshed),
            error_detail=None,
        )

    def _get_telegram_private_adapter(self) -> TelegramPrivateDeliveryAdapter:
        if self._telegram_private_adapter is None:
            self._telegram_private_adapter = AiogramTelegramPrivateDeliveryAdapter.from_settings()
        return self._telegram_private_adapter

