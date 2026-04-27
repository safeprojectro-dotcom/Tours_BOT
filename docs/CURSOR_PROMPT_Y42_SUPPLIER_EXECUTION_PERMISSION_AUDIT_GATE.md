You are continuing Tours_BOT after Y38–Y41.

Current accepted gates:
- Y38: Supplier Interaction Design Gate
- Y39: Supplier Entry Points Design
- Y40: Supplier Execution Flow Design
- Y41: Supplier Execution Data Contract Design

Cursor mode:
Plan first, then Agent only for documentation edits.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_INTERACTION_GATE.md
- docs/SUPPLIER_ENTRY_POINTS.md
- docs/SUPPLIER_EXECUTION_FLOW.md
- docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md
- docs/OPERATOR_WORKFLOW_GATE.md
- docs/OPERATOR_DECISION_GATE.md

Goal:
Define Y42 — Supplier Execution Permission & Audit Gate.

Create:
- docs/SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md

Update:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Define:
1. Who may initiate future supplier execution:
   - central admin explicit action
   - authorized operator explicit action
   - authorized system job
   - authenticated external integration

2. Permission rules:
   - assigned operator may record intent
   - recording intent is not execution permission
   - supplier execution needs separate permission
   - admin/operator action must be explicit and auditable

3. Audit requirements:
   - who initiated
   - what entry point was used
   - source entity
   - intent snapshot if used
   - idempotency key
   - validation result
   - attempt/result state
   - error reason if blocked/failed

4. Fail-closed rules:
   - missing permission blocks execution
   - missing source entity blocks execution
   - missing idempotency key blocks execution
   - ambiguous source blocks execution
   - stale/invalid intent snapshot does not auto-refresh into execution

5. Strict separation:
   - operator_workflow_intent is context only
   - operator decision endpoint is not an execution endpoint
   - no hidden trigger from DB update/events

Hard constraints:
- documentation only
- no migrations
- no models
- no schemas
- no app/ changes
- no tests/ changes
- no API changes
- no runtime behavior changes
- no supplier messaging
- no RFQ implementation
- no booking/order/payment mutation
- no Mini App changes
- no execution links
- no identity bridge
- no customer notifications

Before editing:
Explain why permission and audit must be defined before implementation.

After editing:
Report:
- files changed
- permission rules added
- audit fields/rules added
- fail-closed rules
- what remains forbidden
- next safe step