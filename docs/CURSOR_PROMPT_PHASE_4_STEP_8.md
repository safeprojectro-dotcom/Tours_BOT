Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/TESTING_STRATEGY.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, `docs/CHAT_HANDOFF.md`, and `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, implement only the first real `telegram_private` notification delivery slice on top of the existing notification preparation, dispatch, and reminder groundwork.

Goal:
Add the first real `telegram_private` notification delivery path without expanding into group delivery, Mini App delivery, waitlist/handoff notifications, or advanced queue/scheduler complexity.

Allowed scope:
- add a minimal delivery service or adapter for `telegram_private` only
- send already prepared notification dispatches through the Telegram private channel only
- support the currently existing notification groundwork only:
  - notification preparation outputs
  - notification dispatch envelopes
  - payment-pending reminder outputs
- add any minimal schemas/helpers needed for delivery results if strictly necessary
- add focused tests for delivery behavior, safe failure handling, and clear service boundaries
- keep business rules in the service layer and keep worker/bot wiring thin

Requirements:
- reuse the existing notification preparation, dispatch, and payment-pending reminder foundations where appropriate
- keep the implementation PostgreSQL-first
- keep delivery limited to `telegram_private`
- do not add group delivery
- do not add Mini App delivery
- do not add waitlist notifications
- do not add handoff notifications
- do not add predeparture reminders yet
- do not add post-trip reminders yet
- do not add full scheduler/orchestrator complexity yet
- do not add advanced outbox persistence or queueing unless it is strictly necessary for the narrow current slice
- keep API/UI layers untouched unless a very small integration point is strictly required
- implement delivery through a dedicated adapter/service boundary, not directly inside worker logic
- keep the Telegram sending dependency mockable/testable
- run the minimal relevant tests first and do not claim broader coverage than what is actually tested

Do not implement yet:
- group delivery
- Mini App delivery
- waitlist notifications
- handoff notifications
- full production scheduler/orchestrator
- advanced outbox/queue persistence
- group bot behavior
- Mini App UI
- refund workflow
- advanced admin automation

Before writing code:
1. summarize the current project state
2. list what is already completed in Phase 4
3. identify the exact next safe step and explain why it is smaller than broader notification delivery rollout
4. list the services, workers, schemas, adapters, helpers, and tests you will add or extend
5. explain the boundary between notification preparation/dispatch/reminder selection and real Telegram private delivery
6. explain what remains postponed

Then generate the code and tests.