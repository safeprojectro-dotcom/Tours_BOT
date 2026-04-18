Implement **Phase 7.1 / Sales Mode / Step 3** as a narrow Mini App read-side adaptation.

Prerequisite:
- Step 1 completed: `tour.sales_mode` source-of-truth exists
- Step 2 completed: backend sales-mode policy exists
- this step must consume backend/service-layer policy, not invent UI logic

## Goal
Adapt Mini App read-side behavior so it reflects backend sales-mode policy safely, without introducing direct whole-bus booking flow.

## Important constraints
Do not implement:
- direct whole-bus booking
- new payment behavior
- operator-assisted whole-bus workflow
- ad hoc UI-only policy
- old Phase 7 reopening

## Safe scope
Mini App may now:
- read sales-mode-aware backend outputs
- change CTA visibility/text/state based on backend policy
- avoid exposing standard self-service booking CTA for tours that should not behave like per-seat self-service

Examples of allowed adaptation:
- for `per_seat`: existing read-side/CTA can remain compatible
- for `full_bus`: Mini App may show an informational state or “contact / request assistance” style placeholder, but only if backed by backend policy

## Must not change yet
- no real full-bus reservation creation flow
- no payment flow for whole-bus mode
- no operator handoff implementation unless already scheduled separately
- no booking engine rewrite

## Tests
Add focused Mini App read-side tests only:
- `per_seat` tour still renders current expected path
- `full_bus` tour does not pretend per-seat self-service if backend policy says otherwise
- no booking/payment behavior changes are introduced

Before coding:
1. summarize Step 1 and Step 2
2. list exact endpoints/services/UI files to touch
3. list what remains postponed

After coding:
1. files changed
2. Mini App behavior changed
3. tests run
4. results
5. postponed items