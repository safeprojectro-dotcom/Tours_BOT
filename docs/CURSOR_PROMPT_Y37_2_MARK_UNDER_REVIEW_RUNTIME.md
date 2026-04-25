Continue Tours_BOT after Y37.1 operator workflow gate.

Task:
Implement first safe operator workflow runtime slice:
Mark assigned custom request as under_review.

Read first:
- docs/CHAT_HANDOFF.md
- docs/OPERATOR_WORKFLOW_GATE.md
- docs/OPERATOR_ASSIGNMENT_GATE.md

Scope:
Custom marketplace requests only.

Rules:
- No reassign.
- No unassign.
- No resolve.
- No close.
- No booking/payment changes.
- No Mini App changes.
- No supplier route changes.
- No execution-link changes.
- No identity bridge changes.
- Do not change assignment semantics.
- Do not auto-create bookings/orders/tours.
- Status change must be narrow and explicit.

Expected behavior:
- Add protected admin endpoint:
  POST /admin/custom-requests/{request_id}/mark-under-review
- Actor is resolved using the same Y36 pattern:
  X-Admin-Actor-Telegram-Id -> User -> users.id
- Request must be assigned to the current actor.
- If unassigned -> block safely.
- If assigned to another operator -> block safely.
- If already under_review and assigned to current actor -> idempotent success.
- If terminal/blocked status -> block safely.
- Do not change selected supplier response, bridge, commercial resolution, payments, bookings, or customer identity.

Telegram UI:
In admin request detail:
- If Owner: Assigned to you and status=open, show button:
  Mark under review
- After click:
  status becomes under_review
  detail refreshes
- If unassigned, no Mark under review button.
- If assigned to another operator, no Mark under review button.
- If already under_review, show no duplicate action or show passive state only.
- Keep callbacks compact, no PII in callback_data.

Tests:
- API success assigned-to-me open -> under_review
- API idempotent when already under_review and assigned-to-me
- API blocks unassigned
- API blocks assigned-to-other
- API blocks terminal/non-actionable statuses
- Telegram detail shows Mark under review only when assigned-to-me + open
- Telegram callback updates detail/status
- Mini App My requests remains user-scoped and unaffected
- Supplier routes unchanged if existing tests are available

Run:
python -m compileall app tests/unit/test_api_admin.py tests/unit/test_telegram_admin_moderation_y281.py
python -m pytest tests/unit/test_api_admin.py -k "under_review or assign"
python -m pytest tests/unit/test_telegram_admin_moderation_y281.py -k "admin_ops"

After implementation stop and report:
- files changed
- endpoint added
- Telegram UI changes
- status/lifecycle behavior
- tests run
- postponed items