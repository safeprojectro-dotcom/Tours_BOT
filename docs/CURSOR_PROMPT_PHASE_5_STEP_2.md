# Cursor Prompt — Phase 5 / Step 2

Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/TESTING_STRATEGY.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, `docs/CHAT_HANDOFF.md`, `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, and `docs/MINI_APP_UX.md`, implement only the first Mini App UI slice: foundation + catalog + filters.

Goal:
Add the first real Mini App implementation slice for catalog browsing and filters, based on the UX definition in `docs/MINI_APP_UX.md`, without expanding into reservation/payment UI yet.

Allowed scope:
- add the Mini App foundation/skeleton needed for Phase 5 UI work
- implement catalog browsing
- implement filters
- implement tour list/card browsing
- bind the UI only to already existing read/preparation service capabilities
- keep the implementation mobile-first and aligned with `docs/MINI_APP_UX.md`
- add focused tests if there is testable non-UI logic or endpoint behavior associated with this slice

Requirements:
- do not implement reservation creation UI yet
- do not implement payment UI yet
- do not implement Mini App booking flow yet
- do not implement waitlist flow
- do not implement handoff workflow
- do not add group delivery
- do not expand bot/payment backend scope unless a minimal integration point is strictly necessary
- keep business rules in the existing service layer
- do not duplicate booking/payment logic in the Mini App layer
- keep scope limited to foundation, catalog, filters, and tour browsing

Do not implement yet:
- reservation UI flow
- payment UI flow
- waitlist workflow
- handoff workflow
- group behavior
- Mini App help/operator backend expansion beyond minimal placeholders if needed
- unrelated admin/content expansions

Before writing code:
1. summarize the current project state
2. list what is already completed in Phase 4 and Phase 5 Step 1
3. identify the exact next safe step and explain why catalog + filters is the right first Mini App implementation slice
4. list the files, modules, UI components, endpoints, services, and tests you will add or extend
5. explain how the Mini App catalog and filters map to current implemented backend/service capabilities
6. explain what remains postponed
7. explain any assumptions

Then generate the code and tests.