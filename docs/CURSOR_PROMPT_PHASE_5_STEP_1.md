Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/TESTING_STRATEGY.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, `docs/CHAT_HANDOFF.md`, and `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, implement only the Mini App UX definition step before Phase 5 UI work.

Goal:
Define the Mini App UX in `docs/MINI_APP_UX.md` so the Phase 5 UI can be built against an explicit screen map, CTA hierarchy, and state model without prematurely expanding into Flet UI implementation.

Allowed scope:
- create or update `docs/MINI_APP_UX.md`
- define the screen map for catalog, filters, tour card, booking, payment, my bookings, language/settings, and help/operator entry points
- define CTA hierarchy, loading states, empty states, error states, and reservation timer states
- define help and handoff entry points from the Mini App experience
- align the UX definition with the current Phase 2-4 service capabilities and explicit postponed items
- map each Mini App screen to current implemented backend/service capabilities where possible
- keep the work documentation-first and avoid UI code or API expansion in this step

Requirements:
- do not implement Flet UI yet
- do not add Mini App auth/init endpoints yet
- do not add Mini App booking/payment UI yet
- do not expand bot, payment, waitlist, or handoff code in this step
- keep the UX definition aligned with the existing architecture and current Phase 2-4 capabilities
- explicitly mark still-postponed behaviors instead of inventing unsupported flows
- base every screen and action only on already implemented capabilities or explicitly mark them as future/not yet implemented

Do not implement yet:
- Flet UI implementation
- Mini App API delivery changes
- waitlist workflow implementation
- handoff workflow implementation
- group delivery
- content/admin expansions unrelated to Mini App UX definition

Before writing code:
1. summarize the current project state
2. list what is already completed in Phase 4
3. identify the exact next safe step and explain why Mini App UX definition is the right bridge into Phase 5
4. list the docs or files you will add or extend
5. explain the proposed screen map and CTA hierarchy
6. explain what remains explicitly postponed before UI implementation
7. explain what remains postponed

Then generate the documentation only.