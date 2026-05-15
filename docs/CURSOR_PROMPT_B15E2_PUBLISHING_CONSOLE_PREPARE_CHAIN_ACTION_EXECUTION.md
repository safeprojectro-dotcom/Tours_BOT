# CURSOR_PROMPT_B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_ACTION_EXECUTION

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoints:

- 9e4b8d docs: record prepare conversion chain production smoke
- fd4e25d feat: expose prepare conversion chain action affordances
- f8f146f feat: add guarded prepare conversion chain admin endpoint

Closed:
- B16D2C — guarded admin POST endpoint for prepare_conversion_chain
- B16D2D — read model/action affordance metadata
- B16D2E — Railway production smoke passed with note

Now implement:

# B15E2 — Publishing Console Action Execution for prepare_conversion_chain

## Goal

Allow the admin publishing console to execute the existing guarded action:

POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain

through a publishing-console-specific admin action endpoint or existing publishing console action execution mechanism, if one already exists.

This must execute ONLY the internal prepare_conversion_chain action.

It must NOT execute Telegram publish/send/retry.

---

# 1. Required behavior

Add a controlled publishing console execution path for action:

code: prepare_conversion_chain

The publishing console already exposes action metadata/read affordances from B16D2D.

Now implement the execution bridge so an admin can trigger the guarded B16D2C service path from the publishing console.

Required:

1. Admin auth required.
2. idempotency_key required.
3. confirm=true required for live execution.
4. dry_run supported.
5. Execution must delegate to the same service/endpoint logic used by B16D2C:
   - Preferred: call PrepareConversionChainExecutionService.execute(...) directly from a thin admin route/service boundary.
   - Or reuse existing route helper if the project already has one.
6. Response should reuse AdminPrepareConversionChainExecutionResultRead or compatible existing schema.
7. No duplicated business logic in publishing console route/service.
8. No Telegram I/O.
9. No hidden publish.
10. No Layer A order/payment/reservation mutation.

---

# 2. Route shape

Before coding, inspect existing publishing console routes and action execution patterns.

If there is an existing generic action execution endpoint, extend it narrowly.

If not, add a narrow endpoint such as one of these, choosing the style that best matches the current project:

Option A:
POST /admin/publishing-console/actions/prepare-conversion-chain

Body:
{
  "supplier_offer_id": 12,
  "idempotency_key": "...",
  "confirm": true,
  "dry_run": false
}

Option B:
POST /admin/publishing-console/supplier-offers/{offer_id}/prepare-conversion-chain

Body:
{
  "idempotency_key": "...",
  "confirm": true,
  "dry_run": false
}

Do not invent a broad action framework if not already present.

Keep this B15E2 slice narrow.

---

# 3. Request schema

Required fields:

- supplier_offer_id if not in path
- idempotency_key: required non-blank string after trim
- confirm: bool = false
- dry_run: bool = false

Optional:
- action_code only if an existing generic action endpoint requires it
- actor/requested_by only if current admin action patterns already support it

Do not add unrelated fields.

---

# 4. Response schema

Preferred:
- reuse AdminPrepareConversionChainExecutionResultRead

If a publishing console wrapper is needed, it may include:
- action_code
- source surface: publishing_console
- execution_result: AdminPrepareConversionChainExecutionResultRead

But avoid unnecessary wrapper if existing API style returns action results directly.

---

# 5. Service / architecture rules

Must preserve:

- PostgreSQL-first
- service layer owns business rules
- route layer thin
- repository layer persistence-only
- no UI/publishing console duplication of chain logic
- B16D2C/B16D2B remains source of truth for execution behavior
- payment/order/reservation paths untouched
- Telegram publish/send/retry untouched

Do not call:
- supplier offer publish service
- Telegram Bot API
- showcase publish attempt create/send/retry
- payment entry
- booking/reservation services
- Mini App routing helpers

Only allowed mutation path:
- PrepareConversionChainExecutionService.execute(...)

---

# 6. Confirm / dry-run behavior

Rules:

- dry_run=true:
  - confirm may be false
  - no business mutation
  - no persisted audit attempt if service contract says dry_run creates no audit rows

- dry_run=false:
  - confirm must be true
  - otherwise return 422 before execution

- idempotency_key:
  - required
  - blank after trim rejected
  - repeated live key must replay stored attempt

---

# 7. Error mapping

Reuse existing project conventions and B16D2C behavior.

Expected:
- missing/invalid admin token -> existing admin auth response
- missing supplier offer -> 404
- live without confirm -> 422
- running/conflicting idempotency -> 409
- blocked/invalid execution -> safe 422/409 according to existing B16D2C mapping
- unexpected -> existing FastAPI behavior

---

# 8. Tests required

Add focused tests for B15E2.

Required cases:

1. auth required
2. missing supplier offer -> 404
3. blank idempotency_key rejected
4. live without confirm -> 422
5. dry_run works through publishing console execution path
6. live happy path works and returns execution result
7. idempotent replay uses same attempt_id and does not create duplicate attempt
8. blocked offer returns safe mapped error/result according to existing service behavior
9. no Telegram publish/showcase send/retry is called
10. no Layer A order/payment/reservation mutation
11. B16D2C direct endpoint tests still pass
12. B16D2D affordance/read model tests still pass

Mock or assert no calls to Telegram/publish services where project test style allows.

---

# 9. Docs update

Minimal docs only:

- docs/CHAT_HANDOFF.md
- create docs/HANDOFF_B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_ACTION_EXECUTION.md
- optionally update docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md if it is the current publishing console continuity doc
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md only if real new debt appears

Document:
- publishing console can now execute prepare_conversion_chain
- execution still goes through guarded service/idempotency
- idempotency_key required
- confirm=true required for live
- dry_run supported
- no Telegram publish/send/retry
- no Layer A booking/payment mutation
- no migration

---

# 10. Strict boundaries / must not do

Do NOT implement:

- Telegram publish
- Telegram send
- Telegram retry
- channel post
- auto-publish
- scheduler
- UI frontend button rendering beyond backend API/action contract
- Mini App changes
- B11 deep-link changes
- order creation
- payment creation
- reservation creation
- seat mutation outside existing prepare_conversion_chain service path
- new Alembic migration
- new table
- broad action framework rewrite

This is a narrow backend execution bridge from publishing console to existing guarded prepare_conversion_chain.

---

# 11. Before coding, report briefly

Before editing files, output:

1. Existing publishing console routes/services/schemas found.
2. Whether an action execution endpoint already exists.
3. Chosen route shape for B15E2 and why.
4. Files/classes to change.
5. Tests to add/update and run.

Then implement.

---

# 12. Verification commands

Run at minimum:

python -m compileall app tests

python -m pytest tests/unit/test_admin_prepare_conversion_chain_api.py -q
python -m pytest tests/unit/test_prepare_conversion_chain_d2d_affordance.py -q

Then run focused publishing console tests, adapting filenames to actual project:

python -m pytest tests/unit/test_admin_publishing_console.py -q
python -m pytest tests/unit/test_admin_publishing_console_prepare_chain_action.py -q

Also run service regression:

python -m pytest tests/unit/test_prepare_conversion_chain_execution_service.py -q

---

# 13. After coding, report

After coding, report:

1. Files changed.
2. Endpoint/route added or extended.
3. Request/response schema.
4. How it delegates to PrepareConversionChainExecutionService.
5. Confirm/dry_run/idempotency behavior.
6. Tests added/updated.
7. Test results.
8. Docs updated.
9. Risks/follow-up.

Do not commit.
Do not push.
Do not run production smoke.