Continue Tours_BOT strict continuation.

Task:
Create docs-only design gate for operator assignment on custom requests (RFQ).

Context:
Y35 introduced:
- admin read-only visibility
- Telegram admin UI
- customer summary layer

Operators can see requests but cannot act on them.

Goal:
Design safe assignment model for custom requests.

Scope:
Custom requests only (NOT bookings yet).

Rules:
- Docs only.
- No runtime code.
- No migrations unless justified.
- No booking/payment changes.
- No Mini App changes.
- No execution-link changes.
- Preserve user privacy model.

Design must include:

1. Current state
- requests have status but no owner

2. Assignment model
- assigned_operator_id (Telegram user id)
- unassigned vs assigned

3. States
- open (unassigned)
- assigned
- in_progress (optional future)
- resolved (future)
- closed (future)

4. Allowed transitions
- open → assigned
- assigned → reassigned
- assigned → unassigned (optional)

5. UI (Telegram)
- Assign to me
- Reassign
- Show current owner

6. Permissions
- only admin/operator can assign
- no self-service user actions

7. Audit
- who assigned
- when assigned

8. Fail-safe
- cannot assign if request not visible
- cannot break existing flows

9. First safe runtime slice
- Assign to me only
- No reassign yet
- No close/resolve yet

10. Tests required
- assignment works
- assignment visible in UI
- no effect on Mini App

Create:
docs/OPERATOR_ASSIGNMENT_GATE.md

Update:
docs/CHAT_HANDOFF.md

Stop after design.