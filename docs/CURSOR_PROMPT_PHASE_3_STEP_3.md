Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, and `docs/CHAT_HANDOFF.md`, implement only Phase 3 / Step 3.

Goal:
Add the next private-chat slice that prepares the user for reservation without actually creating a reservation yet.

Allowed scope:
- extend private bot flow from tour browsing into reservation-preparation inputs
- support safe collection/preparation of:
  - selected tour
  - seat count
  - boarding point choice
- show a multilingual reservation-preparation summary before any real reservation exists
- keep handlers thin and service-driven
- add or extend bot-layer services only where needed for read-only preparation
- use the existing repositories, schemas, read services, and preparation services

Requirements:
- do not create a reservation yet
- do not write booking state yet
- do not decrement seats
- do not start payment flow
- do not implement waitlist actions
- do not implement handoff workflow
- do not implement group behavior
- do not implement Mini App UI
- do not add business workflow logic to handlers

Implementation constraints:
- preserve existing `/start`, `/language`, `/tours`, browsing flow, and `tour_<CODE>` behavior
- preserve multilingual behavior
- keep reservation-preparation separate from actual booking workflow
- add tests for the new preparation behavior if there is already a bot-layer test pattern

Before writing code:
1. list the handlers, bot services, schemas, and helper files you will add or extend
2. explain the boundary between reservation-preparation and real reservation creation
3. explain what remains postponed
4. explain any assumptions about seat count and boarding point selection

Then generate the code.
