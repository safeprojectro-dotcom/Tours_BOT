Implement Y37.4 — first operator decision runtime slice.

Source of truth:
- docs/OPERATOR_DECISION_GATE.md
- docs/CHAT_HANDOFF.md
- docs/OPERATOR_WORKFLOW_GATE.md
- existing Y36/Y37 assignment + under_review implementation

Goal:
Add the first narrow operator decision for custom marketplace requests after status=under_review.

Scope:
- Add one additive machine-readable operator decision field/model according to OPERATOR_DECISION_GATE.
- Implement only ONE first decision value, preferably need_manual_followup.
- Add protected admin API:
  POST /admin/custom-requests/{request_id}/operator-decision
  with X-Admin-Actor-Telegram-Id
- Allow only if:
  - request exists
  - actor maps to users.id
  - request is assigned to this actor
  - status == under_review
- Idempotent if same decision already set by same actor.
- Telegram admin detail: show decision status and button/menu only when Owner = you and Status = under_review.
- No customer-facing notification.

Do not implement:
- resolve/close
- supplier RFQ send
- bridge creation
- booking/order/payment changes
- reassign/unassign
- Mini App changes
- execution-link changes
- identity bridge changes

Tests:
- API allow/deny matrix
- Telegram button visibility and callback length
- Mini App/My requests privacy regression
- compileall

Stop and report:
- files changed
- endpoint added
- DB/migration status
- exact decision behavior
- blocked states
- tests run