# CURSOR_PROMPT_B16D2E_PREPARE_CONVERSION_CHAIN_PRODUCTION_SMOKE

You are continuing the existing Tours_BOT project.

Current clean checkpoint:

- fd4e25d feat: expose prepare conversion chain action affordances
- f8f146f feat: add guarded prepare conversion chain admin endpoint

B16D2C and B16D2D are closed.

This task is:

# B16D2E — Production / Railway Smoke for prepare_conversion_chain

This is NOT a code implementation task.

Do not change runtime code unless a real blocking bug is found and explicitly reported first.

---

## Goal

Prepare and execute a careful smoke verification for:

POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain

The smoke must verify:

1. dry_run works safely
2. live execution works only with confirm=true
3. bridge exists or is created
4. tour is activated/open_for_sale if eligible
5. active execution link exists
6. guarded action audit attempt + steps are visible/persisted
7. idempotent replay works
8. no Telegram publish/send/retry happened
9. no Layer A order/payment/reservation mutation happened
10. no Mini App routing or B11 behavior changed

---

## Strict boundaries

Do NOT:

- publish to Telegram
- send Telegram messages
- retry supplier execution attempts
- create orders
- create payments
- create reservations
- mutate seats outside the existing prepare_conversion_chain service path
- change Mini App routing
- change B11 deep links
- add dashboard/publishing console execution
- add scheduler/auto-publish
- run destructive SQL
- change code before reporting the exact issue

---

## Before doing smoke

Inspect current code/docs and report:

1. Exact endpoint path and request body.
2. Required admin auth header.
3. Which GET endpoints can verify:
   - supplier offer review package
   - prepare_conversion_chain plan
   - publishing console row
   - ops dashboard row
   - audit attempt/steps visibility
   - bridge/tour/execution link state
4. How to identify a safe candidate supplier_offer_id.
5. Which states are safe for smoke and which are unsafe.
6. Exact PowerShell curl/Invoke-RestMethod commands with placeholders only:
   - $BASE_URL
   - $ADMIN_API_TOKEN
   - $OFFER_ID
   - $IDEMPOTENCY_KEY

Do not include real secrets.

---

## Smoke sequence

Use this sequence:

### Step 1 — Read-only precheck

- GET review package / detail for chosen offer
- GET prepare_conversion_chain plan
- check:
  - plan_status
  - recommended_action
  - blockers_count
  - prepare_conversion_chain_action metadata
  - no blockers for live execution, unless smoke is intentionally blocked-case only

### Step 2 — dry_run

POST:

/admin/supplier-offers/{offer_id}/prepare-conversion-chain

Body:

{
  "idempotency_key": "b16d2e-smoke-dry-run-<timestamp>",
  "dry_run": true,
  "confirm": false
}

Verify:

- response returned
- no bridge/tour/execution-link mutation
- no audit attempt if service contract says dry_run does not create audit rows
- no Telegram I/O

### Step 3 — live execution

Only if Step 1 and Step 2 are safe.

POST same endpoint:

{
  "idempotency_key": "b16d2e-smoke-live-<timestamp>",
  "dry_run": false,
  "confirm": true
}

Verify response:

- status succeeded / partial_success according to expected result
- steps are present
- bridge/catalog/execution-link steps are explicit
- no hidden Telegram action

### Step 4 — idempotent replay

Repeat the same live request with the same idempotency_key.

Verify:

- same stored attempt is replayed
- no duplicate attempt
- no duplicate bridge/catalog/link calls
- response indicates replay or stored attempt behavior according to service contract

### Step 5 — post-read verification

Read again:

- prepare_conversion_chain plan
- review package
- publishing console / ops dashboard if relevant
- audit visibility endpoint/section
- DB/admin read surfaces for bridge/tour/execution link if available

Verify:

- tour is visible/open_for_sale only if activation step succeeded
- active execution link exists
- action affordance now reflects current plan/status
- no Telegram publish/send/retry
- no order/payment/reservation changes

---

## Documentation output

After smoke, update or create a minimal document:

docs/B16D2E_PREPARE_CONVERSION_CHAIN_PRODUCTION_SMOKE.md

Include:

- environment: Railway/staging/production as actually used
- date/time
- commit tested
- offer_id used
- dry_run idempotency key
- live idempotency key
- results of each step
- observed attempt/step ids if safe to record
- no Telegram I/O confirmation
- no Layer A order/payment/reservation mutation confirmation
- issues/warnings
- final status:
  - passed
  - passed with warnings
  - blocked
  - failed

Also update docs/CHAT_HANDOFF.md minimally with B16D2E status.

Do not commit or push.

---

## If a bug is found

Stop and report:

1. exact command
2. response
3. expected behavior
4. actual behavior
5. suspected file/service
6. whether data mutation occurred
7. whether rollback/manual cleanup is needed

Do not repair automatically without explicit approval.