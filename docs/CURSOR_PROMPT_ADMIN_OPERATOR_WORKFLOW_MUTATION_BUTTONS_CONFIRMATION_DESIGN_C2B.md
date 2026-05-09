# CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_MUTATION_BUTTONS_CONFIRMATION_DESIGN_C2B

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Plan.

This is a design/contract step.

Do not change code in this step.
Do not modify files in this step unless explicitly asked after the design report.

---

## Functional block

ADMIN OPERATOR WORKFLOW — Slice C2B Design

Mutation buttons confirmation policy for Telegram admin workflow.

---

## Context

Implemented and deployed:

- Slice B: `GET /admin/supplier-offers/{offer_id}/review-package` includes read-only `operator_workflow`.
- Slice C1: Telegram admin card displays `operator_workflow`.
- Slice C1.1: Telegram operator workflow block compacted.
- Slice C2A: Telegram admin card consumes `operator_workflow.actions` for read-only buttons only:
  - refresh review-package
  - showcase preview read-only

Manual C2A check passed:

- `Reîncarcă review-package` works.
- `Previzualizare showcase` works.
- webhook 200.
- lifecycle remains unchanged.
- showcase preview does not publish to channel.
- no execution link / publish / catalog mutation happens.

Now we need to decide how to safely add or adapt mutating Telegram buttons.

---

## Critical safety principles

Preserve:

- No auto-publish.
- No auto-create Tour.
- No auto-activate catalog.
- No auto-create execution link.
- No batch “run whole workflow”.
- No booking/payment mutation from admin card.
- No external AI.
- Mini App remains execution truth.
- Layer A remains booking/payment authority.
- review-package remains read-only.
- Telegram buttons must map to explicit single actions only.

---

## Existing Telegram buttons

Telegram admin card currently has legacy buttons such as:

- Aprobă
- Respinge
- Orders
- Requests
- Previous / Next
- Back / Home

The existing `Aprobă / Respinge` are mutating moderation actions.

Do not assume we should remove them. Analyze whether they should:

1. remain unchanged,
2. receive a confirmation step,
3. be replaced by operator_workflow-based buttons,
4. be kept as legacy while new workflow buttons are separate.

---

## Goal of this Plan step

Design C2B safely.

Answer:

1. Which mutating actions are eligible for Telegram in the next implementation slice?
2. Which actions must remain disabled/postponed?
3. What confirmation UX should be used?
4. How to prevent accidental public actions?
5. How to avoid duplicate buttons with existing `Aprobă / Respinge`?
6. What tests are needed?
7. What is the smallest safe implementation slice after this design?

---

## Action categories from operator_workflow

Known danger levels:

- `safe_read`
- `safe_mutation`
- `conversion_enabling`
- `public_dangerous`

Known action examples:

### safe_read

- review_package_refresh
- get_showcase_preview
- verify_mini_app_catalog
- verify_supplier_offer_landing
- verify_bot_deep_link

### safe_mutation

- generate_packaging_draft
- approve_packaging_for_publish
- approve_offer_moderation
- create_tour_bridge

### conversion_enabling

- activate_tour_for_catalog
- create_execution_link

### public_dangerous

- publish_showcase_channel

---

## Questions to answer

### 1. Candidate C2B actions

Evaluate these possible next Telegram mutating actions:

- approve_offer_moderation
- approve_packaging_for_publish
- generate_packaging_draft
- create_tour_bridge

For each:

- business meaning
- risk level
- whether it already has an existing Telegram button
- whether confirmation is required
- whether it should be included in C2B or postponed

Expected conservative bias:

- Existing `Aprobă / Respinge` should not be duplicated blindly.
- If adding workflow-based mutation buttons, start with only one or two safe_mutation actions.
- All safe_mutation actions should require confirmation unless already intentionally legacy.

### 2. Explicitly postponed actions

Confirm these must not be in C2B:

- activate_tour_for_catalog
- create_execution_link
- publish_showcase_channel
- batch workflow / “complete conversion”
- booking/payment/order actions

Explain why.

### 3. Confirmation UX

Design confirmation flow.

Possible pattern:

Initial card button:

```text
Approve moderation