Y52 — Supplier Messaging Read/Audit Visibility is completed.

Current state:
- Y50 controlled Telegram send exists
- Y52 improves admin read visibility for messaging result/audit
- no retry execution exists
- no automatic retry exists

Admin reads expose:
- attempt status
- target_supplier_ref
- provider_reference
- error_code/error_message
- idempotency evidence
- timestamps where available

Still forbidden:
- auto retry
- hidden retry on read
- send from request/attempt creation
- booking/order/payment mutation
- Mini App changes
- execution links
- identity bridge
- customer notifications

Next safe step:
Y54 — manual retry implementation, if needed (after Y53 design gate; see `docs/SUPPLIER_MANUAL_RETRY_DESIGN.md` and `docs/HANDOFF_Y53_SUPPLIER_MANUAL_RETRY_DESIGN.md`).