You are continuing Tours_BOT after Y44.

Current state:
- persistence exists (Y43)
- admin read visibility exists (Y44)
- NO execution exists
- NO supplier messaging exists

--------------------------------
🔒 SOURCE OF TRUTH
--------------------------------

Read:

- docs/CHAT_HANDOFF.md
- docs/SUPPLIER_INTERACTION_GATE.md
- docs/SUPPLIER_ENTRY_POINTS.md
- docs/SUPPLIER_EXECUTION_FLOW.md
- docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md
- docs/SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md

--------------------------------
🎯 GOAL (Y45)
--------------------------------

Design FIRST controlled execution trigger.

NO IMPLEMENTATION YET.

--------------------------------
🧱 TASK
--------------------------------

Create:

- docs/SUPPLIER_EXECUTION_TRIGGER_DESIGN.md

Define:

1. FIRST allowed trigger:
   - admin explicit action only

2. What trigger does:
   - creates supplier_execution_request
   - validates input
   - stores audit data
   - DOES NOT contact supplier yet

3. Trigger MUST NOT:
   - send messages
   - call supplier APIs
   - create RFQ
   - create bookings/orders/payments
   - touch Mini App
   - create execution links
   - modify identity bridge
   - notify customers

4. Required checks:
   - ADMIN_API_TOKEN auth
   - source entity exists
   - idempotency key present
   - request not already active
   - fail closed

5. Output of trigger:
   - DB record only
   - status = pending or validated
   - audit trail

6. Relationship:
   - uses Y41 data contract
   - follows Y42 permission rules
   - uses Y39 entry point definition

--------------------------------
🚫 HARD CONSTRAINTS
--------------------------------

NO:
- execution runtime
- supplier messaging
- RFQ logic
- booking/order/payment
- Mini App changes
- notifications
- side effects

--------------------------------
📌 OUTPUT
--------------------------------

Before editing:
- explain why trigger must be separated from execution

After editing:
- files created
- trigger rules defined
- safety checks defined
- what is explicitly forbidden
- next step