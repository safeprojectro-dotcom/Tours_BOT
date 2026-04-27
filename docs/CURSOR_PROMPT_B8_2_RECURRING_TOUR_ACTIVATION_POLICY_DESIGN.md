# CURSOR_PROMPT_B8_2_RECURRING_TOUR_ACTIVATION_POLICY_DESIGN

You are continuing the Tours_BOT project.

## Cursor model / mode

Use the strongest reasoning model available.

Cursor mode: Plan.

Do not edit code in this step unless explicitly requested later. This is a design/planning gate.

---

## Current checkpoint

B8 slice 1 was implemented and stabilized.

Latest accepted checkpoint:

- B8 recurring draft Tour generation exists.
- Admin-only endpoint:
  POST /admin/supplier-offers/{offer_id}/recurrence/draft-tours
- Generated Tours use B8R-* codes.
- Generated Tours are created as draft.
- Generated Tours are not open_for_sale.
- Generated Tours are not visible/bookable in Mini App catalog.
- No Telegram publish happens.
- No orders/reservations/payments are created.
- No SupplierOfferTourBridge records are created or mutated by B8.
- B8 reuses shared draft Tour insertion mapping only.
- Re-runs are currently non-idempotent and documented as tech debt.
- start_offset_days=0 can duplicate the template/B10 bridged date and is documented as tech debt.

Accepted stabilization commit:

- dbd1272 — test,docs: stabilize B8 recurring draft tours

---

## Main architecture rules

Preserve these rules:

- Supplier Offer = raw supplier proposal/source facts.
- Tour = customer-facing sellable catalog object.
- Mini App = execution truth and conversion.
- Layer A = booking/payment authority.
- Telegram Channel = marketing showcase.
- Telegram Bot = router/consultant/entry point, not duplicate Mini App catalog.
- Admin = final decision maker.
- AI = draft generator only.

Hard rules:

- visibility != bookability.
- Bridge creation != catalog activation != Telegram publish != booking/payment.
- Recurrence generation must not silently activate Tours.
- Recurrence generation must not publish anything.
- Recurrence generation must not create orders/reservations/payments.
- No silent ORM triggers.
- No AI-created Tours.
- No supplier bypass.
- Business rules stay in service layer.
- Repositories stay persistence-oriented.
- Mini App consumes backend truth, it must not invent booking rules.

---

## Source documents to review first

Read these before answering:

- docs/HANDOFF_B10X_TO_B8_RECURRING_SUPPLIER_OFFERS.md
- docs/HANDOFF_B8_STABILIZATION_TO_NEXT_STEP.md if it exists
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md
- docs/MINI_APP_UX.md
- docs/TESTING_STRATEGY.md

If some documents are missing, do not invent content. Mention missing files in the final report and continue with available sources.

---

## Goal of this Plan step

Design the next safe policy for B8 recurring generated draft Tours:

How should recurring generated draft Tours become eligible for catalog activation and Layer A execution?

This is not an implementation step.

The output should be an architecture decision and the recommended next small implementation slice.

---

## Questions to answer

### 1. Activation ownership

Compare these options:

A. Manual activation per generated Tour  
B. Batch review + selective activation  
C. Automatic activation during recurrence generation  
D. Scheduled activation by policy later

For each option, analyze:

- safety
- operational complexity
- risk of accidental catalog visibility
- risk of duplicate active Tours
- compatibility with B10.2
- compatibility with Mini App execution truth
- suitability for MVP

Recommend one default.

Expected bias:
- safest MVP default should avoid automatic activation.

---

### 2. Execution linkage

Do B8 generated Tours need a new execution/link record, or is the Tour row plus audit table enough?

Consider:

- B10 primary bridge has explicit SupplierOffer → Tour bridge.
- B8 generated Tours already have audit rows in supplier_offer_recurrence_generated_tours.
- Generated Tours are already Layer A Tour rows.
- Layer A reservation/payment can operate on Tours once open_for_sale.
- B8 must not create SupplierOfferTourBridge records.

Clarify whether the audit row is sufficient for traceability, or whether a new link/execution table is needed later.

---

### 3. Catalog activation relationship

Should B8 generated Tours use the same activation endpoint/policy as B10.2?

Preferred principle:

- one explicit admin activation rule for Tour draft → open_for_sale
- no hidden special B8 activation path
- no silent activation during generation

Evaluate if this is enough or if B8 needs an additional guard before activation.

---

### 4. Activation readiness checks

Before a generated recurring Tour can be activated, what should be checked?

Consider:

- title/default content exists
- departure/return dates are valid
- sales_deadline is valid
- price/currency is valid
- seats_total/seats_available are valid
- sales_mode is valid
- per_seat/full_bus semantics are valid
- fixed full_bus does not use per-seat wording
- boarding fallback rules are safe
- media/cover fallback is acceptable, but B7.3 real media pipeline is still postponed

Do not pull B7.3 media storage/download/card rendering into this step.

---

### 5. Duplicate-date policy

The accepted B8 tech debt says:

- re-running the same recurrence input can create duplicate draft Tours
- start_offset_days=0 can overlap with the template/B10 bridged date

Question:

Should duplicate draft Tours remain acceptable but duplicate active/open_for_sale Tours be blocked or warned?

Propose a safe activation-time rule.

Example policy to evaluate:

- duplicate draft Tours are allowed as operational tech debt
- activation should fail or warn if another active/open_for_sale Tour exists for the same supplier_offer/source route/date window
- if duplicate active Tours are allowed for a legitimate reason, admin must explicitly override later, but not in MVP

---

### 6. Admin UX / operational visibility

What minimum admin visibility is needed before activation?

Options:

- no new UI/API yet, use existing Tour admin detail/list
- add admin recurrence-generated list/read endpoint
- add warnings to generated Tour detail
- add batch review endpoint later

Recommend the smallest safe next implementation slice.

---

### 7. Recommended next implementation step

Recommend the next small Agent step after this Plan is accepted.

Good candidates:

- B8.3: Activation guard for recurring generated Tours, reusing existing Tour activation endpoint
- B8.3: Admin read/list for recurrence generated Tours with warnings
- B8.3: Documentation-only acceptance if current activation path is already sufficient
- B8.3: Duplicate active Tour guard before open_for_sale

Choose one and justify.

---

## Non-goals

Do not propose implementing now:

- automatic activation
- automatic Telegram publish
- Telegram deep link B11
- Telegram bot redesign B10.6
- B7.3 media storage/download/card rendering
- scheduler/cron recurrence
- supplier-side generation
- AI-generated Tours
- payment/order/reservation changes
- Mini App UI changes
- broad recurrence_rule engine
- full idempotency/batch-key implementation unless only documented as future
- unmoderated supplier lifecycle side effects

---

## Required final report

Return a structured design report with:

1. Current state summary
2. Decision matrix for activation options
3. Recommended activation policy
4. Execution link decision
5. Activation readiness checks
6. Duplicate-date policy
7. Admin visibility recommendation
8. Files likely affected in the next implementation step
9. Tests likely needed in the next implementation step
10. Non-goals preserved
11. Recommended next Agent prompt name

Do not change files in this Plan step.