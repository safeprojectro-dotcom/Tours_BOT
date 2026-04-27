You are continuing Tours_BOT after Y46.

Current state:
- execution request exists
- admin trigger exists
- NO execution attempts exist
- NO supplier messaging exists

--------------------------------
🔒 SOURCE OF TRUTH
--------------------------------

Read:

- docs/CHAT_HANDOFF.md
- docs/SUPPLIER_EXECUTION_FLOW.md
- docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md
- docs/SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md
- docs/SUPPLIER_EXECUTION_TRIGGER_DESIGN.md

--------------------------------
🎯 GOAL (Y47)
--------------------------------

Design execution attempt layer.

NO IMPLEMENTATION.

--------------------------------
🧱 TASK
--------------------------------

Create:

- docs/SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md

Define:

1. What is execution attempt:
   - one try to perform supplier interaction
   - tied to supplier_execution_request

2. Attempt lifecycle:
   - created
   - pending
   - in_progress
   - succeeded
   - failed

3. Attempt responsibilities:
   - represent execution step
   - hold external interaction metadata
   - store provider references
   - store error data

4. Attempt MUST NOT:
   - be created by trigger (Y46)
   - be created automatically
   - run without explicit next gate

5. Future behavior (document only):
   - may send supplier message
   - may call external API
   - may retry

6. Separation:
   - request = intention
   - attempt = action

--------------------------------
🚫 HARD CONSTRAINTS
--------------------------------

NO:
- supplier messaging implementation
- API calls
- workers
- booking/order/payment
- Mini App changes
- execution links
- identity bridge
- notifications

--------------------------------
📌 OUTPUT
--------------------------------

Before editing:
- explain why attempts must be separated from trigger

After editing:
- files created
- attempt model defined
- lifecycle defined
- what is forbidden
- next step