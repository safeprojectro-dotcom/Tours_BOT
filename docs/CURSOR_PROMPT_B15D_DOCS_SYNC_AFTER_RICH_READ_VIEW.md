# CURSOR_PROMPT_B15D_DOCS_SYNC_AFTER_RICH_READ_VIEW

## Context

B15D Admin Publishing Console richer read/admin view implementation is already done.

Current implementation files changed:
- `app/schemas/admin_publishing_console.py`
- `app/services/admin_publishing_console_service.py`
- `tests/unit/test_admin_publishing_console.py`

Focused test already passed:
- `python -m pytest tests/unit/test_admin_publishing_console.py -q`
- Result: `8 passed`

Current issue:
The implementation is not yet docs-synced. Do not change app behavior in this prompt.

## Goal

Complete B15D documentation sync only.

## Required docs changes

Create:
- `docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md`
- `docs/CURSOR_PROMPT_B15D_DOCS_SYNC_AFTER_RICH_READ_VIEW.md`

Update:
- `docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/HANDOFF_B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW_TO_NEXT_STEP.md`

The handoff file already exists as untracked from the implementation prompt. Keep it and update it with actual implementation results.

## Required B15D doc contents

`docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md` must include:

1. Objective:
   - B15D extends read-only Admin Publishing Console with richer readiness/action guidance.

2. Endpoint:
   - `GET /admin/publishing-console`
   - still read-only
   - no publish/send/retry/scheduler/mutation

3. Additive response fields:
   - readiness_summary
   - readiness_level
   - conversion_target_kind
   - conversion_target_url
   - cta_safety_status
   - primary_blocker
   - blocker_codes
   - next_action_code
   - next_action_label
   - admin_action_path
   - preview_path
   - source_status_summary
   - audit_hint

4. Source of truth:
   - uses existing review-package / conversion status / B15C CTA readiness / operator workflow / tour catalog visibility.
   - console aggregates and summarizes existing truth; it does not own business rules.

5. Example semantics:
   - ready supplier offer candidate
   - blocked supplier offer missing execution link
   - tour promotion candidate

6. Tests:
   - `python -m pytest tests/unit/test_admin_publishing_console.py -q`
   - `8 passed`

7. Non-goals:
   - no auto-publish
   - no scheduler
   - no template editor
   - no channel selector
   - no media rendering/storage
   - no Layer A changes
   - no Mini App routing changes

8. Next step:
   - B15E: explicit console action affordances/design, still guarded and no auto-publish unless separately scoped.

## Update handoff

`docs/HANDOFF_B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW_TO_NEXT_STEP.md` must record:

- B15D implemented.
- Endpoint remains read-only.
- New fields are additive.
- Tests passed: 8.
- Next recommended step: B15E action affordances/design.
- Safety confirmations.

## Update CHAT_HANDOFF

Add a concise B15D bullet after B15C closure / B15B console notes:

- B15D done: richer publishing console read model with readiness, blockers, exact-tour CTA safety, conversion target, next action/admin paths.
- No mutation/send/scheduler.
- Tests: `test_admin_publishing_console.py` — 8 passed.
- Next: B15E.

## Update OPEN_QUESTIONS_AND_TECH_DEBT

Mark B15D as done and keep future B15E/B15F/B15G as follow-ups:
- B15E action affordances/design.
- B15F templates/source expansion.
- B15G guarded auto-publish only after explicit design approval.

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

- **Completed:** 2026-05-09 (docs-only; no application code changes in this sync).
- **Artifacts:** [`docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md`](B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md) created; [`docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md`](B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md), [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md), [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md), [`docs/HANDOFF_B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW_TO_NEXT_STEP.md`](HANDOFF_B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW_TO_NEXT_STEP.md) updated.