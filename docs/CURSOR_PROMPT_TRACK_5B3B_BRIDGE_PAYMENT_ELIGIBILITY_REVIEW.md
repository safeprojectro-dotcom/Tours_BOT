Stabilize and review the completed **Track 5b.3b — Bridge Payment Eligibility + Existing Layer A PaymentEntry Reuse**.

Do not add new features.

## Context
Track 5b.3b has already been implemented.
Now perform a strict compatibility and scope review before moving further.

## Goal
Confirm that bridge payment eligibility remains:
- additive,
- read-only,
- policy-gated,
- aligned with existing Layer A payment-entry,
- and does not introduce a second payment architecture.

## What must be reviewed carefully
Review all Track 5b.3b changes, with extra attention to:
- payment eligibility route/read shape
- order alignment rules
- effective policy gate
- reuse of existing PaymentEntryService path
- absence of payment side effects
- backward compatibility of additive read fields

## Required review tasks

### A. Scope creep review
Confirm Track 5b.3b did NOT accidentally introduce:
- new payment provider behavior
- new payment session model
- bridge-owned payment rows
- bridge-specific payment execution path separate from existing payment-entry
- automatic payment open after hold
- implicit payment open from resolution / bridge create / bridge patch
- broad RFQ UI redesign
- broad auth/handoff rewrite

### B. Layer A compatibility review
Confirm Track 5b.3b preserves:
- current tours/order/payment semantics
- current PaymentEntryService behavior
- current reservation/payment services
- current standard Mini App booking/payment routes
- current private bot booking/payment routes
- current Track 5b.2 bridge execution behavior
- current Track 5b.3a effective policy behavior
- current migrate -> deploy -> smoke discipline

### C. Payment-gate review
Explicitly explain:
- whether payment eligibility is allowed only when effective policy allows platform checkout
- whether active bridge + request + selected response + user + tour alignment is enforced
- whether explicit order_id is required and no guessing occurs
- whether invalid / expired / mismatched order blocks eligibility correctly
- whether assisted / external / incomplete policy blocks payment eligibility correctly

### D. Existing payment-entry reuse review
Explicitly explain:
- whether eligibility read is fully read-only
- whether no payment rows or payment sessions are created by eligibility read
- whether actual payment still goes only through existing `POST /mini-app/orders/{order_id}/payment-entry`
- whether `is_order_valid_for_payment_entry()` matches existing payment-entry rules closely enough

### E. Read-contract review
Explicitly explain:
- whether the new eligibility response is additive and safe
- whether older clients would simply ignore it
- whether blocked envelopes are clear and stable enough for future Mini App wiring

### F. Docs update
Update the appropriate docs:
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `COMMIT_PUSH_DEPLOY.md`
- optionally `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`

### G. Baseline verification
Run the minimum focused checks necessary to support acceptance.

## Before doing anything
Summarize:
1. intended Track 5b.3b scope
2. main compatibility risks
3. exact files/docs to inspect/update

## After completion
Report:
1. files changed
2. whether scope creep was found
3. whether payment eligibility gate is correct
4. whether existing payment-entry reuse is correct
5. whether no payment side effects exist
6. tests/checks run
7. final compatibility statement
8. exact next safe track