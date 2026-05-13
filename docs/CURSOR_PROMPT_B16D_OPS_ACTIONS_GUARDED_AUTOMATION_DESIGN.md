# CURSOR_PROMPT_B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN

## Context

Project: Tours_BOT.

We are continuing after B16 Step 1 and B15 publishing-console foundation.

Recent clean checkpoint:

- `6d4a911 feat: add admin ops dashboard read view`
- `1083fa9 docs: close B15 publishing console foundation`
- `2808d2b feat: add publishing console template source channel read model`
- `1aeeb10 feat: add publishing console action affordances`

B15B–B15F closed safe publishing console foundation:

- read-only publishing console;
- readiness/blockers;
- exact CTA safety;
- read-only action affordances;
- source/template/channel/media read model;
- no action execution;
- no scheduler;
- no auto-publish.

B16 Step 1 implemented:

- `GET /admin/ops-dashboard`
- read-only OPS dashboard
- summary
- attention_items
- recent_orders
- upcoming_tours
- recent_publications
- conversion_links
- audit_hint

Current product concern:

The admin/operator may become overloaded if every supplier-offer publication requires too many manual steps:

1. generate/approve package
2. approve moderation
3. create tour bridge
4. activate tour for catalog
5. create execution link
6. approve/clear media
7. publish to Telegram channel

We need automation, but safely.

Accepted principle:

Do not jump to auto-publish.

Instead, design guarded operator actions:

- system computes next action automatically;
- admin gets one-click guarded actions;
- non-public internal preparation may be chained;
- public channel publish remains explicit and confirmation-gated;
- every action must be audited.

## Goal

Create a design-only document for B16D / OPS guarded automation.

This design should define how future dashboard/admin actions may work without implementing them yet.

The key design target is a future action:

`prepare_conversion_chain`

Meaning:

For an approved supplier offer, automatically perform internal non-public preparation:

1. create/link tour bridge if missing;
2. activate linked tour for catalog if eligible;
3. create active execution link if missing.

But it must NOT publish to Telegram.

After successful preparation, the item becomes:

`ready_to_publish`

and public publish remains a separate explicit action:

`publish_showcase_channel`

with confirmation.

## Scope

Docs/design only.

Do not change app code.
Do not change tests.
Do not add endpoints.
Do not mutate data.
Do not publish/send/retry.
Do not change Layer A.
Do not change Mini App routing.

## Required docs to create

Create:

- `docs/B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md`
- `docs/HANDOFF_B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN_TO_NEXT_STEP.md`
- `docs/CURSOR_PROMPT_B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md`

Update:

- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

Optionally update:

- `docs/B16_ADMIN_OPS_VISIBILITY_READ_DASHBOARD.md`
- `docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`

Only update optional docs if there is a clear place for a short cross-reference.

## Required design content

`docs/B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md` must include:

### 1. Problem

Explain the operator burden:

- too many safe-but-manual steps;
- PowerShell/API calls are not a sustainable operator workflow;
- dashboard should guide and eventually execute guarded actions;
- but public publish and payment/order actions are risky.

### 2. Automation levels

Define levels:

#### Level 0 — read-only visibility

Already done:

- publishing console;
- ops dashboard;
- readiness;
- blockers;
- action affordances;
- no mutation.

#### Level 1 — assisted one-click actions

Future:

- single explicit action;
- existing underlying service call;
- confirmation depending on danger level;
- audit required.

Examples:

- approve packaging
- approve cover
- create tour bridge
- activate tour
- create execution link
- publish with confirmation

#### Level 2 — guarded internal chain

Future:

- `prepare_conversion_chain`
- may run multiple internal non-public steps
- must stop before Telegram publish
- requires strict preconditions
- requires audit trail for each sub-step

#### Level 3 — public publish with confirmation

Future:

- publish is external/public side effect
- must remain separate from prepare chain
- requires explicit confirmation
- no hidden publish inside internal chain

#### Level 4 — scheduler / auto-publish

Future only:

- not approved now
- requires separate B15G design gate

### 3. Proposed future action: prepare_conversion_chain

Define:

Code:

- `prepare_conversion_chain`

Purpose:

- move approved supplier offer to “ready to publish” without public side effects.

Possible sub-steps:

1. create tour bridge
2. activate tour for catalog
3. create execution link

Explicitly excluded:

- Telegram publish
- Telegram send
- payment changes
- order changes
- supplier outbound message
- auto-retry

### 4. Preconditions

List strict preconditions:

