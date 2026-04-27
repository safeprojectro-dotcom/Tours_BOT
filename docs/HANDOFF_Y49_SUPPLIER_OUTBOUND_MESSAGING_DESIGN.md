Y49 — Supplier Outbound Messaging Design is completed.

Current state:

- request exists
- attempt exists
- messaging NOT implemented

Rule:

Outbound messaging:
- can ONLY happen inside execution attempt
- requires explicit permission
- requires idempotency
- requires audit

Forbidden:
- messaging in trigger
- messaging in request
- messaging in attempt creation

Next step:
Y50 — safe messaging implementation (controlled, idempotent).