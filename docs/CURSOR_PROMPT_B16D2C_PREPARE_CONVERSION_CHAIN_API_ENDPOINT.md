# CURSOR_PROMPT_B16D2C_PREPARE_CONVERSION_CHAIN_API_ENDPOINT

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current task:

## B16D2C — API Execution Endpoint for prepare_conversion_chain

Add a guarded central-admin API endpoint:

POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain

This endpoint exposes the already implemented service-level execution:

PrepareConversionChainExecutionService.execute(...)

Do not implement dashboard buttons, publishing console execution, Telegram actions, scheduler actions, or Mini App routing.

---

# 0. Current authoritative context

Use repository state and current docs as source of truth, especially:

- docs/CHAT_HANDOFF.md
- docs/IMPLEMENTATION_PLAN.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/TECH_SPEC_TOURS_BOT.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md
- docs/B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md
- docs/HANDOFF_B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE_TO_NEXT_STEP.md

Important: if some docs are stale, preserve the latest implemented code truth and the latest B16D2B handoff/checkpoint. Do not roll the project back to older Phase 5 context.

Latest known checkpoint before this task:

- B16D1 read-only plan endpoint is closed:
  GET /admin/supplier-offers/{offer_id}/prepare-conversion-chain/plan

- B16D1.1 read models expose:
  prepare_conversion_chain_plan_path

- B16D1.2 read models expose:
  prepare_conversion_chain_plan_status
  prepare_conversion_chain_recommended_action
  prepare_conversion_chain_blockers_count

- B16E ops dashboard audit visibility is closed.

- B16D2A guarded action audit/idempotency foundation is closed:
  admin_guarded_action_attempts
  admin_guarded_action_steps
  unique idempotency:
  (action_code, source_entity_type, source_entity_id, idempotency_key)

- Alembic migration 20260609_30_admin_guarded_action_audit.py already exists and is already applied on Railway.

- B16D2B service-level prepare_conversion_chain execution is closed:
  PrepareConversionChainExecutionService
  no HTTP route yet
  dry_run support
  partial_success support
  idempotent replay for succeeded / partial_success / failed
  writes attempt/step audit
  no Telegram publish/send/retry
  no order/payment/reservation mutation
  no Layer A booking/payment changes
  no Mini App routing changes
  no migration

---

# 1. Goal

Implement the admin API route:

POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain

The route must be a thin delivery layer over:

PrepareConversionChainExecutionService.execute(...)

The endpoint should allow:

1. dry_run execution
2. live execution only when confirm=true
3. idempotent replay via required idempotency_key
4. authenticated central-admin access only

---

# 2. Required request contract

Add or reuse a Pydantic request schema.

Required fields:

- idempotency_key: str
  - required
  - non-empty / trimmed
  - should be validated enough to prevent accidental blank keys

- confirm: bool = false
  - live execution requires confirm=true
  - dry_run may run without confirm=true

- dry_run: bool = false
  - when dry_run=true, call execution service in dry_run mode
  - dry_run must not mutate conversion chain state

Optional fields only if already aligned with existing service signature:
- actor / actor_id / requested_by, if current service expects it
- reason / note, only if current audit foundation already supports it

Do not invent broad new fields.

---

# 3. Response contract

Reuse existing schemas where possible.

Preferred:
- use the same response model style as the B16D2B execution service result
- include attempt status
- include step results
- include idempotency/replay indication if already exposed by service
- include clear message/recommended next step if already exposed
- include audit attempt id if already part of service result

Do not create a second competing response format if an existing execution result schema already exists.

---

# 4. Endpoint behavior

Route behavior:

1. Authenticate via existing central admin auth mechanism.
   - Reuse existing admin auth dependency/pattern.
   - Do not create a new auth system.
   - Do not expose supplier-admin access.

2. Validate request:
   - idempotency_key required
   - if dry_run is false and confirm is not true:
     return safe 400/422-style error according to project conventions

3. Call only:
   PrepareConversionChainExecutionService.execute(...)

4. Route must not duplicate business logic:
   - no manual bridge creation in route
   - no manual tour activation in route
   - no manual execution link creation in route
   - no manual audit-step writing in route
   - no direct repository orchestration except standard dependency/session wiring

