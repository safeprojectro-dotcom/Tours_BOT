Continue Tours_BOT strict continuation.

Identity and My requests are now fixed.
Evidence:
- has_identity=True
- POST /mini-app/custom-requests returns 201
- GET /mini-app/custom-requests/{id} returns 200
- My requests displays request #13

Remaining UX issue:
Opening/request detail or booking bridge preparation for a fresh custom request calls:
GET /mini-app/custom-requests/{id}/booking-bridge/preparation
and backend returns 404.

This is expected when no active execution/booking bridge exists yet.
Task:
Handle this expected 404 as a user-friendly non-error state in Mini App UI.

Rules:
- Do NOT change identity bridge.
- Do NOT change booking/payment Layer A.
- Do NOT change RFQ/supplier semantics.
- Do NOT create fake bridge/linkage.
- Do NOT change backend contracts unless strictly necessary.
- Keep fail-closed for identity.

Goal:
When booking-bridge/preparation returns 404 for a custom request:
- do not show technical error
- show normal message:
  "No booking step is available yet. Your request is waiting for operator review."
- keep request detail visible
- keep user able to return to My requests/catalog/help
- do not retry aggressively

Investigate:
- mini_app api client method for custom request booking bridge preparation
- custom request detail UI
- where 404 is handled/rendered

Checks:
- python -m compileall app mini_app
- focused tests if existing patterns allow

Report:
- files changed
- migrations none
- root cause
- tests run