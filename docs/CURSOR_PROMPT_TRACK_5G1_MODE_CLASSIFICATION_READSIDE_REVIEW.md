Stabilize and review the completed **Track 5g.1 — Commercial mode classification (read-side only)**.

Do not add new features.

## Context
Track 5g design gate established the accepted 3-mode model:

- supplier_route_per_seat
- supplier_route_full_bus
- custom_bus_rental_request

Track 5g.1 implementation has now added read-side commercial mode classification.

This review must confirm that the implementation is:
- additive,
- read-only,
- backward-compatible,
- and does not change booking/payment/RFQ execution behavior.

## Goal
Verify that the new commercial mode classification safely separates:
- catalog per-seat offers
- catalog full-bus offers
- custom RFQ requests

without introducing execution/policy changes.

## Required review tasks

### A. Scope creep review
Confirm that Track 5g.1 did NOT introduce:
- booking behavior changes
- payment behavior changes
- bridge behavior changes
- RFQ execution changes
- CTA logic changes
- bot routing changes
- admin workflow changes
- copy/policy overhaul

### B. Classification correctness review
Explicitly verify:
- Layer A tour detail read path maps `per_seat -> supplier_route_per_seat`
- Layer A tour detail read path maps `full_bus -> supplier_route_full_bus`
- customer custom request detail maps to `custom_bus_rental_request`
- no hybrid/ambiguous mode is introduced
- classification is derived from existing authoritative objects

### C. Read-model safety review
Confirm:
- new fields are additive
- existing clients that ignore unknown fields remain safe
- schema defaults / validation remain backward-compatible
- no existing read contract is broken

### D. Compatibility review
Explicitly verify:
- Track 5a remains unchanged
- Track 5b bridge behavior remains unchanged
- Track 5b.3a effective execution policy remains unchanged
- Track 5b.3b payment eligibility remains unchanged
- Track 5f v1 remains unchanged in meaning
- Layer A order/payment semantics remain unchanged

### E. Mode-separation review
Explain whether this slice successfully creates a safe technical separation between:
- Mode 2 ready-made full-bus catalog offers
- Mode 3 custom RFQ requests

at least on the read-side/presentation-model level.

### F. Docs update
Update:
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `COMMIT_PUSH_DEPLOY.md`

Record Track 5g.1 as implemented + reviewed.

## Before doing anything
Summarize:
1. intended Track 5g.1 scope
2. main compatibility risks
3. exact files/docs to inspect/update

## After completion
Report:
1. files changed
2. whether scope creep was found
3. whether classification is correct
4. whether read-model compatibility is preserved
5. whether Mode 2 vs Mode 3 separation is now technically clearer
6. tests/checks run
7. final compatibility statement
8. exact next safe track