Y49 — Supplier Outbound Messaging Design is accepted and synced.

Source of truth:
- docs/SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Current rule:

Outbound messaging is:
- the first real external side effect
- allowed ONLY inside execution attempt

Messaging requires:
- explicit permission
- idempotency
- audit trail

Messaging MUST NOT be triggered by:
- operator_workflow_intent
- request creation
- attempt creation alone

Still forbidden:
- automatic messaging
- hidden triggers
- RFQ/booking/payment changes
- Mini App changes
- execution links
- identity bridge
- customer notifications (unless explicitly defined later)

Next safe step:
Y50 — controlled messaging implementation (single channel, idempotent, audited).