5. Map exceptions safely:
   - missing offer -> 404
   - readiness/blockers/blocked execution -> appropriate 400/409-style response according to existing conventions
   - auth missing/invalid -> existing admin auth response
   - unexpected errors -> preserve existing FastAPI error handling style

6. Preserve idempotency:
   - same action_code/source_entity/idempotency_key should replay existing attempt according to B16D2B service behavior
   - do not create new attempts for succeeded / partial_success / failed replay
   - do not bypass service-level idempotency

---

# 5. Strict boundaries / must not do

Do NOT implement:

- dashboard button
- publishing console action execution
- Telegram publish
- Telegram send
- Telegram retry
- showcase channel post
- scheduler
- auto-publish
- frontend UI
- Mini App route changes
- B11 deep-link routing changes
- order creation
- payment entry
- payment reconciliation
- reservation creation
- seat mutation outside the existing catalog activation behavior inside the service chain
- new Alembic migration
- new table
- broad docs rewrite

This is only:
admin POST endpoint + schema glue + tests + minimal docs note.

---

# 6. Tests required

Add focused tests for B16D2C.

Use existing test style and fixtures.

Required test cases:

1. auth required
   - request without valid admin auth is rejected

2. missing supplier offer -> 404
   - route returns not found safely

3. confirm required for live execution
   - dry_run=false and confirm=false should be rejected before live execution

4. dry_run no mutation
   - dry_run=true should call service dry_run behavior
   - should not create bridge/tour activation/execution link if service contract says dry_run is non-mutating
   - should not create live mutation side effects

5. happy path
   - confirm=true, dry_run=false, valid idempotency_key
   - route returns execution result
   - audit attempt/steps visible/persisted as expected by service behavior

6. idempotent replay
   - same idempotency_key returns replayed/stored result
   - no duplicate attempt
   - no duplicate bridge/catalog/link calls

7. service regression still passes
   - existing B16D2B service tests must remain green

8. focused B16 regression
   - existing B16D1/B16D2 related focused tests must remain green

Do not write overly broad end-to-end production tests in this step.

---

# 7. Minimal docs note

Update docs minimally, probably:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md only if a real new debt or decision appears
- B16D2/B16 design handoff doc if it exists and is the current continuity ledger

Document:
- B16D2C endpoint added
- mutation is admin-guarded
- idempotency_key required
- confirm=true required for live execution
- dry_run supported
- no Telegram publish/send/retry
- no Layer A booking/payment mutation
- no Mini App routing changes
- no migration

Do not rewrite large docs sections.

---

# 8. Verification commands

Run at minimum:

python -m compileall app tests

python -m pytest tests/unit/test_prepare_conversion_chain_execution_service.py -q

Then run the most relevant focused API/admin test file(s), depending on existing naming. Look for existing tests around:

- admin supplier offers
- prepare conversion chain plan endpoint
- guarded action audit
- ops dashboard B16
- publishing console B15/B16

Examples, adapt to actual filenames:

python -m pytest tests/unit/test_prepare_conversion_chain_execution_service.py -q
python -m pytest tests/unit/test_admin_prepare_conversion_chain_api.py -q
python -m pytest tests/unit/test_admin_guarded_action_audit.py -q
python -m pytest tests/unit/test_api_admin_supplier_offers.py -q

If project uses unittest for these files, use the existing project style.

---

# 9. Before coding, report briefly

Before editing files, output:

1. Which existing files/classes/routes you found for:
   - admin supplier-offer routes
   - plan endpoint
   - PrepareConversionChainExecutionService
   - guarded action audit service/repository
   - admin auth dependency

2. Proposed files to change/add.

3. Exact tests you will add/run.

Then implement.

---

# 10. After coding, report

After coding, report:

1. Files changed
2. Endpoint added
3. Request/response schemas added/reused
4. Auth/confirm/idempotency behavior
5. Tests added
6. Test results
7. Any docs updated
8. Any risks or follow-up needed

Do not commit.
Do not push.
Do not run Railway production smoke in this step.