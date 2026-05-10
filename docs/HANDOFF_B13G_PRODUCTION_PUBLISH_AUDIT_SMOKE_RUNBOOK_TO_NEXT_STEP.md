
---

## HANDOFF name

`HANDOFF_B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK_TO_NEXT_STEP.md`

---

## HANDOFF content

```md
# HANDOFF_B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK_TO_NEXT_STEP

## Status

**B13G finalized (docs / ops only).** Canonical runbook: **[`docs/B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md`](B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md)**. Docs sync: **`CURSOR_PROMPT_B13G_DOCS_FINALIZE`** — **`CHAT_HANDOFF`**, **`B13C`**, this handoff, **`CURSOR_PROMPT_B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK`** completion.

## Project

Tours_BOT — showcase publish audit production smoke and verification.

## Step

B13G — Production publish smoke with audit verification **runbook** (operator checklist, not product code).

## Checkpoint (before ops runs the runbook)

- **B13D:** table **`supplier_offer_showcase_publish_attempts`**, migration **`20260531_29`** in repo.
- **B13E:** **`publish`** writes attempt rows (`requested` → `provider_sent` → `persisted` | `failed`).
- **B13F:** **`showcase_publish_attempts_review`** on **`GET …/review-package`**, Telegram compact audit block.

## Runbook purpose

Give operators a **safe, repeatable** path to confirm post-deploy: Alembic includes B13D revision, **`review-package`** exposes attempt history, and (only if approved) a **controlled** publish creates a traceable **`persisted`** or **`failed`** attempt. Full detail: **[`docs/B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md`](B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md)**.

## Docs changed (finalize pass)

| Path | Role |
|------|------|
| [`docs/B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md`](B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md) | Main runbook (unchanged in finalize if already present) |
| [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) | B13G completed bullet |
| [`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md) | B13G pointer §9 + §12 + Related |
| [`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md) | Related → B13G (from earlier B13G authoring) |
| [`docs/CURSOR_PROMPT_B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md`](CURSOR_PROMPT_B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md) | Docs-finalize completion note |
| This file | Handoff wrapper |

## Migration reminder (Railway / production shell)

```bash
python -m alembic upgrade head
python -m alembic current
```

**Expect:** `current` reports **head** revision chain that **includes** **`20260531_29`** (B13D attempt table). If newer migrations exist after **`20260531_29`**, **head** may be a later id — **must** still be **≥** **`20260531_29`**. When **`20260531_29`** is literally repo **head**, output matches **`20260531_29 (head)`**.

## Read-only checks (no publish)

- **`GET /admin/supplier-offers/{offer_id}/review-package`** with **`ADMIN_API_TOKEN`**: response **must** include **`showcase_publish_attempts_review`** (`total_returned`, `items`, `preview_notice`).
- Optional: confirm **`items`** reflect known history after any prior publish.

## Controlled publish policy

**Only** with explicit ops/product approval and a suitable offer/environment (**staging first**). **`POST …/publish`** (or Telegram C2B8B) creates a **real** channel post. Follow **[`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md)** then **`B13G`** runbook §4.

## Stop conditions

Abort or escalate when: migration fails or **`current`** does not include **`20260531_29`**; **`review-package`** missing **`showcase_publish_attempts_review`**; unexpected errors during optional publish smoke; orphan-post / DB boundary concerns per **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)** §2/§7.

## Operator-owned next actions

1. Deploy latest commit.
2. Run **`alembic upgrade head`** and **`current`** on Railway (or release phase).
3. Run **read-only** checks.
4. **Only with explicit approval**, run **controlled** publish smoke and re-verify audit rows.

## Non-goals

B13G **does not** add code, tests, migrations, retry/resend, idempotency, dedicated list endpoint, new channels, Mini App, booking, payment, or orders. Doc authoring **does not** call mutating endpoints or Telegram.

## Likely forward

- **B13H+:** manual retry/resend **design** (docs-first, product gate).
- Optional **`GET …/showcase-publish-attempts`** (see B13F handoff).
```

---

## Notes (wrapper)

Finalize prompt: **[`docs/CURSOR_PROMPT_B13G_DOCS_FINALIZE.md`](CURSOR_PROMPT_B13G_DOCS_FINALIZE.md)**. Implementation prompt: **[`docs/CURSOR_PROMPT_B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md`](CURSOR_PROMPT_B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md)**. Runbook: **[`docs/B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md`](B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md)**. Prior: **[`docs/HANDOFF_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE_TO_NEXT_STEP.md`](HANDOFF_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE_TO_NEXT_STEP.md)**.
