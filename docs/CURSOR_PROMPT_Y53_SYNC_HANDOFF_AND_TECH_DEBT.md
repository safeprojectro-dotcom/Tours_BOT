Sync Y53 into continuity docs only.

Read:
- docs/SUPPLIER_MANUAL_RETRY_DESIGN.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Update only:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Requirements:
1. Add Y53 as accepted design-only checkpoint.
2. State manual retry only.
3. State no automatic retry, no hidden retry, no retry on read.
4. State preferred model: create a new retry attempt, not in-place resend by default.
5. State each retry send requires a new idempotency key.
6. State same attempt_id + idempotency_key remains replay/no duplicate.
7. State next safe step: Y54 manual retry implementation if needed.

No code changes.