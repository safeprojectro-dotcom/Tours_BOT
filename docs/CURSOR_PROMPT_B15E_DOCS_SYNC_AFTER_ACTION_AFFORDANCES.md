# CURSOR_PROMPT_B15E_DOCS_SYNC_AFTER_ACTION_AFFORDANCES

## Context

B15E implementation is already done.

Current implementation changed:
- `app/schemas/admin_publishing_console.py`
- `app/services/admin_publishing_console_service.py`
- `tests/unit/test_admin_publishing_console.py`

Focused test passed:
- `python -m pytest tests/unit/test_admin_publishing_console.py -q`
- Result: `8 passed`

Current issue:
Docs are not fully synced yet. Do not change application behavior in this prompt.

## Goal

Complete B15E documentation sync only.

## Required docs changes

Create:
- `docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`
- `docs/CURSOR_PROMPT_B15E_DOCS_SYNC_AFTER_ACTION_AFFORDANCES.md`

Update:
- `docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/HANDOFF_B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN_TO_NEXT_STEP.md`

The original prompt file already exists:
- `docs/CURSOR_PROMPT_B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`

Keep it and do not delete it.

## Required B15E doc contents

`docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md` must include:

1. Objective:
   - B15E adds read-only action affordance metadata to `GET /admin/publishing-console`.

2. Endpoint:
   - `GET /admin/publishing-console`
   - remains read-only
   - no mutation/send/retry/publish/scheduler

3. New schema/model:
   - `AdminPublishingConsoleActionAffordanceRead`
   - added `actions` field on `AdminPublishingConsoleItemRead`

4. Action fields:
   - `code`
   - `label`
   - `kind`
   - `enabled`
   - `requires_confirmation`
   - `danger_level`
   - `admin_path`
   - `method`
   - `implemented`
   - `disabled_reason`
   - `source`

5. Sources:
   - supplier-offer actions are projected from existing `operator_workflow.actions`
   - tour-promotion actions are console read-only / future hints

6. Safety:
   - action affordances are metadata only
   - endpoint does not call mutation services
   - no Telegram send/publish/retry
   - no bridge/catalog/execution-link creation from the console read endpoint
   - no Layer A changes
   - no Mini App routing changes

7. Tour promotion behavior:
   - safe/read affordances only
   - future draft/publish affordance marked `implemented=false`, `enabled=false`

8. Tests:
   - `python -m pytest tests/unit/test_admin_publishing_console.py -q`
   - `8 passed`

9. Next steps:
   - B15F template/source/channel expansion read model
   - B15E2 explicit action execution design only if approved
   - B15G guarded auto-publish design only after explicit approval

## Update B15D doc

In `docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md`, add a short note:
- B15E extends B15D by adding read-only action affordances.
- B15D readiness fields remain unchanged and backward-compatible.

## Update CHAT_HANDOFF

Add concise B15E bullet:
- B15E done: publishing console now exposes read-only action affordances derived from operator workflow / console hints.
- Endpoint remains read-only.
- Tests: `test_admin_publishing_console.py` — 8 passed.
- Next: B15F or B15E2 design.

## Update OPEN_QUESTIONS_AND_TECH_DEBT

Mark B15E as done.
Keep future items:
- B15F template/source/channel expansion.
- B15E2 explicit action execution design only if approved.
- B15G guarded auto-publish only after explicit design approval.

## Update handoff

Update:
`docs/HANDOFF_B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN_TO_NEXT_STEP.md`

It must record:
- B15E implemented.
- Endpoint remains read-only.
- Action metadata is additive.
- Supplier offer actions come from existing operator workflow.
- Tour promotion actions are safe/read or future-disabled.
- Tests passed: 8.
- Next recommended step: B15F or B15E2 only after explicit approval.

## Non-goals

Do not change:
- app code
- tests
- schemas
- services
- migrations
- production data
- Telegram posts
- Layer A
- Mini App routing

## After completion report

Return:

1. Files changed.
2. Docs created/updated.
3. Confirmation that app code was not changed by this docs-sync prompt.
4. `git status --short`.
5. `git diff --stat`.

---

## Documentation sync completion record

- **Completed:** 2026-05-09 (docs-only; **no** application code changes in this sync).
- **Created:** [`docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`](B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md).
- **Updated:** [`docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md`](B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md), [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md), [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md), [`docs/HANDOFF_B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN_TO_NEXT_STEP.md`](HANDOFF_B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN_TO_NEXT_STEP.md).