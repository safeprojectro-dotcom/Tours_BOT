Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y27 design gate completed
- `docs/SUPPLIER_OFFER_EXECUTION_LINKAGE_DESIGN.md` accepted as current design truth
- current `docs/CHAT_HANDOFF.md`

Не начинать заново.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment core semantics.
Не менять RFQ/bridge semantics.
Не менять payment-entry/reconciliation semantics.
Не делать broad analytics/dashboard rewrite.

## Continuity base
Use as source of truth:
- current codebase
- `docs/CHAT_HANDOFF.md`
- `docs/SUPPLIER_OFFER_EXECUTION_LINKAGE_DESIGN.md`

Accepted from Y27:
- authoritative execution truth = Layer A `Tour + Order`
- safe path requires explicit additive linkage record
- one supplier offer may have only one active execution link at a time
- historical links should be preserved
- supplier booking-derived metrics are shown only when active link exists
- booking-derived push alerts are postponed to a later step

# Exact next step
## Y27.1 — Supplier offer execution linkage persistence + admin link/unlink

## Goal
Implement the narrow persistence and admin operating path for authoritative offer→execution linkage, without yet building booking-derived alerts.

## What this step must implement

### 1. Add linkage persistence
Create a narrow additive persistence model for execution linkage, e.g. `supplier_offer_execution_links`.

The linkage should minimally represent:
- supplier_offer_id
- tour_id
- link status / active flag semantics
- created_at / updated_at
- closed/replaced timestamps or equivalent if needed by the accepted design

Preserve historical links.
Do not collapse everything into one mutable row if that breaks history.

### 2. Enforce one-active-link invariant
At any given time:
- one supplier offer may have at most one active execution link

Replacement should close the previous active link and create/activate the new one safely.

Use the narrowest safe implementation.
Prefer explicit service-layer validation plus DB support if appropriate.

### 3. Add admin link action
Add a narrow admin action to link a published supplier offer to a specific `Tour`.

This should be explicit admin-controlled linkage.
Do not infer linkage automatically.
Do not match by title/date heuristics.

### 4. Add admin unlink / close action
Add a narrow admin action to close/remove the currently active linkage for a supplier offer.

This should preserve history and remove active execution visibility.

### 5. Restrict linkage semantics safely
Linkage should be operationally meaningful only when grounded and allowed by the accepted design.

Use narrow safe validation such as:
- offer exists
- tour exists
- supplier offer lifecycle state is appropriate for linkage (likely published; follow accepted design)
- target tour is valid for operational linkage
- no unsafe duplicate active linkage remains

Do not broaden beyond the narrowest required rule set.

### 6. Add supplier read-side aggregate metrics only when linked
Extend supplier read-side so booking-derived aggregate metrics appear only when there is an active authoritative link.

Safe metrics allowed by design:
- declared_capacity
- occupied_capacity
- remaining_capacity
- active_reserved_hold_seats
- confirmed_paid_seats
- sold_out flag or equivalent

Only if each metric is cleanly grounded in current execution truth.
If some metric is ambiguous, do not expose it yet.

### 7. Preserve non-linked behavior
If no active link exists:
- supplier offer read-side should remain honest
- do not invent booking stats
- show a narrow “not linked / stats unavailable” style signal if useful

## What this step must NOT do
Do NOT:
- add booking-derived push notifications yet
- expose customer identity or lists
- expose payment rows/provider details
- add supplier booking/payment controls
- redesign Layer A booking/order model
- redesign RFQ/bridge semantics
- build dashboards/analytics suite
- auto-link offers to tours heuristically

## Architecture guardrails
- execution truth remains `Tour + Order`
- linkage must be explicit and additive
- read-side only for supplier metrics
- no UI-only fake math
- no second booking truth model
- preserve supplier offer lifecycle boundaries

## Likely files to touch
Likely:
- new model + migration for linkage table
- repository/service for linkage operations
- narrow admin routes/schemas
- supplier workspace read-side service/handler
- focused tests

Avoid touching unrelated subsystems.

## Before coding
Output briefly:
1. current state
2. what Y27 decided
3. exact Y27.1 implementation goal
4. likely files to change
5. risks
6. what remains postponed

## Suggested implementation order
1. add linkage model + migration
2. add repository/service
3. implement one-active-link invariant
4. add admin link action
5. add admin unlink/close action
6. expose safe aggregate metrics in supplier read-side only when linked
7. add focused tests

## Required focused tests
Add focused tests for:
1. link record persists correctly
2. one-active-link invariant holds
3. admin can link published offer to tour
4. admin can close/unlink active linkage while preserving history
5. supplier sees booking-derived aggregate metrics only when linked
6. no customer PII leaks
7. no booking/payment/RFQ semantics changed

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what admin can now do
6. what supplier can now see
7. what remains intentionally postponed
8. compatibility notes

## Important note
This step implements persistence + admin link/unlink + safe aggregate read-side only.
Do not silently expand into booking-derived alerts, customer lists, finance views, or dashboard rewrite.