You are continuing Tours_BOT after Y43.

Current state:
- Supplier execution persistence exists (Y43)
- No execution logic exists
- No supplier messaging
- No API visibility yet

--------------------------------
🔒 SOURCE OF TRUTH
--------------------------------

Read:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_INTERACTION_GATE.md
- docs/SUPPLIER_ENTRY_POINTS.md
- docs/SUPPLIER_EXECUTION_FLOW.md
- docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md
- docs/SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md

--------------------------------
🎯 GOAL (Y44)
--------------------------------

Add READ-ONLY admin visibility for supplier execution records.

--------------------------------
🧱 TASK
--------------------------------

Add admin API endpoints:

1. GET /admin/supplier-execution-requests
   - list requests
   - basic fields only
   - filters: status, source_entity_type

2. GET /admin/supplier-execution-requests/{id}
   - full request detail
   - include attempts

3. NO mutation endpoints

--------------------------------
📌 RULES
--------------------------------

- reuse ADMIN_API_TOKEN auth
- no execution triggering
- no supplier messaging
- no RFQ logic
- no booking/order/payment
- no Mini App changes
- no execution links
- no identity bridge
- no notifications

--------------------------------
🧠 DATA
--------------------------------

Use:
- supplier_execution_requests
- supplier_execution_attempts

Expose:
- id
- status
- source_entity
- intent snapshot
- created_at
- attempts (read-only)

--------------------------------
🧪 TESTS
--------------------------------

Add:
- unit tests for endpoints
- auth tests
- read-only verification

--------------------------------
⚠️ HARD CONSTRAINT
--------------------------------

This must NOT:
- change runtime behavior
- trigger execution
- modify data
- introduce side effects

--------------------------------
📌 OUTPUT
--------------------------------

Before coding:
- explain why read-only is safe

After coding:
- files changed
- endpoints added
- tests added
- confirmation no side effects
- next step