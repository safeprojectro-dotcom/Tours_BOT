# CURSOR_PROMPT_B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK

You are working on Tours_BOT.

Create B13G: Production publish smoke with audit verification runbook.

This is a docs / ops-readiness step.

Do not change app code.
Do not change tests.
Do not run production mutations.
Do not publish anything.

## Current checkpoint

Closed and pushed:

- B13D — showcase publish attempt audit foundation
  - migration/table exists
  - FK retention ON DELETE RESTRICT
- B13E — publish path writes attempt audit rows
  - requested -> provider_sent -> persisted
  - failed on send/missing message id
  - no retry/resend
  - no idempotency enforcement
- B13F — admin read surface
  - review-package includes `showcase_publish_attempts_review`
  - Telegram admin card shows compact publish audit block
  - no dedicated endpoint in MVP

Important:

B13D added a migration. Production/Railway must run:

```bash
python -m alembic upgrade head
python -m alembic current
```

Expect `current` to include revision from `alembic/versions/20260531_29_supplier_offer_showcase_publish_attempts.py`.

## Deliverable

- New runbook: **[`docs/B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md`](B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md)** — deploy/migration gate, read-only `review-package` check, audit field semantics, optional controlled E2E publish smoke, non-goals, cross-links.

## Completion constraints (agent)

- **Docs only** — no app code, no tests, no production mutations, no publish executed from agent context.

## Completion (B13G runbook — created)

**Created:** `docs/B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md` as above.

**Cross-links:** Runbook links `ADMIN_SHOWCASE_PUBLISH_RUNBOOK`, B13C, B13F handoff, `CHAT_HANDOFF`.

**Agent:** Did not modify application code or tests; did not run production commands.

---

## Completion (B13G — docs finalized)

**Synced:** [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) (B13G bullet), [`docs/HANDOFF_B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK_TO_NEXT_STEP.md`](HANDOFF_B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK_TO_NEXT_STEP.md), [`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md) (B13G pointer).

**Unchanged:** [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) — no new item for this slice.

**Finalize agent:** Docs only — no code, tests, migrations, publish, mutating HTTP, or Telegram calls.