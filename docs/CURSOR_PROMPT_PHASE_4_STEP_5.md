# Cursor Prompt — Phase 4 / Step 5

Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, `docs/CHAT_HANDOFF.md`, and `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, implement only the reminder/notification groundwork slice.

Goal:
Add the first notification foundation for the existing booking/payment lifecycle without expanding into broader workflow automation.

Allowed scope:
- add notification/reminder preparation services
- add notification event/type definitions if needed
- add safe selection logic for existing lifecycle states that already exist
- prepare multilingual notification payload/message content for:
  - temporary reservation created
  - payment pending
  - payment confirmed
  - reservation expired
- add tests for the preparation/selection logic
- keep business logic in service layer
- keep bot/API/UI layers untouched unless a minimal integration point is strictly necessary

Requirements:
- use the current repositories, schemas, and service layer
- do not add waitlist notification logic
- do not add handoff notification logic
- do not add group behavior
- do not add Mini App UI
- do not add refund workflow
- do not add advanced scheduling/orchestration yet
- do not duplicate message logic that already exists in the bot layer unless a shared notification foundation is clearly needed

Do not implement yet:
- waitlist release logic
- handoff lifecycle
- group bot behavior
- Mini App UI
- refund workflow
- advanced admin automation
- full production-grade scheduler/orchestrator complexity

Before writing code:
1. list the services, schemas, helpers, and tests you will add or extend
2. explain the boundary between notification preparation and actual delivery/orchestration
3. explain what lifecycle points will be covered now
4. explain what remains postponed
5. explain any assumptions about multilingual message preparation

Then generate the code and tests.