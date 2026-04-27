You are continuing Tours_BOT after Y48.

Current state:
- execution request exists
- attempt exists
- NO outbound messaging exists
- NO supplier communication exists

--------------------------------
🔒 SOURCE OF TRUTH
--------------------------------

Read:

- docs/CHAT_HANDOFF.md
- docs/SUPPLIER_EXECUTION_FLOW.md
- docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md
- docs/SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md
- docs/SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md

--------------------------------
🎯 GOAL (Y49)
--------------------------------

Design supplier outbound messaging.

NO IMPLEMENTATION.

--------------------------------
🧱 TASK
--------------------------------

Create:

- docs/SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md

Define:

1. What outbound messaging is:
   - actual supplier contact
   - first real external side effect

2. Where messaging belongs:
   - ONLY inside execution attempt
   - NEVER in trigger
   - NEVER in request creation

3. Messaging MUST require:
   - explicit attempt
   - explicit permission
   - idempotency
   - audit trail

4. Messaging MUST NOT:
   - be automatic
   - be triggered by intent
   - be triggered by request creation
   - be triggered by attempt creation alone

5. Define allowed future channels:
   - telegram
   - email
   - api

6. Define safety:
   - retry rules (future)
   - failure recording
   - no duplicate sends

--------------------------------
🚫 HARD CONSTRAINTS
--------------------------------

NO:
- implementation
- sending real messages
- API calls
- workers
- booking/order/payment changes
- Mini App changes
- execution links
- identity bridge
- notifications to customer

--------------------------------
📌 OUTPUT
--------------------------------

Before editing:
- explain why messaging is the most dangerous step

After editing:
- files created
- messaging rules
- safety constraints
- what is forbidden
- next step