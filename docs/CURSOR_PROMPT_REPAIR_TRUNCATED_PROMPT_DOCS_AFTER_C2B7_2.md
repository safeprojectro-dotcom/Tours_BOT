# CURSOR_PROMPT_REPAIR_TRUNCATED_PROMPT_DOCS_AFTER_C2B7_2

Ты продолжаешь проект Tours_BOT.

## Cursor mode

Agent.

This is a docs-only cleanup step.

Do not modify app/, tests/, alembic/, mini_app/, runtime code, schemas, services, routes, handlers, constants.

Only inspect and repair docs/CURSOR_PROMPT_*.md and related docs/HANDOFF_*.md if needed.

---

## Problem

Three local untracked CURSOR_PROMPT files are truncated and unsafe to reuse:

1. docs/CURSOR_PROMPT_ADMIN_COVER_REAPPROVAL_AFTER_REPLACEMENT_C2B7_2_DESIGN.md
2. docs/CURSOR_PROMPT_ADMIN_COVER_REAPPROVAL_OK_PHOTO_C2B7_2_IMPLEMENTATION.md
3. docs/CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_GENERATE_PACKAGING_BUTTON_C2B2.md

Known issue:

- fenced code blocks are opened and not closed;
- documents stop mid-section;
- wording may say “add/implement” for features that are already implemented;
- this can mislead future agents.

Important: these files are currently untracked. Do not assume Git history can restore them.

---

## Current project truth

C2B2:

- generate_packaging_draft Telegram workflow was already implemented earlier.
- There is/should be a handoff:
  - docs/HANDOFF_ADMIN_OPERATOR_WORKFLOW_GENERATE_PACKAGING_BUTTON_C2B2_TO_NEXT_STEP.md
- There is/should be docs sync:
  - docs/CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_C2B2_DOCS_SYNC.md

C2B7.1:

- PUT /admin/supplier-offers/{offer_id}/cover implemented and deployed.
- commit exists:
  - feat: add admin supplier offer cover replacement endpoint
- Production smoke passed.

C2B7.2:

- Design/decision record exists or should exist as handoff:
  - docs/HANDOFF_ADMIN_COVER_REAPPROVAL_AFTER_REPLACEMENT_C2B7_2_DESIGN.md
- If implementation is not actually completed in code, do not claim it is implemented.
- If implementation is completed, mark implementation prompt as archive/implemented and point to the final commit/handoff.
- If uncertain, state “design accepted / implementation pending” rather than pretending.

---

## Task

Repair the three truncated prompt docs safely.

For each file:

### A. Close broken fenced code blocks

Ensure all ``` blocks are closed.

### B. Add a clear status banner at top

Use one of:

```md
> Status: ARCHIVE / already implemented. Do not run as an implementation prompt.
```

or (design-only archive):

```md
> Status: ARCHIVE — historical Plan-mode design prompt. Current truth: docs/HANDOFF_….md
```

### C. Fix misleading wording

Replace imperative “add / implement / now add” with past tense or “historical goal”, and point to **`docs/HANDOFF_*.md`** (and tests/code pointers only as documentation, without editing code).

### D. Optional tail sections

Short **Shipped summary** or **Pointers** (file paths only) are OK if they prevent re-running obsolete tasks.

### E. HANDOFF files

Edit **`docs/HANDOFF_*.md`** only if something is factually wrong; prefer leaving handoffs as source of truth.

---

## Done criteria

- No unclosed ` ``` ` fences in the three repaired prompts.
- Each repaired file has a **status banner** under the title.
- Agents are not instructed to implement C2B2 or C2B7.2 from these prompts without reading HANDOFF first.