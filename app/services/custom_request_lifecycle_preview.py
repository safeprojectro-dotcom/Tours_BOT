"""W2: read-side Mini App preview of Mode 3 lifecycle copy (uses W1 preparation; no dispatch)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from sqlalchemy.orm import Session

from app.models.enums import CustomMarketplaceRequestStatus, CustomRequestBookingBridgeStatus
from app.repositories.custom_marketplace import CustomMarketplaceRequestRepository
from app.schemas.custom_request_notification import (
    AdminPreparedCustomRequestLifecycleMessageRead,
    CustomRequestNotificationEventType,
    MiniAppCustomRequestActivityPreviewRead,
)
from app.services.custom_request_notification_preparation import CustomRequestNotificationPreparationService
from app.services.user_profile import UserProfileService

_TERMINAL: frozenset[CustomMarketplaceRequestStatus] = frozenset(
    {
        CustomMarketplaceRequestStatus.CLOSED_ASSISTED,
        CustomMarketplaceRequestStatus.CLOSED_EXTERNAL,
        CustomMarketplaceRequestStatus.CANCELLED,
        CustomMarketplaceRequestStatus.FULFILLED,
    },
)

_FOLLOWUP_BRIDGE_STATUSES: frozenset[CustomRequestBookingBridgeStatus] = frozenset(
    {
        CustomRequestBookingBridgeStatus.READY,
        CustomRequestBookingBridgeStatus.LINKED_TOUR,
        CustomRequestBookingBridgeStatus.CUSTOMER_NOTIFIED,
    },
)


def _resolve_event_for_list(
    status: CustomMarketplaceRequestStatus,
) -> tuple[CustomRequestNotificationEventType, bool | None]:
    if status == CustomMarketplaceRequestStatus.OPEN:
        return CustomRequestNotificationEventType.REQUEST_RECORDED, None
    if status == CustomMarketplaceRequestStatus.UNDER_REVIEW:
        return CustomRequestNotificationEventType.REQUEST_UNDER_REVIEW, None
    if status in _TERMINAL:
        return CustomRequestNotificationEventType.REQUEST_CLOSED, None
    if status == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        return CustomRequestNotificationEventType.REQUEST_SELECTION_RECORDED, None
    return CustomRequestNotificationEventType.REQUEST_RECORDED, None


def _resolve_event_for_detail(
    status: CustomMarketplaceRequestStatus,
    bridge_status: CustomRequestBookingBridgeStatus | None,
) -> tuple[CustomRequestNotificationEventType, bool | None]:
    if status == CustomMarketplaceRequestStatus.OPEN:
        return CustomRequestNotificationEventType.REQUEST_RECORDED, None
    if status == CustomMarketplaceRequestStatus.UNDER_REVIEW:
        return CustomRequestNotificationEventType.REQUEST_UNDER_REVIEW, None
    if status in _TERMINAL:
        return CustomRequestNotificationEventType.REQUEST_CLOSED, None
    if status == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        if bridge_status in _FOLLOWUP_BRIDGE_STATUSES:
            return CustomRequestNotificationEventType.REQUEST_APP_FOLLOWUP_MAY_EXIST, True
        return CustomRequestNotificationEventType.REQUEST_SELECTION_RECORDED, None
    return CustomRequestNotificationEventType.REQUEST_RECORDED, None


class CustomRequestLifecyclePreviewService:
    """Builds customer-visible preview payloads; all copy comes from W1 templates."""

    def __init__(
        self,
        *,
        request_repository: CustomMarketplaceRequestRepository | None = None,
        preparation: CustomRequestNotificationPreparationService | None = None,
        user_profile_service: UserProfileService | None = None,
    ) -> None:
        self._requests = request_repository or CustomMarketplaceRequestRepository()
        self._prep = preparation or CustomRequestNotificationPreparationService()
        self._users = user_profile_service or UserProfileService()

    def list_activity_title(
        self,
        session: Session,
        *,
        request_id: int,
        language_code: str | None,
    ) -> str | None:
        row = self._requests.get(session, request_id=request_id)
        if row is None:
            return None
        event_type, flag = _resolve_event_for_list(row.status)
        prepared = self._prep.prepare(
            session,
            request_id=request_id,
            event_type=event_type,
            language_code=language_code,
            app_next_step_maybe_available=flag,
        )
        return prepared.title if prepared is not None else None

    def detail_activity_preview(
        self,
        session: Session,
        *,
        request_id: int,
        bridge_status: CustomRequestBookingBridgeStatus | None,
        language_code: str | None,
    ) -> MiniAppCustomRequestActivityPreviewRead | None:
        row = self._requests.get(session, request_id=request_id)
        if row is None:
            return None
        user = self._users.get_user(session, user_id=row.user_id)
        if user is None:
            return None
        event_type, flag = _resolve_event_for_detail(row.status, bridge_status)
        prepared = self._prep.prepare(
            session,
            request_id=request_id,
            event_type=event_type,
            language_code=language_code,
            app_next_step_maybe_available=flag,
        )
        if prepared is None:
            return None
        disclaimer = self._prep.preview_disclaimer_text(
            language_code=language_code,
            user_preferred_language=user.preferred_language,
        )
        return MiniAppCustomRequestActivityPreviewRead(
            title=prepared.title,
            message=prepared.message,
            notification_event=prepared.event_type.value,
            in_app_preview_only=True,
            preview_disclaimer=disclaimer,
        )

    def admin_prepared_lifecycle_message(
        self,
        session: Session,
        *,
        request_id: int,
        bridge_status: CustomRequestBookingBridgeStatus | None,
        language_code: str | None,
    ) -> AdminPreparedCustomRequestLifecycleMessageRead | None:
        """W3: same W1/W2 resolution as customer detail preview; explicit not-sent semantics for ops/admin."""
        row = self._requests.get(session, request_id=request_id)
        if row is None:
            return None
        user = self._users.get_user(session, user_id=row.user_id)
        if user is None:
            return None
        event_type, flag = _resolve_event_for_detail(row.status, bridge_status)
        prepared = self._prep.prepare(
            session,
            request_id=request_id,
            event_type=event_type,
            language_code=language_code,
            app_next_step_maybe_available=flag,
        )
        if prepared is None:
            return None
        internal_disc = self._prep.admin_prepared_internal_disclaimer_text(
            language_code=language_code,
            user_preferred_language=user.preferred_language,
        )
        customer_disc = self._prep.preview_disclaimer_text(
            language_code=language_code,
            user_preferred_language=user.preferred_language,
        )
        meta: dict[str, Any] = deepcopy(prepared.metadata)
        meta["w3_resolved_notification_event"] = prepared.event_type.value
        meta["w3_booking_bridge_status_used_for_resolution"] = (
            bridge_status.value if bridge_status is not None else None
        )
        return AdminPreparedCustomRequestLifecycleMessageRead(
            title=prepared.title,
            message=prepared.message,
            notification_event=prepared.event_type.value,
            language_code=prepared.language_code,
            preparation_scope=prepared.preparation_scope,
            w1_metadata=meta,
            internal_disclaimer=internal_disc,
            customer_preview_disclaimer=customer_disc,
            request_status=row.status.value,
            booking_bridge_status_used_for_resolution=(
                bridge_status.value if bridge_status is not None else None
            ),
        )
