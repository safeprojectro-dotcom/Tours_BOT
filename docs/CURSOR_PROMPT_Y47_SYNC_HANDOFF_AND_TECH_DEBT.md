You are continuing Tours_BOT after creating:

- docs/SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md

Task:
Sync Y47 into continuity docs only.

Read:
- docs/SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Update only:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Requirements:
1. Add Y47 as accepted design-only checkpoint.
2. State request != attempt.
3. State attempts are NOT created by Y46 trigger.
4. State attempts require a separate explicit step.
5. State no supplier messaging/API/workers/RFQ/booking/payment/Mini App/links/identity/notifications.
6. State next safe step is safe attempt creation, still no outbound messaging.

No code changes.

After editing, report:
- files changed
- exact Y47 continuity text added
- next safe step