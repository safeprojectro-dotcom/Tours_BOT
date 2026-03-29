# Cursor Prompt — Phase 4 / Step 7

Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/TESTING_STRATEGY.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, `docs/CHAT_HANDOFF.md`, and `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, implement only the first payment-pending reminder worker slice on top of the existing reservation expiry and notification foundations.

Goal:
Add the first due reminder selection/worker path for temporary reservations that are still awaiting payment, without introducing real Telegram delivery or full scheduler/orchestrator complexity.

Allowed scope:
- add reminder eligibility logic for temporary reservations that are still active and awaiting payment
- add a small worker/service slice that selects due reminder candidates and prepares dispatches using the existing notification dispatch layer
- add minimal schemas/helpers for reminder batch results only if needed
- support one narrow reminder case only: payment still pending shortly before reservation expiry
- add focused tests for selection rules, dispatch preparation, and safe repeated execution behavior
- keep business rules in the service layer and keep worker code thin

Requirements:
- reuse the existing reservation expiry and notification preparation/dispatch foundations where appropriate
- keep the implementation PostgreSQL-first
- do not perform real Telegram API delivery yet
- do not add waitlist reminders
- do not add handoff reminders
- do not add predeparture reminders yet
- do not add post-trip reminders yet
- do not add full scheduler/orchestrator complexity yet
- do not add outbox persistence or dispatch-tracking unless it is strictly necessary for the narrow current slice
- keep bot/API/UI layers untouched unless a very small integration point is strictly required
- run the minimal relevant tests first and do not claim broader coverage than what is actually tested

Do not implement yet:
- real notification sending through aiogram or any external provider
- full production scheduler/orchestrator
- waitlist release notifications
- handoff notifications
- group bot behavior
- Mini App UI
- refund workflow
- advanced admin automation

Before writing code:
1. summarize the current project state
2. list what is already completed in Phase 4
3. identify the exact next safe step and explain why it is smaller than broader reminder automation
4. list the services, workers, schemas, repositories, helpers, and tests you will add or extend
5. explain the reminder eligibility rules and repeated-execution/idempotency boundary
6. explain what remains postponed

Then generate the code and tests.
