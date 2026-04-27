You are continuing Tours_BOT after Y52.

Goal:
Y53 — Supplier Messaging Manual Retry Design Gate.

This is DESIGN ONLY.
No implementation.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_MESSAGING_AUDIT_RETRY_DESIGN.md
- docs/SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md
- docs/SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md

Create:
- docs/SUPPLIER_MANUAL_RETRY_DESIGN.md

Define:
1. Manual retry principle:
   - retry must be explicit admin action
   - no automatic retry
   - no hidden retry on read
   - no retry from request/attempt creation

2. Retry model:
   - failed attempt should not be resent in-place by default
   - preferred model: create a new attempt for retry
   - each retry send requires a new idempotency key
   - same idempotency key means replay/no duplicate send

3. Preconditions:
   - original attempt failed or is in retry-eligible state
   - parent request still valid
   - admin permission required
   - target must be confirmed again
   - message text must be confirmed again

4. Audit:
   - original_attempt_id
   - retry_attempt_id
   - retry_requested_by
   - retry_reason
   - timestamp
   - idempotency key

5. Forbidden:
   - background retry worker
   - retry by reading detail page
   - retry from operator_workflow_intent
   - retry from request creation
   - retry from attempt creation
   - retry without new explicit admin action
   - customer notifications
   - booking/payment/Mini App changes

6. Next safe implementation:
   - add manual retry endpoint or flow only after this gate
   - still no auto retry

After editing:
- files changed
- retry model
- preconditions
- audit requirements
- forbidden behavior
- next safe step