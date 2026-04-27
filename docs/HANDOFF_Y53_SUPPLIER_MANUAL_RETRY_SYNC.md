Y53 — Supplier Manual Retry Design is accepted and synced.

Current rule:
Retry is manual only.

Forbidden:
- automatic retry
- hidden retry
- retry on read
- retry from operator intent
- retry from request creation
- retry from attempt creation

Preferred retry model:
- create a new retry attempt
- do not resend failed attempt in-place by default
- require new idempotency key for the new send
- same attempt_id + idempotency_key means replay/no duplicate

Required audit:
- original_attempt_id
- retry_attempt_id
- retry_requested_by
- retry_reason
- timestamp
- idempotency key

Next safe step:
Y54 — manual retry implementation, if needed.