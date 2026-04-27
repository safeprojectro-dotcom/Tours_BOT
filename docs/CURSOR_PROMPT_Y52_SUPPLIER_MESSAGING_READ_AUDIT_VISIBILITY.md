You are continuing Tours_BOT after Y51.

Goal:
Y52 — Supplier Messaging Read/Audit Visibility Implementation.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_MESSAGING_AUDIT_RETRY_DESIGN.md
- docs/SUPPLIER_OUTBOUND_MESSAGING_DESIGN.md
- docs/SUPPLIER_EXECUTION_DATA_CONTRACT.md
- docs/SUPPLIER_EXECUTION_PERMISSION_AUDIT_GATE.md

Scope:
Improve read/admin visibility for Y50 messaging results.

Allowed:
- expose messaging result/audit fields in admin read DTOs
- expose Telegram idempotency evidence
- expose target_supplier_ref / provider_reference / error_code / error_message / status / timestamps
- optionally add minimal audit field if already available in current model

Must NOT:
- send messages
- retry messages
- create attempts
- change request/attempt creation behavior
- add workers
- add auto retry
- touch booking/order/payment
- touch Mini App
- create execution links
- modify identity bridge
- notify customers

Implementation:
- update read schemas/services/routes as needed
- add tests for read visibility
- no outbound I/O

Before coding:
1. summarize Y51 rules
2. list files expected to change
3. explain why this is read-only safe

After coding:
1. files changed
2. fields exposed
3. tests run
4. confirm no retry/no send
5. next safe step