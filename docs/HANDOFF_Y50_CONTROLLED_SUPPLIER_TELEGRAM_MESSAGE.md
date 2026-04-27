Y50 — Controlled Single-Channel Supplier Telegram Messaging is completed.

Current state:
- supplier_execution_request exists
- supplier_execution_attempt exists
- one explicit admin endpoint can send one Telegram supplier message for one attempt
- no automatic sends exist

Endpoint:
POST /admin/supplier-execution-attempts/{attempt_id}/send-telegram

Rules:
- ADMIN_API_TOKEN required
- explicit admin action only
- pending attempt only
- idempotency required
- one attempt = one controlled send
- success/failure is recorded on the attempt
- provider/message reference is stored when available

Still forbidden:
- automatic messaging
- request-created sends
- attempt-created sends
- intent-triggered sends
- operator-decision sends
- RFQ creation
- booking/order/payment mutation
- Mini App changes
- execution links
- identity bridge
- customer notifications
- fan-out
- workers/retries

Next safe step:
Y51 — messaging result visibility / audit hardening, or retry design gate.