- supplier offer lifecycle approved
- packaging approved_for_publish
- cover/media status either approved_for_card or explicitly cleared for text-only
- no blocking quality warnings that prevent publish
- source fields sufficient for tour materialization
- no active conflicting bridge/link
- linked tour has valid departure, price, capacity, boarding data
- catalog activation precheck passes
- execution link precheck passes
- operator/admin identity known
- idempotency key available
- confirmation accepted if action is classified conversion_enabling

### 5. Failure and partial success policy

Important:

The chain may partially succeed.

Example:

- bridge created
- catalog activation failed
- execution link not created

Design must define:

- every sub-step audited separately
- final result can be partial_success
- dashboard must show remaining next action
- retries must be explicit
- idempotent replay must not duplicate bridges/links
- no rollback unless explicitly designed later
- no silent retry
- no hidden publish after partial success

### 6. Audit model

Define audit requirements:

For each action and sub-step:

- action_code
- actor_surface
- requested_by
- idempotency_key
- source_entity_type
- source_entity_id
- target_entity_type
- target_entity_id
- started_at
- finished_at
- status
- error_code
- error_message
- sub_steps[]
- before/after summary where safe

If current audit tables are insufficient, mark as future implementation requirement, not implemented now.

### 7. Danger classification

Use existing style:

- safe_read
- safe_mutation
- conversion_enabling
- public_dangerous

Classify:

- prepare_conversion_chain = conversion_enabling
- publish_showcase_channel = public_dangerous
- payment completion = public/financial dangerous or separate payment-controlled action
- order cancel/refund = future explicit OPS action, not part of this design

### 8. Dashboard/UI behavior

Future dashboard should show:

- next_action_code
- next_action_label
- enabled
- disabled_reason
- requires_confirmation
- danger_level
- action_explainer
- what will happen
- what will NOT happen
- expected result after success

For prepare_conversion_chain:

Button label examples:

- `Prepare for publish`
- RO: `Pregătește pentru publicare`

Confirmation copy must state:

- creates/links tour;
- activates catalog if eligible;
- creates booking link;
- does not publish to Telegram;
- does not charge customers;
- does not change existing orders.

### 9. API design options

Design possible future endpoints, but do not implement:

Option A:

- `POST /admin/ops/actions/prepare-conversion-chain`

Option B:

- `POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain`

Option C:

- generic action executor:
  `POST /admin/actions`

Recommend one option.

The recommendation should consider:

- clarity
- auditability
- admin route conventions
- idempotency
- future reuse

### 10. Idempotency

Define:

- client supplies idempotency_key
- same action + same source + same key returns same result or safe replay
- no duplicate bridges
- no duplicate execution links
- no duplicate Telegram publish

Even though publish is not part of prepare chain, design must reserve this principle.

### 11. Non-goals

Explicitly exclude:

- implementation
- endpoint creation
- auto-publish
- scheduler
- payment completion
- order cancellation
- refund
- supplier outbound send
- Telegram publish
- Mini App changes
- Layer A changes

### 12. Recommended next implementation sequence

After this design, recommend:

1. B16B — filters/limits/time-window controls for ops-dashboard, if not done yet.
2. B16C — dashboard-to-detail navigation polish.
3. B16D1 — implement read-only action plan preview endpoint, not execution.
4. B16D2 — implement `prepare_conversion_chain` with strict audit and idempotency.
5. B15E2 — explicit action execution integration in publishing console.
6. B15G — guarded auto-publish design only much later.

## Update CHAT_HANDOFF

Add a concise bullet:

- B16D design done: guarded OPS automation levels and future `prepare_conversion_chain` design.
- No implementation.
- Public publish remains separate and confirmation-gated.
- Next recommended: B16B filters or B16C navigation before execution.

## Update OPEN_QUESTIONS_AND_TECH_DEBT

Add / update rows:

- B16D guarded automation design done.
- Future implementation gated:
  - B16D1 action plan preview endpoint
  - B16D2 prepare_conversion_chain execution
  - B15E2 action execution integration
  - B15G auto-publish only after explicit design

## Non-goals for this prompt

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
2. Design summary.
3. Recommended future endpoint option.
4. Future implementation sequence.
5. `git status --short`.
6. `git diff --stat`.
7. Confirmations:
   - docs-only;
   - no app code changes;
   - no tests required;
   - no production calls;
   - no production data mutation;
   - no Telegram send/publish/retry;
   - no Layer A changes;
   - no Mini App routing changes.

---

## Completion (this archive)

Artifacts produced from this prompt:

- [`docs/B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md`](B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN.md)
- [`docs/HANDOFF_B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN_TO_NEXT_STEP.md`](HANDOFF_B16D_OPS_ACTIONS_GUARDED_AUTOMATION_DESIGN_TO_NEXT_STEP.md)
