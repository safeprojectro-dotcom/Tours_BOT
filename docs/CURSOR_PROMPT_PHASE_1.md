# Cursor Prompt — Phase 1

## Purpose
This file stores the approved prompts used for Phase 1 implementation of Tours_BOT.

It is a working reference for:
- project bootstrap
- backend skeleton
- configuration
- PostgreSQL setup
- Alembic initialization
- health endpoints
- local bootstrap refinement

---

## Prompt 1 — Phase 1 / Step 1

Using `docs/TECH_SPEC_TOURS_BOT.md` and `docs/IMPLEMENTATION_PLAN.md`, implement only the first execution step of Phase 1.

Scope:
- backend project skeleton
- settings/config structure
- PostgreSQL setup
- SQLAlchemy base
- Alembic initialization
- /health and /healthz endpoints
- modular folder layout

Do not implement yet:
- Telegram bot handlers
- Mini App UI
- booking logic
- payment logic
- admin business features
- content publication features

Before writing code:
1. list files to be created
2. explain why
3. list assumptions

Then generate the code.

---

## Prompt 2 — Phase 1 / Step 2

Using `docs/TECH_SPEC_TOURS_BOT.md` and `docs/IMPLEMENTATION_PLAN.md`, continue only with the next safe part of Phase 1.

Scope:
- verify and refine `.gitignore`
- verify `.env.example`
- refine `README.md` with local bootstrap instructions
- refine deployment/bootstrap notes for local PostgreSQL
- verify Alembic foundation and local migration workflow
- do not implement business models yet
- do not implement Telegram handlers
- do not implement Mini App UI
- do not implement booking or payment logic

Before making changes:
1. list what is already correct
2. list what is missing
3. explain what should be created manually vs by code generation

Then generate the changes.

---

## Phase 1 Status
- Step 1: completed
- Step 2: completed

## Notes
Phase 1 established:
- backend skeleton
- local project environment
- PostgreSQL-first setup
- Alembic foundation
- health endpoints
- bootstrap docs