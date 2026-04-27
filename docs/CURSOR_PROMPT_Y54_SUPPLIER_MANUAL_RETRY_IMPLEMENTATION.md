You are continuing Tours_BOT after Y53.

Goal:
Y54 — Supplier Manual Retry Implementation.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_MANUAL_RETRY_DESIGN.md
- docs/SUPPLIER_MESSAGING_AUDIT_RETRY_DESIGN.md
- docs/SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md

Scope:
Implement manual retry support only.

Preferred model from Y53:
- retry creates a NEW supplier_execution_attempt
- do NOT resend failed attempt in-place by default
- retry is explicit admin action only
- retry does NOT send automatically

Add endpoint:
POST /admin/supplier-execution-attempts/{attempt_id}/retry

Allowed behavior:
- require ADMIN_API_TOKEN
- require X-Admin-Actor-Telegram-Id
- validate original attempt exists
- validate original attempt is failed or retry-eligible
- validate parent supplier_execution_request is still valid
- require retry_reason
- create a new pending supplier_execution_attempt
- link original_attempt_id -> retry_attempt_id in audit/log/persistence according to current architecture
- return new attempt

Must NOT:
- send Telegram message
- call supplier APIs
- reuse old idempotency key
- retry automatically
- retry on read
- change request/attempt creation behavior
- touch booking/order/payment
- touch Mini App
- create execution links
- modify identity bridge
- notify customers
- fan out

Tests:
- auth required
- missing actor rejected
- unknown attempt 404
- succeeded attempt rejected
- pending attempt rejected unless explicitly allowed by design
- failed attempt creates new pending retry attempt
- retry attempt has next attempt_number
- retry does not send Telegram
- retry does not mutate original attempt
- retry linkage/audit is stored or explicitly documented if not persisted yet

Before coding:
1. summarize Y53 retry model
2. list files expected to change
3. explain why retry creation is safe without sending

After coding:
1. files changed
2. endpoint added
3. retry linkage/audit approach
4. tests run
5. confirm no sends / no auto retry
6. next safe step