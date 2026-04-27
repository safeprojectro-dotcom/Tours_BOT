You are continuing Tours_BOT after Y38 and Y39.

Current accepted gates:
- Y38: Supplier Interaction Design Gate
- Y39: Supplier Entry Points Design

Cursor mode:
Plan first, then Agent only for documentation edits.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_INTERACTION_GATE.md
- docs/SUPPLIER_ENTRY_POINTS.md
- docs/OPERATOR_WORKFLOW_GATE.md
- docs/OPERATOR_DECISION_GATE.md

Goal:
Define Y40 — Supplier Execution Flow Design.

Create:
- docs/SUPPLIER_EXECUTION_FLOW.md

Update:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Define:
1. Future supplier execution flow stages:
   - explicit entry point
   - validation
   - execution request record / audit record
   - supplier action attempt
   - result recording
   - operator/admin review state if needed

2. Clear distinction:
   - operator intent = decision data
   - entry point = start signal
   - execution flow = controlled action pipeline

3. Required safety invariants:
   - idempotency
   - auditability
   - retry safety
   - no hidden triggers
   - fail-closed behavior
   - explicit permissions

4. What execution flow may eventually do:
   - prepare supplier contact action
   - send supplier request/message only in future implementation
   - record supplier response only in future implementation

5. What it must NOT do now:
   - no supplier messaging
   - no RFQ implementation
   - no booking/order/payment
   - no Mini App changes
   - no execution links
   - no identity bridge
   - no customer notifications

Hard constraints:
- documentation only
- no app/ changes
- no tests/ changes
- no migrations
- no API changes
- no runtime behavior changes

Before editing:
Explain why Y40 is needed after Y38/Y39.

After editing:
Report:
- files changed
- execution flow stages defined
- safety invariants
- what remains forbidden
- next safe step