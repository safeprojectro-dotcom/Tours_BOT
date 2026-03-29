# Cursor Prompt — Phase 4 / Step 2

Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, and `docs/CHAT_HANDOFF.md`, implement only the payment reconciliation slice after payment entry.

Goal:
Consume verified provider/webhook results and update payments and orders idempotently, without implementing refunds, waitlist, handoff, workers, or Mini App UI.

Allowed scope:
- add payment reconciliation logic for an existing payment/session tied to an order
- support verified provider result ingestion in a provider-agnostic way
- update payment and order state idempotently
- keep handlers thin and service-driven if bot/private layer needs read-only status messaging
- keep reconciliation separate from payment entry

Requirements:
- use service layer for payment reconciliation orchestration
- validate that the incoming payment result maps to a known payment/session
- update payment state safely and idempotently
- update order state safely and idempotently when payment is confirmed
- do not create refunds
- do not implement waitlist logic
- do not implement handoff workflow
- do not implement reminder or expiry workers
- do not implement group behavior
- do not implement Mini App UI
- do not add reconciliation business logic directly to handlers

Do not implement yet:
- refund workflow
- reminder workers
- expiry worker execution
- waitlist actions
- handoff lifecycle
- group bot behavior
- Mini App UI
- admin payment workflows beyond what is strictly needed for reconciliation

Before writing code:
1. list the services, repositories, schemas, and handlers you will add or extend
2. explain the boundary between payment entry and payment reconciliation
3. explain the idempotency strategy
4. explain what remains postponed
5. explain any assumptions about provider result format

Then generate the code and tests.