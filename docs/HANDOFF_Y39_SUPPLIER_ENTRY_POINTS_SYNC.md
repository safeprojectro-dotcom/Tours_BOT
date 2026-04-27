Y39 — Supplier Entry Points Design is completed and synced.

Source of truth:
- docs/SUPPLIER_INTERACTION_GATE.md
- docs/SUPPLIER_ENTRY_POINTS.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Current rule:
Supplier interaction may start only from explicit entry points:
- admin explicit action
- scheduled/background job
- authenticated external trigger
- manual operator “do” action separate from intent recording

Forbidden:
- operator_workflow_intent change as trigger
- operator-decision endpoint as executor
- implicit ORM/event side effects
- customer/Mini App starts unless future gate explicitly approves

Future implementation tickets must name one Y39 entry family/surface and define idempotency + audit.

No supplier execution is implemented yet.