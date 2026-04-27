Y54 — Supplier Manual Retry Implementation is completed.

Current state:
- failed supplier execution attempts can be retried manually
- retry creates a new pending attempt
- retry does NOT send automatically

Endpoint:
POST /admin/supplier-execution-attempts/{attempt_id}/retry

Rules:
- explicit admin action only
- original attempt must be retry-eligible
- new attempt gets next attempt_number
- original attempt is not resent in-place
- Telegram send still requires separate Y50 send endpoint with a new idempotency key

Still forbidden:
- automatic retry
- retry on read
- hidden retry
- reusing old idempotency key to create a new send
- booking/order/payment mutation
- Mini App changes
- execution links
- identity bridge
- customer notifications
- fan-out

Next safe step:
Close supplier execution MVP layer or move to supplier identity/onboarding.