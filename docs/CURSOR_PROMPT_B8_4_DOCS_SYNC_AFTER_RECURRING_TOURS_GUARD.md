# CURSOR_PROMPT_B8_4_DOCS_SYNC_AFTER_RECURRING_TOURS_GUARD

You are continuing the Tours_BOT project.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

This is a documentation-only sync step after B8.3.

Do not change runtime code.
Do not change migrations.
Do not change tests unless you find a broken docs reference that absolutely requires a small docs-only test fixture update. Prefer docs only.

---

## Current checkpoint

B8 recurring supplier offers have been implemented and stabilized.

Completed:

### B8 slice 1
- Admin-only recurring draft Tour generation implemented.
- Endpoint:
  POST /admin/supplier-offers/{offer_id}/recurrence/draft-tours
- Creates B8R-* draft Tour rows from an approved SupplierOffer template.
- Adds audit/provenance rows in supplier_offer_recurrence_generated_tours.
- Does not create SupplierOfferTourBridge records.
- Does not activate catalog.
- Does not publish to Telegram.
- Does not create orders/reservations/payments.
- Re-runs are currently non-idempotent and documented as accepted tech debt.
- start_offset_days=0 may duplicate the template/B10 bridged date and is documented as accepted tech debt.

### B8 stabilization
- B8 generated Tours remain draft.
- Duplicate draft Tours are allowed.
- B8 does not create or mutate SupplierOfferTourBridge records.
- B8 only reuses shared draft Tour insertion mapping.

### B8.2 activation policy design
- Accepted.
- B10.2 remains the single activation path:
  draft Tour → open_for_sale.
- No hidden B8 activation route.
- No automatic activation.
- Audit table + Tour row are enough for B8 traceability.
- Y27/supplier_offer_execution_links are separate and not automated by B8.

### B8.3 duplicate active Tour activation guard
- Implemented.
- Commit:
  460ef50 — feat: guard recurring tour activation conflicts
- Guard lives inside AdminTourWriteService.activate_tour_for_catalog.
- If the Tour is B8-generated, activation is blocked when another open_for_sale Tour already exists for the same source SupplierOffer and same departure_datetime.
- Conflict includes:
  - sibling B8-generated active Tour
  - primary B10 bridged active Tour for same SupplierOffer/date
- Duplicate draft Tours remain allowed.
- Idempotent activation replay still works.
- Non-B8 activation still works.
- No migration.
- Tests passed.
- Railway production smoke passed:
  - /health -> ok
  - /healthz -> ready
  - Mini App UI -> HTTP 200

---

## Source documents to read first

Read:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md
- docs/CURSOR_PROMPT_B8_2_RECURRING_TOUR_ACTIVATION_POLICY_DESIGN.md
- docs/HANDOFF_B8_2_RECURRING_ACTIVATION_POLICY_TO_IMPLEMENTATION.md
- docs/HANDOFF_B8_3_DUPLICATE_ACTIVE_TOUR_ACTIVATION_GUARD.md if it exists
- docs/TESTING_STRATEGY.md

If some files are missing, do not invent content. Mention missing files in the final report and update available docs only.

---

## Goal of this step

Synchronize project continuity docs after B8.3.

The next agent must clearly understand:

- B8 is implemented and stabilized.
- B8.2 activation policy is accepted.
- B8.3 duplicate active activation guard is implemented.
- Duplicate draft Tours remain accepted tech debt.
- Duplicate active Tours for same source SupplierOffer/date are blocked for B8-generated Tours.
- Legitimate second vehicle on same route/date is not solved by code now and must be treated as future operational policy.
- B7.3 media pipeline remains postponed.
- B10.6 Telegram bot router/consultant redesign remains postponed.
- B11 Telegram deep-link routing is not implemented yet.
- Next safe step should be chosen explicitly after this sync.

---

## Expected files to change

Prefer only:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

Optional, only if already tracking this B-series:

- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md

Do not edit code.

---

## Required updates

### 1. docs/CHAT_HANDOFF.md

Add or update a current checkpoint section:

B8 status:
- B8 recurring draft Tour generation implemented.
- B8 stabilization completed.
- B8.2 activation policy accepted.
- B8.3 duplicate active Tour activation guard implemented.
- Commit: 460ef50 — feat: guard recurring tour activation conflicts.
- Railway smoke passed:
  - /health ok
  - /healthz ready
  - Mini App UI 200

