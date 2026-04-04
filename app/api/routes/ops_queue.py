"""Internal JSON endpoints for ops: handoff/waitlist queues and handoff claim/close."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.ops_queue_auth import require_ops_queue_token
from app.db.session import get_db
from app.models.handoff import Handoff
from app.schemas.ops_queue import (
    OpsHandoffActionRead,
    OpsHandoffClaimRequest,
    OpsHandoffCloseRequest,
    OpsHandoffQueueRead,
    OpsWaitlistActionRead,
    OpsWaitlistQueueRead,
)
from app.models.waitlist import WaitlistEntry
from app.services.handoff_ops_actions import (
    HandoffClaimStateError,
    HandoffCloseStateError,
    HandoffInvalidOperatorError,
    HandoffNotFoundError,
    HandoffOpsActionService,
)
from app.services.ops_queue_read import OpsQueueReadService
from app.services.waitlist_ops_actions import (
    WAITLIST_STATUS_CLOSED,
    WaitlistClaimStateError,
    WaitlistCloseStateError,
    WaitlistEntryNotFoundError,
    WaitlistOpsActionService,
)

router = APIRouter(
    prefix="/internal/ops",
    tags=["internal-ops"],
    dependencies=[Depends(require_ops_queue_token)],
)


def _to_handoff_action_read(row: Handoff) -> OpsHandoffActionRead:
    return OpsHandoffActionRead(
        id=row.id,
        status=row.status,
        assigned_operator_id=row.assigned_operator_id,
        updated_at=row.updated_at,
    )


def _to_waitlist_action_read(row: WaitlistEntry) -> OpsWaitlistActionRead:
    return OpsWaitlistActionRead(
        id=row.id,
        status=row.status,
        user_id=row.user_id,
        tour_id=row.tour_id,
        seats_count=row.seats_count,
        created_at=row.created_at,
    )


@router.get("/handoffs/open", response_model=OpsHandoffQueueRead)
def get_open_handoffs(
    db: Session = Depends(get_db),
    limit: int = Query(default=500, ge=1, le=2000, description="Max rows to return."),
) -> OpsHandoffQueueRead:
    """Open `handoffs` rows only (`status == open`), separate from waitlist."""
    return OpsQueueReadService().open_handoffs(db, limit=limit)


@router.get("/waitlist/active", response_model=OpsWaitlistQueueRead)
def get_active_waitlist(
    db: Session = Depends(get_db),
    limit: int = Query(default=500, ge=1, le=2000, description="Max rows to return."),
) -> OpsWaitlistQueueRead:
    """Active waitlist interest rows only (`status == active`); not bookings or orders."""
    return OpsQueueReadService().active_waitlist(db, limit=limit)


@router.patch("/handoffs/{handoff_id}/claim", response_model=OpsHandoffActionRead)
def claim_handoff(
    handoff_id: int,
    body: OpsHandoffClaimRequest = Body(default_factory=OpsHandoffClaimRequest),
    db: Session = Depends(get_db),
) -> OpsHandoffActionRead:
    """Move handoff from `open` to `in_review`; optional `assigned_operator_id`."""
    svc = HandoffOpsActionService()
    try:
        row = svc.claim(db, handoff_id=handoff_id, operator_id=body.operator_id)
    except HandoffNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="handoff_not_found") from None
    except HandoffClaimStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "handoff_not_open", "current_status": exc.current_status},
        ) from None
    except HandoffInvalidOperatorError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_operator_id") from None
    db.commit()
    return _to_handoff_action_read(row)


@router.patch("/handoffs/{handoff_id}/close", response_model=OpsHandoffActionRead)
def close_handoff(
    handoff_id: int,
    body: OpsHandoffCloseRequest = Body(default_factory=OpsHandoffCloseRequest),
    db: Session = Depends(get_db),
) -> OpsHandoffActionRead:
    """Set status to `closed` (from `open` or `in_review`); does not touch orders or payments."""
    svc = HandoffOpsActionService()
    try:
        row = svc.close(db, handoff_id=handoff_id, operator_id=body.operator_id)
    except HandoffNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="handoff_not_found") from None
    except HandoffCloseStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "handoff_already_closed", "current_status": exc.current_status},
        ) from None
    except HandoffInvalidOperatorError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_operator_id") from None
    db.commit()
    return _to_handoff_action_read(row)


@router.patch("/waitlist/{waitlist_id}/claim", response_model=OpsWaitlistActionRead)
def claim_waitlist_entry(
    waitlist_id: int,
    db: Session = Depends(get_db),
) -> OpsWaitlistActionRead:
    """`active` → `in_review`; removes row from GET .../waitlist/active. No operator field on model."""
    svc = WaitlistOpsActionService()
    try:
        row = svc.claim(db, waitlist_entry_id=waitlist_id)
    except WaitlistEntryNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="waitlist_entry_not_found") from None
    except WaitlistClaimStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "waitlist_not_active", "current_status": exc.current_status},
        ) from None
    db.commit()
    return _to_waitlist_action_read(row)


@router.patch("/waitlist/{waitlist_id}/close", response_model=OpsWaitlistActionRead)
def close_waitlist_entry(
    waitlist_id: int,
    db: Session = Depends(get_db),
) -> OpsWaitlistActionRead:
    """`active` or `in_review` → `closed`; no seats or payment side effects."""
    svc = WaitlistOpsActionService()
    try:
        row = svc.close(db, waitlist_entry_id=waitlist_id)
    except WaitlistEntryNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="waitlist_entry_not_found") from None
    except WaitlistCloseStateError as exc:
        code = (
            "waitlist_already_closed"
            if exc.current_status == WAITLIST_STATUS_CLOSED
            else "waitlist_close_not_allowed"
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": code, "current_status": exc.current_status},
        ) from None
    db.commit()
    return _to_waitlist_action_read(row)
