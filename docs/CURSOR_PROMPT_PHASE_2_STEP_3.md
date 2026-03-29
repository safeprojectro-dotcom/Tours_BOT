Using `docs/TECH_SPEC_TOURS_BOT.md` and `docs/IMPLEMENTATION_PLAN.md`, implement only Phase 2 / Step 3.

Scope:
- add the repository layer for the current MVP schema foundation
- add Pydantic schemas for the current model set
- keep the design PostgreSQL-first
- keep repository methods simple and data-oriented
- add only safe CRUD/query foundations needed by later phases

Model areas in scope:
- users
- tours
- tour_translations
- boarding_points
- orders
- payments
- waitlist
- handoffs
- messages
- content_items
- knowledge_base

Requirements:
- keep repositories separate from business workflows
- keep Pydantic schemas separate from ORM models
- use explicit typing
- keep the code modular and consistent with the current structure
- do not add service/business logic yet

Do not implement yet:
- booking workflow logic
- payment workflow logic
- waitlist behavior logic
- handoff behavior logic
- Telegram handlers
- Mini App UI
- admin workflows
- content publication workflows

Before writing code:
1. list the repositories and schemas you will add
2. explain the repository boundaries
3. explain what belongs to repositories vs later service layer
4. explain what is intentionally postponed

Then generate the code.