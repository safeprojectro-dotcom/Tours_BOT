# Cursor Prompt - Phase 4 / Step 15

Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/TESTING_STRATEGY.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, `docs/CHAT_HANDOFF.md`, and `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, implement only the post-trip reminder groundwork slice on top of the existing notification preparation, dispatch, outbox, processing, recovery, retry-execution, predeparture reminder, and departure-day reminder foundations.

Goal:
Add the first post-trip reminder groundwork so after-trip customer notifications can be prepared and pushed through the existing `telegram_private` notification lifecycle without introducing scheduler/orchestrator complexity or broader channel expansion yet.

Allowed scope:
- add a minimal post-trip reminder service/worker path for identifying a narrow set of eligible completed trips
- prepare only the first post-trip reminder notification outputs needed for the current notification foundation
- reuse existing notification preparation, dispatch, outbox, processing, recovery, retry-execution, predeparture reminder, and departure-day reminder foundations where appropriate
- preserve explicit and idempotent state transitions
- keep the implementation PostgreSQL-first
- add focused tests for reminder eligibility, repeated-run safety, and compatibility with the current notification pipeline
- keep business rules in the service layer
- keep worker code thin
- keep API/UI layers untouched unless a very small integration point is strictly required

Requirements:
- reuse the existing notification preparation, dispatch, outbox, processing, recovery, retry-execution, predeparture reminder, and departure-day reminder foundations where appropriate
- keep delivery limited to the existing `telegram_private` channel only
- do not add new channels
- do not add group delivery
- do not add Mini App delivery
- do not add waitlist notifications
- do not add handoff notifications
- do not add full scheduler/orchestrator complexity yet
- do not add advanced retry policy tuning yet
- preserve the current Step 8-14 behavior unless a very small compatibility fix is strictly necessary
- keep the aiogram dependency boundary narrow and do not reintroduce broad import coupling into unrelated services/tests

Do not implement yet:
- full production scheduler/orchestrator
- advanced retry framework/policy engine
- group delivery
- Mini App delivery
- waitlist notifications
- handoff notifications
- refund workflow
- advanced admin automation

Before writing code:
1. summarize the current project state
2. list what is already completed in Phase 4
3. identify the exact next safe step and explain why post-trip reminder groundwork is the right next foundation
4. list the repositories, services, workers, schemas, helpers, and tests you will add or extend
5. explain the post-trip reminder eligibility strategy
6. explain the idempotency and repeated-run safety strategy
7. explain what remains postponed

Then generate the code and tests.
