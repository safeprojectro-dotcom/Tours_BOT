# Cursor Prompt — Phase 2 / Step 2

## Purpose
Implement the next schema slice for the MVP model layer of Tours_BOT.

---

Using `docs/TECH_SPEC_TOURS_BOT.md` and `docs/IMPLEMENTATION_PLAN.md`, implement only Phase 2 / Step 2.

Scope:
- add the next schema slice for the MVP model layer
- create SQLAlchemy models and relationships for:
  - payments
  - waitlist
  - handoffs
  - messages
  - content_items
  - faq / knowledge_base
- add only schema-level enums/constants if needed
- create the next Alembic migration
- keep the design PostgreSQL-first

Requirements:
- extend the existing model layer cleanly
- keep relationships explicit and unambiguous
- add schema-level constraints and indexes where appropriate
- keep timestamps and shared mixins consistent with the current codebase
- think carefully about nullable vs non-nullable fields
- do not add business workflows yet

Do not implement yet:
- booking business logic
- payment business workflows
- waitlist behavior logic
- handoff behavior logic
- Telegram handlers
- Mini App UI
- admin feature workflows
- content publication workflows
- repositories/services beyond the pure model layer

Before writing code:
1. list the models you will add
2. explain the relationships you will create
3. explain which constraints belong to schema level vs later business logic
4. explain what is intentionally postponed to later Phase 2 steps

Then generate the code and migration.
