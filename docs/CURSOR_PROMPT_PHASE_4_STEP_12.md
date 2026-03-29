# Cursor Prompt — Phase 4 / Step 12

Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/TESTING_STRATEGY.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, `docs/CHAT_HANDOFF.md`, and `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, implement only the retry execution groundwork slice for recovered or pending notification outbox entries.

Goal:
Add the first retry execution foundation for recovered or retryable notification outbox entries without introducing full scheduler/orchestrator complexity or an advanced retry policy engine.

Allowed scope:
- add service/worker logic for safely reprocessing recovered or retryable pending outbox entries
- support narrow retry execution on top of the current outbox processing and recovery foundations
- preserve explicit and idempotent state transitions
- keep the implementation PostgreSQL-first
- add focused tests for retry execution safety, repeated-run behavior, and compatibility with existing outbox processing
- keep business rules in the service layer
- keep worker code thin
- keep API/UI layers untouched unless a very small integration point is strictly required

Requirements:
- reuse the existing outbox persistence, outbox processing, and outbox recovery foundations where appropriate
- do not add group delivery
- do not add Mini App delivery
- do not add waitlist notifications
- do not add handoff notifications
- do not add full scheduler/orchestrator complexity yet
- do not add advanced retry policy tuning yet
- preserve the current Step 8–11 behavior unless a very small compatibility fix is strictly necessary
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
3. identify the exact next safe step and explain why retry execution groundwork is the right next foundation
4. list the repositories, services, workers, schemas, helpers, and tests you will add or extend
5. explain the retry execution eligibility strategy
6. explain the idempotency and repeated-run safety strategy
7. explain what remains postponed

Then generate the code and tests.
