"""Read-only move placement inspection for admin order detail (Phase 6 / Step 30).

No persisted move-audit rows: snapshot reflects **current** `tour_id` / `boarding_point_id`
and `orders.updated_at` only — not a from → to timeline.
"""

from __future__ import annotations

from app.models.order import Order
from app.schemas.admin import AdminOrderMovePlacementSnapshot


def compute_move_placement_snapshot(*, order: Order) -> AdminOrderMovePlacementSnapshot:
    """Build placement snapshot from loaded order + tour + boarding (required for admin detail)."""
    t = order.tour
    bp = order.boarding_point
    if t is None or bp is None:
        raise ValueError("order.tour and order.boarding_point must be loaded for move placement snapshot")

    return AdminOrderMovePlacementSnapshot(
        tour_id=order.tour_id,
        boarding_point_id=order.boarding_point_id,
        tour_code=t.code,
        tour_departure_datetime=t.departure_datetime,
        boarding_city=bp.city,
        order_updated_at=order.updated_at,
        note=(
            "Move history timeline is not persisted. This block shows the current tour and boarding "
            "placement only. Use change logs or external ops notes if a prior placement must be recovered."
        ),
    )
