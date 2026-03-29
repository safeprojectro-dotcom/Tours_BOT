Using `docs/TECH_SPEC_TOURS_BOT.md` and `docs/IMPLEMENTATION_PLAN.md`, implement only Phase 2 / Step 5.

Scope:
- add the next safe service-layer slice on top of the current repositories and read services
- implement only simple business-adjacent read/preparation services needed by later booking and payment flows
- keep the design PostgreSQL-first
- keep logic explicit and limited

Allowed areas:
- catalog filtering/preparation helpers
- language-aware tour read preparation
- basic order summary preparation
- basic payment summary preparation
- simple read-side aggregation helpers for later flows

Requirements:
- services may compose repositories and existing read services
- services must not create reservations yet
- services must not change booking/payment states
- services must not decrement seats
- services must not implement waitlist behavior
- services must not implement handoff behavior
- services must not add Telegram or Mini App logic
- keep outputs schema-oriented and safe for later API/bot layers

Do not implement yet:
- reservation creation/expiry workflow
- payment reconciliation workflow
- waitlist queue/release workflow
- handoff lifecycle workflow
- Telegram handlers
- Mini App UI
- admin workflows
- content publication workflows

Before writing code:
1. list the services/helpers you will add
2. explain why they are safe at this stage
3. explain what is intentionally postponed
4. explain any assumptions

Then generate the code.