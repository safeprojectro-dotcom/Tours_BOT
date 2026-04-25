Continue Tours_BOT strict continuation.

Task:
Implement first safe runtime slice for operator assignment on custom requests: Assign to me.

Read first:
- docs/CHAT_HANDOFF.md
- docs/OPERATOR_ASSIGNMENT_GATE.md
- docs/ADMIN_OPS_VISIBILITY_GATE.md

Goal:
Allow an authenticated admin/operator to assign an open/custom request to themselves.

Scope:
Custom marketplace requests only.
No bookings assignment yet.

Expected model change:
- Add nullable assigned_operator_id -> users.id
- Add nullable assigned_at timestamp
- Optional assigned_by_user_id -> users.id only if simple/additive
- Alembic migration required if columns are added.

Rules:
- No Mini App changes.
- No My requests privacy changes.
- No booking/payment changes.
- No execution-link changes.
- No identity bridge changes.
- No supplier route changes.
- No close/resolve/reassign/unassign yet.
- Assignment must not change request lifecycle/status in this slice.
- Store internal users.id, not raw Telegram id.
- Display Telegram id/name only through User relationship/summary.

API:
Add narrow protected admin endpoint:
POST /admin/custom-requests/{request_id}/assign-to-me

Behavior:
- actor is authenticated admin/operator user.
- find/map actor Telegram id/admin identity to internal User id using existing admin Telegram context if available.
- if current admin auth is token-only and no actor user can be resolved, fail safely or use an explicit documented fallback only if existing project patterns support it.
- if request unassigned -> assign to actor.
- if already assigned to same actor -> idempotent success.
- if assigned to another operator -> return conflict/blocked for now.
- terminal requests should be blocked unless existing policy says otherwise.

Telegram UI:
In admin request detail screen:
- show Owner: unassigned / assigned operator summary
- if unassigned, show Assign to me button
- if assigned to current operator, show "Assigned to you"
- if assigned to another operator, show owner and no assign button or show blocked state
- no reassign/clear buttons yet.

Tests:
- migration/schema if applicable
- API assign success
- idempotent assign to same actor
- assigned to another actor blocked
- owner appears in admin request list/detail
- Telegram detail shows Assign to me for unassigned
- Telegram assign button updates detail
- Mini App My requests remains user-scoped and unaffected
- supplier routes unchanged

After coding report:
- files changed
- migration id
- API endpoint
- Telegram UI changes
- tests run
- what remains postponed