"""Admin API: read surfaces + narrow writes (protected by ADMIN_API_TOKEN)."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.admin_auth import require_admin_api_token
from app.db.session import get_db
from app.models.enums import TourStatus
from app.schemas.admin import (
    AdminBoardingPointCreate,
    AdminBoardingPointTranslationUpsert,
    AdminBoardingPointUpdate,
    AdminHandoffAssignBody,
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
) -> AdminOrderListRead:
    return AdminReadService().list_orders(
        db,
        limit=limit,
        offset=offset,
        lifecycle_kind=lifecycle_kind,
        tour_id=tour_id,
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
) -> AdminHandoffListRead:
    return AdminReadService().list_handoffs(db, limit=limit, offset=offset, status=status)


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
