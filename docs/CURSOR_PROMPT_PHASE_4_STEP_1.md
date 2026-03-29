# Cursor Prompt — Phase 4 / Step 1

Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, and `docs/CHAT_HANDOFF.md`, implement only the first payment-entry slice after temporary reservation creation.

Goal:
Add the first payment-entry flow for a temporary reservation, without implementing payment reconciliation yet.

Allowed scope:
- add payment-entry logic for an already created temporary reservation
- create the minimal payment record/session foundation tied to an order
- return a multilingual private-bot response that clearly explains the next payment step
- keep handlers thin and service-driven
- keep payment initiation separate from payment confirmation/reconciliation

Requirements:
- use service layer for payment-entry orchestration
- validate that the reservation/order is still valid for payment entry
- do not mark payment as paid yet
- do not implement webhook reconciliation yet
- do not implement refunds yet
- do not implement waitlist logic
- do not implement handoff workflow
- do not implement group behavior
- do not implement Mini App UI
- do not add payment business logic directly to handlers

Do not implement yet:
- payment webhook reconciliation
- payment success confirmation workflow
- refund workflow
- reminder workers
- expiry worker execution
- waitlist actions
- handoff lifecycle
- group bot behavior
- Mini App UI

Before writing code:
1. list the handlers, services, repositories, and schemas you will add or extend
2. explain the boundary between payment entry and payment reconciliation
3. explain what remains postponed
4. explain any assumptions about payment session creation and reservation validity

Then generate the code and tests.