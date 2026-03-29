# Cursor Prompt — Phase 2 / Step 1

## Purpose
Implement the first safe slice of the domain model layer for Tours_BOT.

---

Using `docs/TECH_SPEC_TOURS_BOT.md` and `docs/IMPLEMENTATION_PLAN.md`, implement only Phase 2 / Step 1.

Scope:
- define the first real SQLAlchemy domain models for the MVP
- add status enums/constants needed for the model layer
- add model relationships
- create the first meaningful Alembic migration
- keep the design PostgreSQL-first
- include only schema/data-model foundation, not business workflows

Include only these model areas if they are ready for the first safe slice:
- users
- tours
- tour_translations
- boarding_points
- orders

Do not implement yet:
- booking business logic
- payment logic
- waitlist behavior
- handoff behavior
- Telegram handlers
- Mini App UI
- admin feature logic
- content publication logic

Before writing code:
1. list the models you will create
2. explain why these are the safest first slice
3. list assumptions about statuses and relationships
4. explain what is intentionally postponed to later Phase 2 steps

Then generate the code and migration.