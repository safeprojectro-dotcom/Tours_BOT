# Cursor Prompt — Phase 4 / Step 6

Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, `docs/CHAT_HANDOFF.md`, and `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, implement only the next notification dispatch groundwork slice.

Goal:
Add the first notification dispatch/enqueue foundation on top of the existing notification preparation layer, without introducing full scheduling/orchestration complexity.

Allowed scope:
- add a minimal notification dispatch or enqueue foundation
- support safe preparation for delivery of already defined notification event types
- add persistence or dispatch-tracking support only if strictly needed
- keep the design service-layer driven
- keep bot/API/UI layers untouched unless a very small integration point is required

Requirements:
- use the existing notification preparation layer
- do not implement marketing messaging
- do not implement waitlist notifications
- do not implement handoff notifications
- do not implement group behavior
- do not implement Mini App UI
- do not add advanced scheduler/orchestrator complexity yet
- keep logic explicit and testable

Do not implement yet:
- full production scheduler
- waitlist release notifications
- handoff notifications
- group bot behavior
- Mini App UI
- refund workflow
- advanced admin automation

Before writing code:
1. list the services, schemas, repositories, helpers, and tests you will add or extend
2. explain the boundary between notification preparation and dispatch/enqueue logic
3. explain what lifecycle points will remain covered now
4. explain what remains postponed
5. explain any assumptions about notification persistence or dispatch tracking

Then generate the code and tests.