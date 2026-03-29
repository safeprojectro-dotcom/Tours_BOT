# Cursor Prompt — Phase 4 / Step 4

Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, and `docs/CHAT_HANDOFF.md`, implement only the reservation expiry worker slice.

Goal:
Add the first reservation expiry automation slice for temporary reservations that were not paid in time.

Allowed scope:
- add the worker/service logic that finds expired temporary reservations
- update reservation/order state safely for expired unpaid reservations
- restore seats back to the related tour when appropriate
- keep the implementation PostgreSQL-first
- keep business logic in service layer, not in bot/api layer

Requirements:
- expire only reservations that are still eligible for expiry
- do not affect already paid orders
- do not affect already cancelled/finalized orders incorrectly
- restore seats safely and consistently
- keep logic idempotent
- add tests for expiry behavior
- keep route/handler/UI layers untouched unless a minimal integration point is strictly necessary

Do not implement yet:
- reminder workers
- waitlist release logic
- handoff workflow
- group behavior
- Mini App UI
- refund workflow
- advanced admin automation

Before writing code:
1. list the services, repositories, workers, and tests you will add or extend
2. explain the expiry eligibility rules
3. explain the seat restoration rules
4. explain the idempotency strategy
5. explain what remains postponed

Then generate the code and tests.