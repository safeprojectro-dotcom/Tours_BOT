"""Internal read-only JSON endpoints for handoff and waitlist queues."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.ops_queue_auth import require_ops_queue_token
from app.db.session import get_db
from app.schemas.ops_queue import OpsHandoffQueueRead, OpsWaitlistQueueRead
from app.services.ops_queue_read import OpsQueueReadService

router = APIRouter(
    prefix="/internal/ops",
    tags=["internal-ops"],
    dependencies=[Depends(require_ops_queue_token)],
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
