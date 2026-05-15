# CURSOR_PROMPT_B16D2D_PREPARE_CONVERSION_CHAIN_ACTION_AFFORDANCES

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoint:

- f8f146f feat: add guarded prepare conversion chain admin endpoint

B16D2C is closed.

Now implement:

# B16D2D — Read Model / Action Affordance Integration

## Goal

Expose read-only action metadata / affordances for the guarded admin action:

POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain

The goal is to let admin/read surfaces know that this action exists, when it is eligible, and which endpoint/method/requirements apply.

This block must NOT execute the action from UI or Telegram.

---

# 1. Relevant existing state

Already closed:

- B16D1:
  GET /admin/supplier-offers/{offer_id}/prepare-conversion-chain/plan

- B16D1.1:
  read models expose:
  prepare_conversion_chain_plan_path

- B16D1.2:
  read models expose:
  prepare_conversion_chain_plan_status
  prepare_conversion_chain_recommended_action
  prepare_conversion_chain_blockers_count

- B16D2A:
  guarded action audit/idempotency foundation

- B16D2B:
  service-level execution:
  PrepareConversionChainExecutionService.execute(...)

- B16D2C:
  POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain
  idempotency_key required
  confirm=true required for live execution
  dry_run supported
  admin auth required
  no Telegram I/O
  no Layer A booking/payment mutation
  no Mini App routing changes

---

# 2. Required behavior

Add action affordance metadata to appropriate read models for supplier-offer-related rows.

Candidate surfaces:

1. Supplier offer review package
2. Publishing console supplier-offer rows
3. Ops dashboard supplier-offer-related rows:
   - publication rows
   - conversion rows
   - attention rows
4. Operator workflow read model only if the current architecture already has a clean place for it

Do not force it into surfaces where it does not naturally belong.

---

# 3. Suggested metadata shape

Prefer one reusable small schema if existing style allows it.

Example fields:

prepare_conversion_chain_action:
  code: "prepare_conversion_chain"
  method: "POST"
  path: "/admin/supplier-offers/{offer_id}/prepare-conversion-chain"
  requires_admin: true
  requires_idempotency_key: true
  requires_confirm_for_live: true
  supports_dry_run: true
  enabled: bool
  disabled_reason: optional string
  plan_path: existing plan path if available
  plan_status: existing status if available
  recommended_action: existing recommended action if available
  blockers_count: existing blockers count if available

If the project already uses a different action metadata schema, reuse it.

Important:
- This is read-only metadata.
- Do not call execution service from read models.
- Do not create attempts.
- Do not write audit rows.
- Do not mutate bridge/tour/execution links.

---

# 4. Enabled / disabled logic

Keep logic service-layer owned.

Do not duplicate complex readiness business rules inside route/UI.

Preferred:
- derive from existing prepare_conversion_chain plan summary:
  - ineligible / blocked -> enabled=false
  - partial / already_prepared -> decide according to existing recommended_action semantics
  - if safe, enabled=true when action can be proposed to admin
- or expose conservative metadata with enabled=false if blockers exist

If there is already a service/helper used for plan status/read model enrichment, extend it there.

The route/schema should only serialize the result.

---

# 5. Strict boundaries / must not do

Do NOT implement:

- dashboard button click handler
- publishing console action execution
- Telegram publish/send/retry
- Telegram channel post
- scheduler
- auto-publish
- Mini App route changes
- B11 deep-link changes
- order/payment/reservation mutation
- Layer A booking/payment changes
- new Alembic migration
- new table
- frontend UI
- broad docs rewrite

This is only read-model metadata / affordance integration.

---

# 6. Tests required

Add or update focused tests.

Required coverage:

1. review package exposes prepare_conversion_chain action metadata
2. publishing console supplier-offer row exposes action metadata
3. ops dashboard supplier-offer-related row exposes action metadata where appropriate
4. blocked/ineligible plan produces disabled affordance or safe metadata
5. eligible/partial plan produces enabled affordance if policy says action may be proposed
6. metadata includes:
   - method POST
   - execution path
   - idempotency required
   - confirm required for live
   - dry_run supported
7. no audit attempt rows are created by read endpoints
8. no bridge/tour/execution-link mutation happens from read endpoints

Also run B16D2C API endpoint tests to ensure no regression.

---

# 7. Minimal docs update

Update only current continuity docs:

- docs/CHAT_HANDOFF.md
- docs/HANDOFF_B16D2C_PREPARE_CONVERSION_CHAIN_API_ENDPOINT.md or create/update a B16D2D handoff if existing pattern requires it
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md only if new debt/decision appears

Document:
- read models now expose prepare_conversion_chain action metadata
- execution remains only through B16D2C POST endpoint
- no UI/button execution yet
- no Telegram I/O
- no migration

---

# 8. Before coding, report briefly

Before editing files, output:

1. Which read models currently expose:
   - prepare_conversion_chain_plan_path
   - prepare_conversion_chain_plan_status
   - prepare_conversion_chain_recommended_action
   - prepare_conversion_chain_blockers_count

2. Which files/classes will be changed.

3. Exact tests to add/update and run.

Then implement.

---

# 9. Verification commands

Run at minimum:

python -m compileall app tests

python -m pytest tests/unit/test_admin_prepare_conversion_chain_api.py -q

Then run focused tests around:
- supplier offer review package
- publishing console
- ops dashboard
- prepare conversion chain plan/read models

Use actual project filenames.

---

# 10. After coding, report

After coding, report:

1. Files changed
2. Read models updated
3. Metadata shape
4. Enabled/disabled logic
5. Tests added/updated
6. Test results
7. Docs updated
8. Risks/follow-up

Do not commit.
Do not push.
Do not run production smoke.