# CURSOR_PROMPT_O1A_PRODUCTION_IAM_BASELINE_SCHEMA_REVIEW

You are continuing the existing Tours_BOT project.

This is NOT a new project, NOT a rewrite, and NOT a runtime implementation step.

## Cursor mode

Agent

## Block

O1A — Production IAM Baseline Design / Schema Review

## Execution mode

Docs-only schema review / design review.

## Why this step exists

O1-DG is complete and defines the production role, identity, access, supplier/driver operations and boarding design gate.

Before implementing any IAM tables, driver access, supplier access, ticket QR, manifest, or boarding scan logic, we must inspect the existing codebase and document what identity/auth pieces already exist.

This step must prevent duplicate identity models.

Do not implement IAM yet.
Do not add migrations.
Do not add endpoints.
Do not change runtime code.

---

## Goal

Create a production IAM baseline schema review document answering:

1. What user/identity/auth models already exist?
2. What supplier/supplier-admin auth already exists?
3. How customer Telegram identity currently works.
4. How Mini App identity currently works.
5. How admin authentication currently works.
6. What can be reused for production IAM.
7. What must be added later.
8. What must NOT be duplicated.
9. What is the safest implementation sequence after this review.

---

## Source docs to inspect first

Inspect:

1. `docs/O1_PRODUCTION_ROLE_IDENTITY_ACCESS_BOARDING_DESIGN_GATE.md`
2. `docs/CHAT_HANDOFF.md`
3. `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
4. `docs/IMPLEMENTATION_PLAN.md`
5. `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
6. `docs/TECH_SPEC_TOURS_BOT.md`
7. `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
8. `docs/DEMO1_PHYSICAL_TELEGRAM_DEMO_SMOKE_PLAYBOOK.md`

---

## Code/schema areas to inspect

Search and inspect current identity/auth-related code.

Use PowerShell equivalents if needed.

```bash
grep -R "class User" -n app tests || true
grep -R "telegram_user_id" -n app tests docs | head -400 || true
grep -R "Supplier" -n app/models app/schemas app/services app/repositories app/api tests | head -500 || true
grep -R "supplier_admin" -n app tests docs | head -400 || true
grep -R "credential" -n app tests docs | head -400 || true
grep -R "ADMIN_API_TOKEN" -n app tests docs | head -300 || true
grep -R "X-Admin-Token" -n app tests docs | head -300 || true
grep -R "Authorization" -n app/api app/services tests | head -400 || true
grep -R "Mini App" -n app mini_app tests docs | head -400 || true
grep -R "init_data" -n app mini_app tests docs | head -300 || true
grep -R "primary_telegram_user_id" -n app tests docs || true
grep -R "role" -n app/models app/schemas app/services app/repositories app/api tests | head -400 || true
grep -R "admin_auth" -n app tests docs || true
grep -R "get_admin" -n app tests docs | head -300 || true
grep -R "require_admin" -n app tests docs | head -300 || true