Architecture status:
- B8 generation creates draft Tours only.
- Catalog activation remains explicit through B10.2.
- No automatic activation.
- No Telegram publish.
- No orders/reservations/payments during generation.
- B8 does not create SupplierOfferTourBridge records.
- Duplicate draft Tours are allowed as tech debt.
- Duplicate active/open_for_sale B8 Tours for same source SupplierOffer + departure_datetime are blocked at activation time.
- B10 primary bridged active Tour conflict is also guarded.

Next-safe-step note:
- B8 follow-up is documentation sync only.
- After sync, choose next step explicitly:
  - B7.3 media pipeline if storage/download policy is decided;
  - B11 Telegram deep-link routing if exact Tour landing behavior is ready;
  - B10.6 Telegram bot router/consultant redesign if bot duplication becomes priority;
  - or business-plan continuation B12/B13 if publishing/template library is prioritized.

Do not imply any of these next steps is automatically approved.

---

### 2. docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Add/update B8 sections:

#### B8 recurrence generation re-run idempotency
Current decision:
- Re-running same recurrence input may create duplicate draft Tours.
- Accepted now because generated Tours remain draft and not bookable.
Risk:
- admin clutter
- accidental duplicate activation attempts
Future options:
- generation_batch_key
- uniqueness by source_supplier_offer_id + generated_departure_datetime
- admin preview before generation
Status:
- open / non-blocking

#### B8 duplicate active Tour guard
Current decision:
- Duplicate draft Tours are allowed.
- Duplicate active/open_for_sale Tours for same source SupplierOffer + departure_datetime are blocked for B8-generated Tours.
- Conflict includes sibling B8 active Tour and B10 primary bridged active Tour.
Why accepted:
- prevents accidental duplicate live catalog rows in Mini App.
Risk:
- legitimate second vehicle on same route/date is blocked under same SupplierOffer.
Status:
- accepted MVP safety default.

#### B8 legitimate second vehicle on same date
Current decision:
- Current B8.3 guard blocks activating a second B8-generated Tour for the same source SupplierOffer and same departure_datetime.
Why accepted now:
- safer MVP default; avoids confusing duplicate live catalog cards.
Preferred MVP handling:
- If it is the same customer-facing product, increase capacity on the existing active Tour.
- If it is operationally distinct, use a separate SupplierOffer/Tour.
Future possible enhancement:
- admin override with explicit reason, audit trail, and Mini App copy rules.
Revisit trigger:
- when real operations require multiple vehicles for same supplier offer/date.
Status:
- open / future operational policy.

---

### 3. Business plan document

Find the actual business plan file. It may be named:

- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- or another business-plan file in the repo

Update B8 section:

B8 — Recurring Supplier Offers:
- mark implemented/stabilized.
- record that recurring supplier offer generation creates draft Tour instances.
- record that activation is explicit and separate.
- record that duplicate active Tour guard exists.
- record that second vehicle same date is future operational policy, not automatic behavior.

Do not rewrite the whole business plan.

---

### 4. Optional docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md

Only if this file already tracks B-series supplier-offer-to-tour continuation:

- add a concise B8 closure note.
- do not mix B8 with RFQ marketplace tracks.
- preserve Layer A compatibility language.

---

## Non-goals

Do not:

- change app code
- change tests
- change migrations
- implement second vehicle override
- implement generation idempotency
- implement admin list endpoint
- implement batch activation
- implement Telegram publish
- implement B7.3 media pipeline
- implement B10.6 bot redesign
- implement B11 deep links
- implement payment/order/reservation changes
- auto-activate Tours
- create SupplierOfferTourBridge records from B8

---

## Required checks

Run only documentation-level checks:

- git diff --stat
- git diff -- docs/CHAT_HANDOFF.md docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- If business plan file is changed, include it in diff review.

No pytest required if docs-only.

If any code changes happen accidentally, stop and report.

---

## Final report required

Report exactly:

1. Files changed
2. Sections updated
3. Confirmation that no code/migrations/tests were changed
4. Whether B8 completion is now visible in CHAT_HANDOFF
5. Whether second vehicle edge case is documented
6. Whether B7.3 / B10.6 / B11 remain explicitly not implemented
7. git diff summary
8. Recommended next safe step options, without choosing automatically