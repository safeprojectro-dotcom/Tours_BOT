# Phase 7 / Step 10 — historical prompt archive

**Status:** completed (implementation + docs). See `docs/CHAT_HANDOFF.md` for the live checkpoint.

## Goal (narrow slice)

- Add **`POST /admin/handoffs/{handoff_id}/assign-operator`**.
- **Only** when handoff **`reason=group_followup_start`**; otherwise **`400`** with `handoff_assign_group_followup_reason_only`.
- Same assignment rules as existing **`POST .../assign`** (Phase 6 / Step 21): status **`open`** or **`in_review`** only; operator must exist; idempotent repeat with same `assigned_operator_id`; **no** reassignment to a different operator.
- **`POST /admin/handoffs/{id}/assign`** behavior **unchanged** for all reasons.

## Explicitly out of scope

- Schema migration, notifications, booking/payment, public/Mini App/waitlist/handoff customer flows.
- Broad claim/takeover engine, internal ops workflow redesign.

## References

- Code: `app/api/routes/admin.py`, `app/services/admin_handoff_write.py`
- Tests: `tests/unit/test_api_admin.py`
