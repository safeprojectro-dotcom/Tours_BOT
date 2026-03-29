# Cursor Prompt — Phase 4 / Step 11

Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/TESTING_STRATEGY.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, `docs/CHAT_HANDOFF.md`, and `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, implement only the retry / recovery groundwork slice for failed or stuck notification outbox entries.

Goal:
Add the first retry/recovery foundation for notification outbox processing so failed or stuck entries can later be retried safely, without introducing full scheduler/orchestrator complexity yet.

Allowed scope:
- add service/worker logic for identifying:
  - failed outbox entries that are eligible for retry
  - processing outbox entries that appear stale/stuck
- add minimal state transitions needed for safe retry preparation or recovery
- keep the implementation PostgreSQL-first
- keep business rules in the service layer
- add focused tests for retry eligibility, stale-processing recovery, and repeated execution safety
- keep worker code thin
- keep API/UI layers untouched unless a minimal integration point is strictly necessary

Requirements:
- reuse the existing outbox persistence and processing foundations where appropriate
- do not add group delivery
- do not add Mini App delivery
- do not add waitlist notifications
- do not add handoff notifications
- do not add full scheduler/orchestrator complexity yet
- do not add advanced retry policy tuning yet
- preserve the current Step 8–10 behavior unless a very small compatibility fix is strictly necessary
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
3. identify the exact next safe step and explain why retry/recovery groundwork is the right next foundation
4. list the models, repositories, services, workers, schemas, helpers, and tests you will add or extend
5. explain the retry/recovery eligibility strategy
6. explain the stale-processing recovery strategy
7. explain what remains postponed

Then generate the code and tests.