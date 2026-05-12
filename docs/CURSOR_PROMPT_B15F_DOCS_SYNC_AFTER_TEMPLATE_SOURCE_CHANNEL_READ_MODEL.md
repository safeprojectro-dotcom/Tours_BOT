# CURSOR_PROMPT_B15F_DOCS_SYNC_AFTER_TEMPLATE_SOURCE_CHANNEL_READ_MODEL

## Context

B15F implementation is already done.

Current implementation changed:
- `app/schemas/admin_publishing_console.py`
- `app/services/admin_publishing_console_service.py`
- `tests/unit/test_admin_publishing_console.py`

Focused test passed:
- `python -m pytest tests/unit/test_admin_publishing_console.py -q`
- Result: `8 passed`

Current issue:
Docs were not fully synced yet. Do not change application behavior in this prompt.

The original B15F prompt required docs, so complete the documentation sync now.

## Goal

Complete B15F documentation sync only.

## Required docs changes

Create:
- `docs/B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`
- `docs/CURSOR_PROMPT_B15F_DOCS_SYNC_AFTER_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`

Update:
- `docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md`
- `docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/HANDOFF_B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL_TO_NEXT_STEP.md`

The original prompt file already exists:
- `docs/CURSOR_PROMPT_B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`

Keep it and do not delete it.

## Required B15F doc contents

`docs/B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md` must include:

1. Objective:
   - B15F extends read-only `GET /admin/publishing-console` with source/template/channel/media metadata.

2. Endpoint:
   - `GET /admin/publishing-console`
   - remains read-only
   - no mutation/send/retry/publish/scheduler/template editing/channel selection

3. New read-model sections:
   - source metadata
   - template/source metadata
   - channel metadata
   - media policy metadata
   - future template/channel affordances

4. New/added fields, including the actual implemented field names from schema:
   - source metadata fields
   - template metadata fields
   - channel metadata fields
   - media policy fields
   - template_actions
   - channel_actions
   - future capability hint model if implemented

5. Supplier offer semantics:
   - source is supplier offer
   - template is supplier offer showcase
   - preview/read path uses review-package where available
   - channel derives from configured showcase channel/settings
   - media policy summarizes current review-package/media state

6. Tour promotion semantics:
   - source is tour
   - template is tour promotion
   - uses placeholder/read-model semantics where full template source is not yet implemented
   - no supplier-offer-specific behavior falsely applied

7. Safety:
   - metadata only
   - endpoint does not call mutation services
   - no Telegram send/publish/retry
   - no bridge/catalog/execution-link creation from console read
   - no Layer A changes
   - no Mini App routing changes
   - no migrations

8. Tests:
   - `python -m pytest tests/unit/test_admin_publishing_console.py -q`
   - `8 passed`

9. Next steps:
   - B15F2 template editor design/read model only if explicitly approved
   - B15F3 channel selector design/read model only if explicitly approved
   - B15E2 explicit action execution design only if approved
   - B15G guarded auto-publish design only after explicit approval

## Update B15D doc

In `docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md`, add a short note:
- B15F extends the publishing console read model with source/template/channel/media metadata.
- B15D readiness fields remain unchanged and backward-compatible.

## Update B15E doc

In `docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`, add a short note:
- B15F adds template/channel/source metadata beside B15E action affordances.
- B15E actions remain metadata only and are not execution endpoints.

## Update CHAT_HANDOFF

Add concise B15F bullet:
- B15F done: publishing console now exposes source/template/channel/media read metadata and future-disabled template/channel hints.
- Endpoint remains read-only.
- Tests: `test_admin_publishing_console.py` — 8 passed.
- Next: B15F2/B15F3/B15E2 only after explicit approval, or B15G design later.

## Update OPEN_QUESTIONS_AND_TECH_DEBT

Mark B15F as done.
Keep future items:
- B15F2 template editor design/read model only if explicitly approved.
- B15F3 channel selector design/read model only if explicitly approved.
- B15E2 explicit action execution design only if approved.
- B15G guarded auto-publish only after explicit design approval.

## Update handoff

Update:
`docs/HANDOFF_B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL_TO_NEXT_STEP.md`

It must record:
- B15F implemented.
- Endpoint remains read-only.
- Source/template/channel/media metadata is additive.
- Supplier offer semantics.
- Tour promotion semantics.
- Tests passed: 8.
- Next recommended step options.

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

## Doc artifacts produced by this sync

| Artifact | Role |
|----------|------|
| [`docs/B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`](B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md) | B15F design record (fields, semantics, safety, tests). |
| Updates to [`docs/B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md`](B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW.md), [`docs/B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md`](B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN.md), [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md), [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md), [`docs/HANDOFF_B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL_TO_NEXT_STEP.md`](HANDOFF_B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL_TO_NEXT_STEP.md) | Cross-links and status lines. |