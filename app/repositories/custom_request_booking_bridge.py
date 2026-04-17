"""Persistence for Track 5b.1 RFQ → Layer A booking bridge records."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.custom_request_booking_bridge import CustomRequestBookingBridge
from app.models.enums import CustomRequestBookingBridgeStatus


_ACTIVE_BRIDGE_STATUSES: frozenset[CustomRequestBookingBridgeStatus] = frozenset(
    {
        CustomRequestBookingBridgeStatus.PENDING_VALIDATION,
        CustomRequestBookingBridgeStatus.READY,
        CustomRequestBookingBridgeStatus.LINKED_TOUR,
        CustomRequestBookingBridgeStatus.CUSTOMER_NOTIFIED,
    },
)


class CustomRequestBookingBridgeRepository:
    def get_active_for_request(
        self,
        session: Session,
        *,
        request_id: int,
    ) -> CustomRequestBookingBridge | None:
        stmt = (
            select(CustomRequestBookingBridge)
            .where(
                CustomRequestBookingBridge.request_id == request_id,
                CustomRequestBookingBridge.bridge_status.in_(_ACTIVE_BRIDGE_STATUSES),
            )
            .order_by(CustomRequestBookingBridge.id.desc())
            .limit(1)
        )
        return session.scalars(stmt).first()

    def get_latest_for_request(
        self,
        session: Session,
        *,
        request_id: int,
    ) -> CustomRequestBookingBridge | None:
        stmt = (
            select(CustomRequestBookingBridge)
            .where(CustomRequestBookingBridge.request_id == request_id)
            .order_by(CustomRequestBookingBridge.id.desc())
            .limit(1)
        )
        return session.scalars(stmt).first()

    def create(self, session: Session, *, row: CustomRequestBookingBridge) -> CustomRequestBookingBridge:
        session.add(row)
        session.flush()
        session.refresh(row)
        return row
