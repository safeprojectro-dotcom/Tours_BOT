Y50 — Controlled Supplier Telegram Messaging is implemented and synced.

Current state:

- supplier_execution_request exists
- supplier_execution_attempt exists
- controlled Telegram messaging exists

Messaging rules:

- only via explicit admin endpoint
- only for pending attempt
- requires idempotency
- exactly one send per idempotency key
- success/failure recorded

Idempotency:

- supplier_execution_attempt_telegram_idempotency
- UNIQUE (attempt_id, idempotency_key)

Still forbidden:

- automatic messaging
- intent-triggered messaging
- request-triggered messaging
- attempt-creation-triggered messaging
- fan-out
- retries without explicit design
- RFQ / booking / Mini App / execution links / identity bridge / customer notifications

Next safe step:

Y51 — audit hardening / retry strategy design (no automatic retries yet).