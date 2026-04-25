"""Admin API: read surfaces + narrow writes (protected by ADMIN_API_TOKEN)."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.admin_auth import require_admin_api_token
from app.db.session import get_db
from app.models.enums import (
    BookingStatus,
    CustomMarketplaceRequestStatus,
    OperatorWorkflowIntent,
    SupplierOfferLifecycle,
    TourStatus,
)
from app.models.supplier import Supplier
from app.schemas.admin import (
    AdminBoardingPointCreate,
    AdminBoardingPointTranslationUpsert,
    AdminBoardingPointUpdate,
    AdminHandoffAssignBody,
    AdminHandoffGroupFollowupQueueFilter,
    AdminHandoffListRead,
    AdminHandoffRead,
    AdminOrderDetailRead,
    AdminOrderListRead,
    AdminOrderMoveBody,
    AdminOverviewRead,
    AdminTourCoreUpdate,
    AdminTourCoverSet,
    AdminTourCreate,
    AdminTourDetailRead,
    AdminTourListRead,
    AdminSupplierCreate,
    AdminSupplierCreatedRead,
    AdminSupplierListRead,
    AdminSupplierOnboardingReject,
    AdminSupplierRead,
    AdminSupplierStatusReason,
    AdminTourTranslationUpsert,
)
from app.services.admin_handoff_write import (
    AdminHandoffAssignGroupFollowupReasonOnlyError,
    AdminHandoffAssignStateError,
    AdminHandoffCloseStateError,
    AdminHandoffInvalidOperatorError,
    AdminHandoffMarkInReviewStateError,
    AdminHandoffMarkInWorkAssignmentRequiredError,
    AdminHandoffMarkInWorkReasonOnlyError,
    AdminHandoffMarkInWorkStateError,
    AdminHandoffNotFoundError,
    AdminHandoffReassignNotAllowedError,
    AdminHandoffReopenStateError,
    AdminHandoffResolveGroupFollowupReasonOnlyError,
    AdminHandoffResolveGroupFollowupStateError,
    AdminHandoffWriteService,
)
from app.services.admin_order_move_write import AdminOrderMoveNotAllowedError, AdminOrderMoveWriteService
from app.services.admin_order_write import (
    AdminOrderMarkCancelledByOperatorNotAllowedError,
    AdminOrderMarkDuplicateNotAllowedError,
    AdminOrderMarkNoShowNotAllowedError,
    AdminOrderMarkReadyForDepartureNotAllowedError,
    AdminOrderNotFoundError,
    AdminOrderWriteService,
)
from app.services.admin_order_lifecycle import AdminOrderLifecycleKind
from app.services.admin_read import AdminReadService
from app.services.supplier_offer_moderation_service import (
    SupplierOfferModerationNotFoundError,
    SupplierOfferModerationService,
    SupplierOfferModerationStateError,
    SupplierOfferPublicationConfigError,
)
from app.services.supplier_offer_supplier_notification_service import SupplierOfferSupplierNotificationService
from app.services.supplier_offer_execution_link_service import (
    SupplierOfferExecutionLinkNotFoundError,
    SupplierOfferExecutionLinkService,
    SupplierOfferExecutionLinkValidationError,
)
from app.services.supplier_offer_service import SupplierOfferService
from app.repositories.user import UserRepository
from app.services.custom_marketplace_request_service import (
    CustomMarketplaceRequestAssignConflictError,
    CustomMarketplaceRequestMarkUnderReviewNotAllowedError,
    CustomMarketplaceRequestNotAssignableError,
    CustomMarketplaceRequestNotFoundError,
    CustomMarketplaceRequestOperatorDecisionNotAllowedError,
    CustomMarketplaceRequestService,
    CustomMarketplaceValidationError,
)
from app.services.custom_request_booking_bridge_service import (
    BookingBridgeConflictError,
    BookingBridgeNotFoundError,
    BookingBridgeValidationError,
    CustomRequestBookingBridgeService,
)
from app.schemas.custom_marketplace import (
    AdminCustomRequestBookingBridgeClose,
    AdminCustomRequestBookingBridgeCreate,
    AdminCustomRequestBookingBridgePatch,
    AdminCustomRequestBookingBridgeReplace,
    AdminCustomRequestPatch,
    AdminCustomRequestResolutionApply,
    AdminOperatorDecisionApply,
    CustomMarketplaceRequestDetailRead,
    CustomMarketplaceRequestListRead,
    CustomMarketplaceRequestRead,
    CustomRequestBookingBridgeRead,
)
from app.schemas.supplier_admin import (
    AdminSupplierOfferExecutionLinkBody,
    AdminSupplierOfferExecutionLinkCloseBody,
    AdminSupplierOfferPublishResult,
    AdminSupplierOfferRejectBody,
    SupplierOfferExecutionLinkListRead,
    SupplierOfferExecutionLinkRead,
    SupplierOfferListRead,
    SupplierOfferRead,
)
from app.repositories.supplier import SupplierOfferRepository
from app.services.admin_supplier_write import AdminSupplierDuplicateCodeError, AdminSupplierWriteService
from app.services.supplier_onboarding_service import (
    SupplierOnboardingApprovalValidationError,
    SupplierOnboardingNotFoundError,
    SupplierOnboardingStatusTransitionError,
    SupplierOnboardingService,
)
from app.services.admin_tour_write import (
    AdminBoardingPointInUseError,
    AdminBoardingPointNotFoundError,
    AdminBoardingPointTranslationNotFoundError,
    AdminTourCreateValidationError,
    AdminTourDuplicateCodeError,
    AdminTourNotFoundError,
    AdminTourTranslationNotFoundError,
    AdminTourWriteService,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_api_token)],
)


@router.get("/overview", response_model=AdminOverviewRead)
def get_admin_overview(
    db: Session = Depends(get_db),
) -> AdminOverviewRead:
    return AdminReadService().overview(db)


@router.post("/tours", response_model=AdminTourDetailRead, status_code=status.HTTP_201_CREATED)
def create_admin_tour(
    db: Session = Depends(get_db),
    payload: AdminTourCreate = Body(...),
) -> AdminTourDetailRead:
    try:
        detail = AdminTourWriteService().create_tour(db, payload=payload)
    except AdminTourDuplicateCodeError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tour code already exists.",
        ) from None
    except AdminTourCreateValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return detail


@router.put("/tours/{tour_id}/cover", response_model=AdminTourDetailRead)
def put_admin_tour_cover(
    tour_id: int,
    db: Session = Depends(get_db),
    payload: AdminTourCoverSet = Body(...),
) -> AdminTourDetailRead:
    try:
        detail = AdminTourWriteService().set_tour_cover(db, tour_id=tour_id, payload=payload)
    except AdminTourNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tour not found.") from None
    db.commit()
    return detail


@router.patch("/tours/{tour_id}", response_model=AdminTourDetailRead)
def patch_admin_tour_core(
    tour_id: int,
    db: Session = Depends(get_db),
    payload: AdminTourCoreUpdate = Body(...),
) -> AdminTourDetailRead:
    try:
        detail = AdminTourWriteService().update_tour_core(db, tour_id=tour_id, payload=payload)
    except AdminTourNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tour not found.") from None
    except AdminTourCreateValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return detail


@router.post("/tours/{tour_id}/archive", response_model=AdminTourDetailRead)
def post_admin_tour_archive(
    tour_id: int,
    db: Session = Depends(get_db),
) -> AdminTourDetailRead:
    try:
        detail = AdminTourWriteService().archive_tour(db, tour_id=tour_id)
    except AdminTourNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tour not found.") from None
    except AdminTourCreateValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return detail


@router.post("/tours/{tour_id}/unarchive", response_model=AdminTourDetailRead)
def post_admin_tour_unarchive(
    tour_id: int,
    db: Session = Depends(get_db),
) -> AdminTourDetailRead:
    try:
        detail = AdminTourWriteService().unarchive_tour(db, tour_id=tour_id)
    except AdminTourNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tour not found.") from None
    except AdminTourCreateValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return detail


@router.put("/tours/{tour_id}/translations/{language_code}", response_model=AdminTourDetailRead)
def put_admin_tour_translation(
    tour_id: int,
    language_code: str,
    db: Session = Depends(get_db),
    payload: AdminTourTranslationUpsert = Body(...),
) -> AdminTourDetailRead:
    try:
        detail = AdminTourWriteService().upsert_tour_translation(
            db,
            tour_id=tour_id,
            language_code=language_code,
            payload=payload,
        )
    except AdminTourNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tour not found.") from None
    except AdminTourCreateValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return detail


@router.delete(
    "/tours/{tour_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_admin_tour_translation(
    tour_id: int,
    language_code: str,
    db: Session = Depends(get_db),
) -> None:
    try:
        AdminTourWriteService().delete_tour_translation(db, tour_id=tour_id, language_code=language_code)
    except AdminTourNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tour not found.") from None
    except AdminTourTranslationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Translation not found.") from None
    except AdminTourCreateValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()


@router.post(
    "/tours/{tour_id}/boarding-points",
    response_model=AdminTourDetailRead,
    status_code=status.HTTP_201_CREATED,
)
def post_admin_tour_boarding_point(
    tour_id: int,
    db: Session = Depends(get_db),
    payload: AdminBoardingPointCreate = Body(...),
) -> AdminTourDetailRead:
    try:
        detail = AdminTourWriteService().add_boarding_point(db, tour_id=tour_id, payload=payload)
    except AdminTourNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tour not found.") from None
    db.commit()
    return detail


@router.patch("/boarding-points/{boarding_point_id}", response_model=AdminTourDetailRead)
def patch_admin_boarding_point(
    boarding_point_id: int,
    db: Session = Depends(get_db),
    payload: AdminBoardingPointUpdate = Body(...),
) -> AdminTourDetailRead:
    try:
        detail = AdminTourWriteService().update_boarding_point(
            db,
            boarding_point_id=boarding_point_id,
            payload=payload,
        )
    except AdminBoardingPointNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Boarding point not found.",
        ) from None
    except AdminTourCreateValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return detail


@router.put(
    "/boarding-points/{boarding_point_id}/translations/{language_code}",
    response_model=AdminTourDetailRead,
)
def put_admin_boarding_point_translation(
    boarding_point_id: int,
    language_code: str,
    db: Session = Depends(get_db),
    payload: AdminBoardingPointTranslationUpsert = Body(...),
) -> AdminTourDetailRead:
    try:
        detail = AdminTourWriteService().upsert_boarding_point_translation(
            db,
            boarding_point_id=boarding_point_id,
            language_code=language_code,
            payload=payload,
        )
    except AdminBoardingPointNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Boarding point not found.",
        ) from None
    except AdminTourCreateValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return detail


@router.delete(
    "/boarding-points/{boarding_point_id}/translations/{language_code}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_admin_boarding_point_translation(
    boarding_point_id: int,
    language_code: str,
    db: Session = Depends(get_db),
) -> None:
    try:
        AdminTourWriteService().delete_boarding_point_translation(
            db,
            boarding_point_id=boarding_point_id,
            language_code=language_code,
        )
    except AdminBoardingPointNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Boarding point not found.",
        ) from None
    except AdminBoardingPointTranslationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Translation not found.",
        ) from None
    except AdminTourCreateValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()


@router.delete(
    "/boarding-points/{boarding_point_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_admin_boarding_point(
    boarding_point_id: int,
    db: Session = Depends(get_db),
) -> None:
    try:
        AdminTourWriteService().delete_boarding_point(db, boarding_point_id=boarding_point_id)
    except AdminBoardingPointNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Boarding point not found.",
        ) from None
    except AdminBoardingPointInUseError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Boarding point cannot be deleted while orders reference it.",
        ) from None
    db.commit()


@router.get("/tours", response_model=AdminTourListRead)
def list_admin_tours(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0, le=100_000),
    status: TourStatus | None = Query(default=None),
    guaranteed_only: bool = Query(default=False),
) -> AdminTourListRead:
    return AdminReadService().list_tours(
        db,
        limit=limit,
        offset=offset,
        status=status,
        guaranteed_only=guaranteed_only,
    )


@router.get("/tours/{tour_id}", response_model=AdminTourDetailRead)
def get_admin_tour_detail(
    tour_id: int,
    db: Session = Depends(get_db),
) -> AdminTourDetailRead:
    detail = AdminReadService().get_tour_detail(db, tour_id=tour_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tour not found.")
    return detail


@router.get("/orders", response_model=AdminOrderListRead)
def list_admin_orders(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0, le=100_000),
    lifecycle_kind: AdminOrderLifecycleKind | None = Query(default=None),
    tour_id: int | None = Query(default=None, ge=1),
    booking_status: BookingStatus | None = Query(default=None),
) -> AdminOrderListRead:
    return AdminReadService().list_orders(
        db,
        limit=limit,
        offset=offset,
        lifecycle_kind=lifecycle_kind,
        tour_id=tour_id,
        booking_status=booking_status,
    )


@router.get("/orders/{order_id}", response_model=AdminOrderDetailRead)
def get_admin_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
) -> AdminOrderDetailRead:
    detail = AdminReadService().get_order_detail(db, order_id=order_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    return detail


@router.post("/orders/{order_id}/mark-cancelled-by-operator", response_model=AdminOrderDetailRead)
def post_admin_order_mark_cancelled_by_operator(
    order_id: int,
    db: Session = Depends(get_db),
) -> AdminOrderDetailRead:
    try:
        AdminOrderWriteService().mark_cancelled_by_operator(db, order_id=order_id)
    except AdminOrderNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.") from None
    except AdminOrderMarkCancelledByOperatorNotAllowedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "order_mark_cancelled_by_operator_not_allowed",
                "booking_status": exc.booking_status,
                "payment_status": exc.payment_status,
                "cancellation_status": exc.cancellation_status,
            },
        ) from None
    db.commit()
    detail = AdminReadService().get_order_detail(db, order_id=order_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    return detail


@router.post("/orders/{order_id}/mark-duplicate", response_model=AdminOrderDetailRead)
def post_admin_order_mark_duplicate(
    order_id: int,
    db: Session = Depends(get_db),
) -> AdminOrderDetailRead:
    try:
        AdminOrderWriteService().mark_duplicate(db, order_id=order_id)
    except AdminOrderNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.") from None
    except AdminOrderMarkDuplicateNotAllowedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "order_mark_duplicate_not_allowed",
                "booking_status": exc.booking_status,
                "payment_status": exc.payment_status,
                "cancellation_status": exc.cancellation_status,
            },
        ) from None
    db.commit()
    detail = AdminReadService().get_order_detail(db, order_id=order_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    return detail


@router.post("/orders/{order_id}/mark-no-show", response_model=AdminOrderDetailRead)
def post_admin_order_mark_no_show(
    order_id: int,
    db: Session = Depends(get_db),
) -> AdminOrderDetailRead:
    try:
        AdminOrderWriteService().mark_no_show(db, order_id=order_id)
    except AdminOrderNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.") from None
    except AdminOrderMarkNoShowNotAllowedError as exc:
        err_body: dict = {
            "code": "order_mark_no_show_not_allowed",
            "booking_status": exc.booking_status,
            "payment_status": exc.payment_status,
            "cancellation_status": exc.cancellation_status,
        }
        if exc.reason is not None:
            err_body["reason"] = exc.reason
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_body,
        ) from None
    db.commit()
    detail_read = AdminReadService().get_order_detail(db, order_id=order_id)
    if detail_read is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    return detail_read


@router.post("/orders/{order_id}/mark-ready-for-departure", response_model=AdminOrderDetailRead)
def post_admin_order_mark_ready_for_departure(
    order_id: int,
    db: Session = Depends(get_db),
) -> AdminOrderDetailRead:
    try:
        AdminOrderWriteService().mark_ready_for_departure(db, order_id=order_id)
    except AdminOrderNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.") from None
    except AdminOrderMarkReadyForDepartureNotAllowedError as exc:
        err_body: dict = {
            "code": "order_mark_ready_for_departure_not_allowed",
            "booking_status": exc.booking_status,
            "payment_status": exc.payment_status,
            "cancellation_status": exc.cancellation_status,
        }
        if exc.reason is not None:
            err_body["reason"] = exc.reason
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_body,
        ) from None
    db.commit()
    detail_read = AdminReadService().get_order_detail(db, order_id=order_id)
    if detail_read is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    return detail_read


@router.post("/orders/{order_id}/move", response_model=AdminOrderDetailRead)
def post_admin_order_move(
    order_id: int,
    body: AdminOrderMoveBody,
    db: Session = Depends(get_db),
) -> AdminOrderDetailRead:
    try:
        AdminOrderMoveWriteService().move_order(
            db,
            order_id=order_id,
            target_tour_id=body.target_tour_id,
            target_boarding_point_id=body.target_boarding_point_id,
        )
    except AdminOrderNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.") from None
    except AdminOrderMoveNotAllowedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": exc.message},
        ) from None
    db.commit()
    detail_read = AdminReadService().get_order_detail(db, order_id=order_id)
    if detail_read is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    return detail_read


@router.get("/handoffs", response_model=AdminHandoffListRead)
def list_admin_handoffs(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0, le=100_000),
    status: str | None = Query(
        default=None,
        description="Filter by handoff status (e.g. open, in_review, closed). Omit for all.",
    ),
    group_followup_queue: AdminHandoffGroupFollowupQueueFilter | None = Query(
        default=None,
        description="Phase 7 / Step 15: narrow filter for group_followup_start queue bucket only (AND with status if both set).",
    ),
) -> AdminHandoffListRead:
    gq = group_followup_queue.value if group_followup_queue is not None else None
    return AdminReadService().list_handoffs(
        db, limit=limit, offset=offset, status=status, group_followup_queue=gq
    )


@router.get("/handoffs/{handoff_id}", response_model=AdminHandoffRead)
def get_admin_handoff_detail(
    handoff_id: int,
    db: Session = Depends(get_db),
) -> AdminHandoffRead:
    detail = AdminReadService().get_handoff_detail(db, handoff_id=handoff_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handoff not found.")
    return detail


@router.post("/handoffs/{handoff_id}/mark-in-review", response_model=AdminHandoffRead)
def post_admin_handoff_mark_in_review(
    handoff_id: int,
    db: Session = Depends(get_db),
) -> AdminHandoffRead:
    try:
        AdminHandoffWriteService().mark_in_review(db, handoff_id=handoff_id)
    except AdminHandoffNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handoff not found.") from None
    except AdminHandoffMarkInReviewStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "handoff_mark_in_review_not_allowed",
                "current_status": exc.current_status,
            },
        ) from None
    db.commit()
    detail = AdminReadService().get_handoff_detail(db, handoff_id=handoff_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handoff not found.")
    return detail


@router.post("/handoffs/{handoff_id}/close", response_model=AdminHandoffRead)
def post_admin_handoff_close(
    handoff_id: int,
    db: Session = Depends(get_db),
) -> AdminHandoffRead:
    try:
        AdminHandoffWriteService().close_handoff(db, handoff_id=handoff_id)
    except AdminHandoffNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handoff not found.") from None
    except AdminHandoffCloseStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "handoff_close_not_allowed",
                "current_status": exc.current_status,
            },
        ) from None
    db.commit()
    detail = AdminReadService().get_handoff_detail(db, handoff_id=handoff_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handoff not found.")
    return detail


@router.post("/handoffs/{handoff_id}/assign", response_model=AdminHandoffRead)
def post_admin_handoff_assign(
    handoff_id: int,
    body: AdminHandoffAssignBody,
    db: Session = Depends(get_db),
) -> AdminHandoffRead:
    try:
        AdminHandoffWriteService().assign_handoff(
            db,
            handoff_id=handoff_id,
            assigned_operator_id=body.assigned_operator_id,
        )
    except AdminHandoffNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handoff not found.") from None
    except AdminHandoffAssignStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "handoff_assign_not_allowed",
                "current_status": exc.current_status,
            },
        ) from None
    except AdminHandoffInvalidOperatorError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "handoff_assign_operator_not_found"},
        ) from None
    except AdminHandoffReassignNotAllowedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "handoff_reassign_not_allowed",
                "current_assigned_operator_id": exc.current_assigned_operator_id,
                "requested_operator_id": exc.requested_operator_id,
            },
        ) from None
    db.commit()
    detail = AdminReadService().get_handoff_detail(db, handoff_id=handoff_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handoff not found.")
    return detail


@router.post("/handoffs/{handoff_id}/assign-operator", response_model=AdminHandoffRead)
def post_admin_handoff_assign_group_followup_operator(
    handoff_id: int,
    body: AdminHandoffAssignBody,
    db: Session = Depends(get_db),
) -> AdminHandoffRead:
    """Phase 7 / Step 10 — assign operator only for ``reason=group_followup_start`` (narrow path)."""
    try:
        AdminHandoffWriteService().assign_group_followup_operator(
            db,
            handoff_id=handoff_id,
            assigned_operator_id=body.assigned_operator_id,
        )
    except AdminHandoffNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handoff not found.") from None
    except AdminHandoffAssignGroupFollowupReasonOnlyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "handoff_assign_group_followup_reason_only",
                "current_reason": exc.current_reason,
            },
        ) from None
    except AdminHandoffAssignStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "handoff_assign_not_allowed",
                "current_status": exc.current_status,
            },
        ) from None
    except AdminHandoffInvalidOperatorError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "handoff_assign_operator_not_found"},
        ) from None
    except AdminHandoffReassignNotAllowedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "handoff_reassign_not_allowed",
                "current_assigned_operator_id": exc.current_assigned_operator_id,
                "requested_operator_id": exc.requested_operator_id,
            },
        ) from None
    db.commit()
    detail = AdminReadService().get_handoff_detail(db, handoff_id=handoff_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handoff not found.")
    return detail


@router.post("/handoffs/{handoff_id}/mark-in-work", response_model=AdminHandoffRead)
def post_admin_handoff_mark_group_followup_in_work(
    handoff_id: int,
    db: Session = Depends(get_db),
) -> AdminHandoffRead:
    """Phase 7 / Step 12 — take-in-work for assigned ``group_followup_start`` only (open → in_review)."""
    try:
        AdminHandoffWriteService().mark_group_followup_in_work(db, handoff_id=handoff_id)
    except AdminHandoffNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handoff not found.") from None
    except AdminHandoffMarkInWorkReasonOnlyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "handoff_mark_in_work_reason_only",
                "current_reason": exc.current_reason,
            },
        ) from None
    except AdminHandoffMarkInWorkAssignmentRequiredError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "handoff_mark_in_work_assignment_required"},
        ) from None
    except AdminHandoffMarkInWorkStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "handoff_mark_in_work_not_allowed",
                "current_status": exc.current_status,
            },
        ) from None
    db.commit()
    detail = AdminReadService().get_handoff_detail(db, handoff_id=handoff_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handoff not found.")
    return detail


@router.post("/handoffs/{handoff_id}/resolve-group-followup", response_model=AdminHandoffRead)
def post_admin_handoff_resolve_group_followup(
    handoff_id: int,
    db: Session = Depends(get_db),
) -> AdminHandoffRead:
    """Phase 7 / Steps 13–14 — close/resolve ``group_followup_start`` from ``in_review`` only."""
    try:
        AdminHandoffWriteService().resolve_group_followup_handoff(db, handoff_id=handoff_id)
    except AdminHandoffNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handoff not found.") from None
    except AdminHandoffResolveGroupFollowupReasonOnlyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "handoff_resolve_group_followup_reason_only",
                "current_reason": exc.current_reason,
            },
        ) from None
    except AdminHandoffResolveGroupFollowupStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "handoff_resolve_group_followup_not_allowed",
                "current_status": exc.current_status,
            },
        ) from None
    db.commit()
    detail = AdminReadService().get_handoff_detail(db, handoff_id=handoff_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handoff not found.")
    return detail


@router.post("/handoffs/{handoff_id}/reopen", response_model=AdminHandoffRead)
def post_admin_handoff_reopen(
    handoff_id: int,
    db: Session = Depends(get_db),
) -> AdminHandoffRead:
    try:
        AdminHandoffWriteService().reopen_handoff(db, handoff_id=handoff_id)
    except AdminHandoffNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handoff not found.") from None
    except AdminHandoffReopenStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "handoff_reopen_not_allowed",
                "current_status": exc.current_status,
            },
        ) from None
    db.commit()
    detail = AdminReadService().get_handoff_detail(db, handoff_id=handoff_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Handoff not found.")
    return detail


@router.post("/suppliers", response_model=AdminSupplierCreatedRead, status_code=status.HTTP_201_CREATED)
def post_admin_supplier(
    db: Session = Depends(get_db),
    payload: AdminSupplierCreate = Body(...),
) -> AdminSupplierCreatedRead:
    """Bootstrap a supplier account + API credential (central admin only)."""
    try:
        supplier, api_token = AdminSupplierWriteService().create_supplier_with_credential(
            db,
            code=payload.code,
            display_name=payload.display_name,
            credential_label=payload.credential_label,
        )
    except AdminSupplierDuplicateCodeError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Supplier code already exists.") from None
    db.commit()
    return AdminSupplierCreatedRead(supplier=AdminSupplierRead.model_validate(supplier), api_token=api_token)


@router.get("/suppliers", response_model=AdminSupplierListRead)
def get_admin_suppliers(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> AdminSupplierListRead:
    stmt = select(Supplier).order_by(Supplier.created_at.desc(), Supplier.id.desc()).offset(offset).limit(limit)
    rows = list(db.scalars(stmt).all())
    return AdminSupplierListRead(
        items=[AdminSupplierRead.model_validate(r) for r in rows],
        total_returned=len(rows),
    )


@router.post("/suppliers/{supplier_id}/onboarding/approve", response_model=AdminSupplierRead)
def post_admin_supplier_onboarding_approve(
    supplier_id: int,
    db: Session = Depends(get_db),
) -> AdminSupplierRead:
    try:
        row = SupplierOnboardingService().admin_approve(db, supplier_id=supplier_id)
    except SupplierOnboardingNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found.") from None
    except SupplierOnboardingApprovalValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    except SupplierOnboardingStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return AdminSupplierRead.model_validate(row)


@router.post("/suppliers/{supplier_id}/onboarding/reject", response_model=AdminSupplierRead)
def post_admin_supplier_onboarding_reject(
    supplier_id: int,
    db: Session = Depends(get_db),
    payload: AdminSupplierOnboardingReject = Body(...),
) -> AdminSupplierRead:
    try:
        row = SupplierOnboardingService().admin_reject(db, supplier_id=supplier_id, reason=payload.reason)
    except SupplierOnboardingNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found.") from None
    except SupplierOnboardingStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return AdminSupplierRead.model_validate(row)


@router.post("/suppliers/{supplier_id}/onboarding/suspend", response_model=AdminSupplierRead)
def post_admin_supplier_onboarding_suspend(
    supplier_id: int,
    db: Session = Depends(get_db),
    payload: AdminSupplierStatusReason = Body(...),
) -> AdminSupplierRead:
    try:
        row = SupplierOnboardingService().admin_suspend(db, supplier_id=supplier_id, reason=payload.reason)
    except SupplierOnboardingNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found.") from None
    except SupplierOnboardingStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return AdminSupplierRead.model_validate(row)


@router.post("/suppliers/{supplier_id}/onboarding/reactivate", response_model=AdminSupplierRead)
def post_admin_supplier_onboarding_reactivate(
    supplier_id: int,
    db: Session = Depends(get_db),
) -> AdminSupplierRead:
    try:
        row = SupplierOnboardingService().admin_reactivate(db, supplier_id=supplier_id)
    except SupplierOnboardingNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found.") from None
    except SupplierOnboardingStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return AdminSupplierRead.model_validate(row)


@router.post("/suppliers/{supplier_id}/onboarding/revoke", response_model=AdminSupplierRead)
def post_admin_supplier_onboarding_revoke(
    supplier_id: int,
    db: Session = Depends(get_db),
    payload: AdminSupplierStatusReason = Body(...),
) -> AdminSupplierRead:
    try:
        row = SupplierOnboardingService().admin_revoke(db, supplier_id=supplier_id, reason=payload.reason)
    except SupplierOnboardingNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found.") from None
    except SupplierOnboardingStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return AdminSupplierRead.model_validate(row)


@router.get("/suppliers/{supplier_id}", response_model=AdminSupplierRead)
def get_admin_supplier(supplier_id: int, db: Session = Depends(get_db)) -> AdminSupplierRead:
    row = db.get(Supplier, supplier_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found.")
    return AdminSupplierRead.model_validate(row)


@router.get("/suppliers/{supplier_id}/offers", response_model=SupplierOfferListRead)
def get_admin_supplier_offers(
    supplier_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> SupplierOfferListRead:
    if db.get(Supplier, supplier_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found.")
    svc = SupplierOfferService()
    items = svc.list_offers(db, supplier_id=supplier_id, limit=limit, offset=offset)
    return SupplierOfferListRead(items=items, total_returned=len(items))


@router.get("/supplier-offers", response_model=SupplierOfferListRead)
def list_admin_supplier_offers_moderation(
    db: Session = Depends(get_db),
    lifecycle_status: SupplierOfferLifecycle | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> SupplierOfferListRead:
    items = SupplierOfferModerationService().list_offers(
        db,
        lifecycle_status=lifecycle_status,
        limit=limit,
        offset=offset,
    )
    return SupplierOfferListRead(items=items, total_returned=len(items))


@router.get("/supplier-offers/{offer_id}", response_model=SupplierOfferRead)
def get_admin_supplier_offer_by_id(offer_id: int, db: Session = Depends(get_db)) -> SupplierOfferRead:
    row = SupplierOfferRepository().get_any(db, offer_id=offer_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.")
    return SupplierOfferRead.model_validate(row, from_attributes=True)


@router.post("/supplier-offers/{offer_id}/moderation/approve", response_model=SupplierOfferRead)
def post_admin_supplier_offer_approve(offer_id: int, db: Session = Depends(get_db)) -> SupplierOfferRead:
    try:
        row = SupplierOfferModerationService().approve(db, offer_id=offer_id)
    except SupplierOfferModerationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.") from None
    except SupplierOfferModerationStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    try:
        SupplierOfferSupplierNotificationService().notify_approved(db, offer_id=offer_id)
    except Exception:
        pass
    return row


@router.post("/supplier-offers/{offer_id}/moderation/reject", response_model=SupplierOfferRead)
def post_admin_supplier_offer_reject(
    offer_id: int,
    db: Session = Depends(get_db),
    payload: AdminSupplierOfferRejectBody = Body(...),
) -> SupplierOfferRead:
    try:
        row = SupplierOfferModerationService().reject(db, offer_id=offer_id, reason=payload.reason)
    except SupplierOfferModerationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.") from None
    except SupplierOfferModerationStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    try:
        SupplierOfferSupplierNotificationService().notify_rejected(
            db,
            offer_id=offer_id,
            reason=payload.reason,
        )
    except Exception:
        pass
    return row


@router.post("/supplier-offers/{offer_id}/publish", response_model=AdminSupplierOfferPublishResult)
def post_admin_supplier_offer_publish(offer_id: int, db: Session = Depends(get_db)) -> AdminSupplierOfferPublishResult:
    try:
        offer_read, message_id = SupplierOfferModerationService().publish(db, offer_id=offer_id)
    except SupplierOfferModerationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.") from None
    except SupplierOfferPublicationConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from None
    except SupplierOfferModerationStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    try:
        SupplierOfferSupplierNotificationService().notify_published(db, offer_id=offer_id)
    except Exception:
        pass
    return AdminSupplierOfferPublishResult(offer=offer_read, telegram_message_id=message_id)


@router.post("/supplier-offers/{offer_id}/execution-link", response_model=SupplierOfferExecutionLinkRead)
def post_admin_supplier_offer_execution_link(
    offer_id: int,
    db: Session = Depends(get_db),
    payload: AdminSupplierOfferExecutionLinkBody = Body(...),
) -> SupplierOfferExecutionLinkRead:
    try:
        row = SupplierOfferExecutionLinkService().link_offer_to_tour(
            db,
            offer_id=offer_id,
            tour_id=payload.tour_id,
            link_note=payload.link_note,
        )
    except SupplierOfferExecutionLinkNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.") from None
    except SupplierOfferExecutionLinkValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return row


@router.post("/supplier-offers/{offer_id}/link-tour", response_model=SupplierOfferExecutionLinkRead)
def post_admin_supplier_offer_link_tour(
    offer_id: int,
    db: Session = Depends(get_db),
    payload: AdminSupplierOfferExecutionLinkBody = Body(...),
) -> SupplierOfferExecutionLinkRead:
    try:
        row = SupplierOfferExecutionLinkService().create_link_for_offer(
            db,
            offer_id=offer_id,
            tour_id=payload.tour_id,
            link_note=payload.link_note,
        )
    except SupplierOfferExecutionLinkNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.") from None
    except SupplierOfferExecutionLinkValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return row


@router.post("/supplier-offers/{offer_id}/replace-link", response_model=SupplierOfferExecutionLinkRead)
def post_admin_supplier_offer_replace_link(
    offer_id: int,
    db: Session = Depends(get_db),
    payload: AdminSupplierOfferExecutionLinkBody = Body(...),
) -> SupplierOfferExecutionLinkRead:
    try:
        row = SupplierOfferExecutionLinkService().replace_link_for_offer(
            db,
            offer_id=offer_id,
            tour_id=payload.tour_id,
            link_note=payload.link_note,
        )
    except SupplierOfferExecutionLinkNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.") from None
    except SupplierOfferExecutionLinkValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return row


@router.get("/supplier-offers/{offer_id}/execution-links", response_model=SupplierOfferExecutionLinkListRead)
def list_admin_supplier_offer_execution_links(
    offer_id: int,
    db: Session = Depends(get_db),
) -> SupplierOfferExecutionLinkListRead:
    try:
        items = SupplierOfferExecutionLinkService().list_links_for_offer(
            db,
            offer_id=offer_id,
        )
    except SupplierOfferExecutionLinkNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.") from None
    return SupplierOfferExecutionLinkListRead(items=items, total_returned=len(items))


@router.get("/supplier-offers/{offer_id}/links", response_model=SupplierOfferExecutionLinkListRead)
def list_admin_supplier_offer_links(
    offer_id: int,
    db: Session = Depends(get_db),
) -> SupplierOfferExecutionLinkListRead:
    try:
        items = SupplierOfferExecutionLinkService().list_links_for_offer(
            db,
            offer_id=offer_id,
        )
    except SupplierOfferExecutionLinkNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.") from None
    return SupplierOfferExecutionLinkListRead(items=items, total_returned=len(items))


@router.post("/supplier-offers/{offer_id}/execution-link/close", response_model=SupplierOfferExecutionLinkRead)
def post_admin_supplier_offer_execution_link_close(
    offer_id: int,
    db: Session = Depends(get_db),
    payload: AdminSupplierOfferExecutionLinkCloseBody | None = Body(default=None),
) -> SupplierOfferExecutionLinkRead:
    body = payload or AdminSupplierOfferExecutionLinkCloseBody()
    try:
        row = SupplierOfferExecutionLinkService().close_active_link(
            db,
            offer_id=offer_id,
            reason=body.reason,
        )
    except SupplierOfferExecutionLinkNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active execution link not found.") from None
    except SupplierOfferExecutionLinkValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    assert row is not None
    return row


@router.post("/supplier-offers/{offer_id}/close-link", response_model=SupplierOfferExecutionLinkRead)
def post_admin_supplier_offer_close_link(
    offer_id: int,
    db: Session = Depends(get_db),
    payload: AdminSupplierOfferExecutionLinkCloseBody | None = Body(default=None),
) -> SupplierOfferExecutionLinkRead:
    body = payload or AdminSupplierOfferExecutionLinkCloseBody()
    try:
        row = SupplierOfferExecutionLinkService().close_active_link(
            db,
            offer_id=offer_id,
            reason=body.reason,
        )
    except SupplierOfferExecutionLinkNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active execution link not found.") from None
    except SupplierOfferExecutionLinkValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    assert row is not None
    return row


@router.post("/supplier-offers/{offer_id}/retract", response_model=SupplierOfferRead)
def post_admin_supplier_offer_retract(offer_id: int, db: Session = Depends(get_db)) -> SupplierOfferRead:
    try:
        row = SupplierOfferModerationService().retract_published(db, offer_id=offer_id)
    except SupplierOfferModerationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.") from None
    except SupplierOfferModerationStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    # Keep execution-link history consistent with publication lifecycle.
    SupplierOfferExecutionLinkService().close_active_link(
        db,
        offer_id=offer_id,
        reason="retracted",
        allow_missing=True,
    )
    db.commit()
    try:
        SupplierOfferSupplierNotificationService().notify_retracted(db, offer_id=offer_id)
    except Exception:
        pass
    return row


@router.get("/custom-requests", response_model=CustomMarketplaceRequestListRead)
def list_admin_custom_requests(
    db: Session = Depends(get_db),
    status_filter: CustomMarketplaceRequestStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> CustomMarketplaceRequestListRead:
    svc = CustomMarketplaceRequestService()
    items = svc.list_for_admin(db, status=status_filter, limit=limit, offset=offset)
    return CustomMarketplaceRequestListRead(items=items, total_returned=len(items))


@router.get("/custom-requests/{request_id}", response_model=CustomMarketplaceRequestDetailRead)
def get_admin_custom_request(request_id: int, db: Session = Depends(get_db)) -> CustomMarketplaceRequestDetailRead:
    try:
        return CustomMarketplaceRequestService().get_admin_detail(db, request_id=request_id)
    except CustomMarketplaceRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.") from None


@router.post("/custom-requests/{request_id}/assign-to-me", response_model=CustomMarketplaceRequestRead)
def post_admin_custom_request_assign_to_me(
    request_id: int,
    db: Session = Depends(get_db),
    x_admin_actor_telegram_id: str | None = Header(default=None, alias="X-Admin-Actor-Telegram-Id"),
) -> CustomMarketplaceRequestRead:
    """Y36.2: assign RFQ to the operator matching the given Telegram user id (internal users.id stored)."""
    if x_admin_actor_telegram_id is None or not str(x_admin_actor_telegram_id).strip().isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Admin-Actor-Telegram-Id header is required (Telegram user id of the operator).",
        )
    actor_tg = int(str(x_admin_actor_telegram_id).strip())
    user = UserRepository().get_by_telegram_user_id(db, telegram_user_id=actor_tg)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No User record for the given X-Admin-Actor-Telegram-Id.",
        )
    try:
        row = CustomMarketplaceRequestService().assign_to_me(
            db,
            request_id=request_id,
            actor_user_id=user.id,
        )
    except CustomMarketplaceRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.") from None
    except CustomMarketplaceRequestNotAssignableError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    except CustomMarketplaceRequestAssignConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from None
    db.commit()
    return row


@router.post("/custom-requests/{request_id}/mark-under-review", response_model=CustomMarketplaceRequestRead)
def post_admin_custom_request_mark_under_review(
    request_id: int,
    db: Session = Depends(get_db),
    x_admin_actor_telegram_id: str | None = Header(default=None, alias="X-Admin-Actor-Telegram-Id"),
) -> CustomMarketplaceRequestRead:
    """Y37.2: set RFQ to under_review when assigned to the operator matching the actor header; idempotent if already under_review."""
    if x_admin_actor_telegram_id is None or not str(x_admin_actor_telegram_id).strip().isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Admin-Actor-Telegram-Id header is required (Telegram user id of the operator).",
        )
    actor_tg = int(str(x_admin_actor_telegram_id).strip())
    user = UserRepository().get_by_telegram_user_id(db, telegram_user_id=actor_tg)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No User record for the given X-Admin-Actor-Telegram-Id.",
        )
    try:
        row = CustomMarketplaceRequestService().mark_under_review(
            db,
            request_id=request_id,
            actor_user_id=user.id,
        )
    except CustomMarketplaceRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.") from None
    except CustomMarketplaceRequestMarkUnderReviewNotAllowedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    except CustomMarketplaceRequestAssignConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from None
    db.commit()
    return row


@router.post("/custom-requests/{request_id}/operator-decision", response_model=CustomMarketplaceRequestRead)
def post_admin_custom_request_operator_decision(
    request_id: int,
    db: Session = Depends(get_db),
    payload: AdminOperatorDecisionApply = Body(...),
    x_admin_actor_telegram_id: str | None = Header(default=None, alias="X-Admin-Actor-Telegram-Id"),
) -> CustomMarketplaceRequestRead:
    """Y37.4: set operator workflow intent (v1: need_manual_followup only) when under_review and assigned to actor."""
    if x_admin_actor_telegram_id is None or not str(x_admin_actor_telegram_id).strip().isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Admin-Actor-Telegram-Id header is required (Telegram user id of the operator).",
        )
    actor_tg = int(str(x_admin_actor_telegram_id).strip())
    user = UserRepository().get_by_telegram_user_id(db, telegram_user_id=actor_tg)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No User record for the given X-Admin-Actor-Telegram-Id.",
        )
    try:
        row = CustomMarketplaceRequestService().set_operator_decision(
            db,
            request_id=request_id,
            actor_user_id=user.id,
            decision=OperatorWorkflowIntent.NEED_MANUAL_FOLLOWUP,
        )
    except CustomMarketplaceRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.") from None
    except CustomMarketplaceRequestOperatorDecisionNotAllowedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    except CustomMarketplaceRequestAssignConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from None
    except CustomMarketplaceValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return row


@router.patch("/custom-requests/{request_id}", response_model=CustomMarketplaceRequestRead)
def patch_admin_custom_request(
    request_id: int,
    db: Session = Depends(get_db),
    payload: AdminCustomRequestPatch = Body(...),
) -> CustomMarketplaceRequestRead:
    try:
        row = CustomMarketplaceRequestService().admin_patch(
            db,
            request_id=request_id,
            admin_intervention_note=payload.admin_intervention_note,
            status=payload.status,
        )
    except CustomMarketplaceRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.") from None
    db.commit()
    return row


@router.post("/custom-requests/{request_id}/resolution", response_model=CustomMarketplaceRequestRead)
def post_admin_custom_request_resolution(
    request_id: int,
    db: Session = Depends(get_db),
    payload: AdminCustomRequestResolutionApply = Body(...),
) -> CustomMarketplaceRequestRead:
    try:
        row = CustomMarketplaceRequestService().admin_apply_resolution(
            db,
            request_id=request_id,
            payload=payload,
        )
    except CustomMarketplaceRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.") from None
    except CustomMarketplaceValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return row


@router.post(
    "/custom-requests/{request_id}/booking-bridge",
    response_model=CustomRequestBookingBridgeRead,
    status_code=status.HTTP_201_CREATED,
)
def post_admin_custom_request_booking_bridge(
    request_id: int,
    db: Session = Depends(get_db),
    payload: AdminCustomRequestBookingBridgeCreate = Body(...),
) -> CustomRequestBookingBridgeRead:
    """Track 5b.1: explicit admin trigger — persists intent only (no reservation/payment)."""
    try:
        row = CustomRequestBookingBridgeService().create_bridge(
            db,
            request_id=request_id,
            payload=payload,
        )
    except BookingBridgeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from None
    except BookingBridgeConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from None
    except BookingBridgeValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return row


@router.patch(
    "/custom-requests/{request_id}/booking-bridge",
    response_model=CustomRequestBookingBridgeRead,
)
def patch_admin_custom_request_booking_bridge(
    request_id: int,
    db: Session = Depends(get_db),
    payload: AdminCustomRequestBookingBridgePatch = Body(...),
) -> CustomRequestBookingBridgeRead:
    try:
        row = CustomRequestBookingBridgeService().patch_bridge(
            db,
            request_id=request_id,
            payload=payload,
        )
    except BookingBridgeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from None
    except BookingBridgeValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return row


@router.post(
    "/custom-requests/{request_id}/booking-bridge/close",
    response_model=CustomRequestBookingBridgeRead,
)
def post_admin_custom_request_booking_bridge_close(
    request_id: int,
    db: Session = Depends(get_db),
    payload: AdminCustomRequestBookingBridgeClose = Body(...),
) -> CustomRequestBookingBridgeRead:
    """Track 5e: supersede or cancel the active bridge — no order/payment changes."""
    try:
        row = CustomRequestBookingBridgeService().close_active_bridge(
            db,
            request_id=request_id,
            payload=payload,
        )
    except BookingBridgeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from None
    except BookingBridgeValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return row


@router.post(
    "/custom-requests/{request_id}/booking-bridge/replace",
    response_model=CustomRequestBookingBridgeRead,
    status_code=status.HTTP_201_CREATED,
)
def post_admin_custom_request_booking_bridge_replace(
    request_id: int,
    db: Session = Depends(get_db),
    payload: AdminCustomRequestBookingBridgeReplace = Body(...),
) -> CustomRequestBookingBridgeRead:
    """Track 5e: supersede active bridge (if any) and create a new bridge in one transaction."""
    try:
        row = CustomRequestBookingBridgeService().replace_bridge(
            db,
            request_id=request_id,
            payload=payload,
        )
    except BookingBridgeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from None
    except BookingBridgeConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from None
    except BookingBridgeValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from None
    db.commit()
    return row
