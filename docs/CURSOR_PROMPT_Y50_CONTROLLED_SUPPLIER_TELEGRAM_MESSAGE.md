You are continuing Tours_BOT after Y49.

Goal:
Implement Y50 — controlled single-channel supplier messaging.

IMPORTANT:
This is the first external side-effect slice.
Keep it narrow, explicit, idempotent, and audited.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md
- docs/SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md
- docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md
- docs/SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md
- docs/SUPPLIER_EXECUTION_TRIGGER_DESIGN.md
- docs/SUPPLIER_EXECUTION_FLOW.md

Scope:
Implement ONE controlled supplier outbound messaging path.

Allowed channel:
- Telegram only

Allowed start:
- explicit admin action only

Add endpoint:
POST /admin/supplier-execution-attempts/{attempt_id}/send-telegram

Allowed behavior:
- require ADMIN_API_TOKEN
- validate attempt exists
- validate parent supplier_execution_request exists
- validate attempt.status is pending
- validate channel_type is telegram or none, depending current model
- require idempotency key/header/body field
- prepare message from explicit request body
- send exactly one Telegram message using existing bot/config patterns if available
- store provider_reference/message id if available
- mark attempt succeeded on confirmed send
- mark attempt failed on send failure
- record error_code/error_message on failure
- never create duplicate send on same idempotency key

Must NOT:
- send automatically
- send from request creation
- send from attempt creation
- send from operator_workflow_intent
- send from operator-decision endpoint
- create RFQ
- create booking/order/payment
- touch Mini App
- create execution links
- modify identity bridge
- notify customers
- fan out to many suppliers
- add workers/retries

Implementation safety:
- fail closed
- no hidden triggers
- one explicit endpoint
- one attempt
- one message
- idempotency mandatory
- audit fields updated

Tests:
- auth required
- missing ADMIN_API_TOKEN matches admin behavior
- unknown attempt 404
- non-pending attempt rejected
- missing idempotency rejected
- send success marks attempt succeeded and stores provider ref
- send failure marks attempt failed and stores error
- repeated same idempotency does not duplicate send
- request creation still does not send
- attempt creation still does not send

Before coding:
1. summarize why Y50 is dangerous
2. list exact files expected to change
3. explain how duplicate sends are prevented
4. confirm no customer-facing changes

After coding:
1. files changed
2. endpoint added
3. tests added/run
4. confirm no hidden triggers
5. confirm request/attempt creation still do not send
6. next safe step