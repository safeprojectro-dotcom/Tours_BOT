You are continuing Tours_BOT after Y50.

Goal:
Y51 — Supplier Messaging Result Visibility / Audit / Retry Design.

This is DESIGN ONLY.
No implementation.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md
- docs/SUPPLIER_EXECUTION_ATTEMPT_DESIGN.md
- docs/SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md

Create:
- docs/SUPPLIER_MESSAGING_AUDIT_RETRY_DESIGN.md

Define:
1. What admin/operator must see after send:
   - attempt status
   - provider_reference
   - error_code/error_message
   - sent target
   - idempotency key presence
   - timestamps

2. Audit hardening:
   - who sent
   - when
   - which endpoint
   - target supplier/chat
   - result
   - failure reason

3. Retry principles:
   - no automatic retry yet
   - manual retry only after explicit future gate
   - retry must use new idempotency key or defined replay semantics
   - failed attempt should not silently resend

4. Forbidden:
   - auto retry workers
   - hidden retry on read
   - retry from request creation
   - retry from attempt creation
   - retry from operator intent
   - customer notifications
   - booking/payment/Mini App changes

5. Next safe implementation:
   - add read visibility/audit fields where missing
   - no auto retry

After editing:
- files changed
- audit rules
- retry rules
- forbidden behavior
- next safe step