# CURSOR_PROMPT_B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE

## Context

Project: Tours_BOT.

Current clean checkpoint:
- `e3e108 feat: add ops dashboard audit visibility`
- `a3e435 feat: add prepare conversion chain readiness summary`
- `e74f505 feat: expose prepare conversion chain plan paths`
- `d5d9e8a feat: add prepare conversion chain plan preview`
- `b0f11e2 docs: design guarded ops automation`

B16 read-only OPS foundation is now strong:

- B16 Step 1: `GET /admin/ops-dashboard`
- B16B: filters / limits / include_sections
- B16C: admin navigation paths
- B16D: guarded automation design
- B16D1: read-only prepare_conversion_chain plan preview
- B16D1.1: plan path exposed in read models
- B16D1.2: readiness summary/status in read models
- B16E: audit_events visibility

Now we need the design gate for the first guarded mutation:

`prepare_conversion_chain`

This is NOT implementation yet.

## Goal

Create a short but precise design gate for B16D2.

Future action:

`POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain`

Purpose:

For an approved supplier offer, internally prepare the conversion chain:

1. create/link tour bridge if missing;
2. activate linked tour for catalog if eligible;
3. create active execution link if missing.

Explicitly NOT included:

- Telegram publish;
- Telegram send;
- publish retry;
- payment changes;
- order changes;
- reservation changes;
- seat changes except through existing catalog activation semantics if already part of that safe service;
- supplier outbound messages;
- Mini App routing changes;
- Layer A booking/payment mutation.

## Required docs

Create:

- `docs/B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md`
- `docs/HANDOFF_B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE_TO_NEXT_STEP.md`
- `docs/CURSOR_PROMPT_B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md`

Update:

- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

Do not change app code.
Do not change tests.
Do not add endpoint.
Do not add migration.

## Required design content

### 1. Objective

Define B16D2 as a future guarded internal preparation action.

It should reduce admin burden but stay below the public publish boundary.

### 2. Future endpoint

Preferred endpoint:

`POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain`

Reason:
- source entity is explicit;
- matches existing supplier-offer admin routes;
- easier audit;
- easier idempotency;
- less abstract than generic action executor.

### 3. Request body

Propose request body:

```json
{
  "idempotency_key": "uuid-or-client-generated-key",
  "confirm": true,
  "dry_run": false
}
```

### 4. Additional design sections (authoritative detail)

The created **`docs/B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md`** must also cover at minimum:

- Execution order (bridge → catalog activation → execution link) and delegation to **existing** services only.
- Preconditions aligned with **`GET .../prepare-conversion-chain/plan`** and **B16D** §4.
- **`dry_run`** semantics (no persistence mutations when true).
- Response shape expectations (`success` / `partial_success` / `failed`, `steps[]`, navigation hints).
- Idempotency and audit (top-level + per-step; compatibility with B16E ops visibility).
- Explicit exclusions list (Telegram publish/send/retry, orders, payments, reservations, Mini App, Layer A booking mutation, supplier outbound, etc.).

### 5. Deliverables checklist

- [x] `docs/B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md`
- [x] `docs/HANDOFF_B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE_TO_NEXT_STEP.md`
- [x] `docs/CURSOR_PROMPT_B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md` (this file, complete)
- [x] `docs/CHAT_HANDOFF.md` — B16D2 design gate continuity bullet + links
- [x] `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` — B16D2 design gate recorded; implementation still gated

### 6. Non-goals (this prompt)

- No FastAPI route, no service implementation, no migrations, no new tests, no OpenAPI registration for `POST .../prepare-conversion-chain` until a separate implementation slice is explicitly authorized after this gate is reviewed.