Y47 — Supplier Execution Attempt Design is accepted and synced.

Source of truth:
- docs/SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Current rule:
supplier_execution_request != supplier_execution_attempt.

Request:
- created by Y46 admin trigger
- stores validated intent/context/audit
- does not mean supplier was contacted

Attempt:
- future execution unit
- one concrete try to perform supplier interaction
- must be created only by a separate explicit step
- is NOT created by the Y46 trigger
- is NOT automatic

Still forbidden:
- supplier messaging
- supplier API calls
- workers
- RFQ implementation
- booking/order/payment mutation
- Mini App changes
- execution links
- identity bridge
- customer/supplier notifications
- operator-decision behavior changes

Next safe step:
Y48 — safe attempt creation, still no outbound messaging.