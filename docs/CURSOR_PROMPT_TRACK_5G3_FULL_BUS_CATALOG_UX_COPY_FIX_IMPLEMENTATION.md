Implement **Track 5g.3 — Full-bus catalog UX/copy fix**.

Do not redesign booking/payment architecture.

## Continuity
This slice comes after:
- accepted Track 5g design gate (3 commercial modes)
- accepted Track 5g.1 read-side classification
- accepted Track 5g.2 full-bus catalog policy/copy gate

Accepted framing:
- `supplier_route_full_bus` is a ready-made catalog charter offer
- it is not RFQ/custom request by default
- current architecture treats it as assisted-by-default in execution/policy
- therefore UX/copy must express “catalog charter with assisted completion,” not RFQ language

## Goal
Fix customer-facing Mini App copy/CTA wording so **Mode 2** (`supplier_route_full_bus`) no longer feels like:
- RFQ
- “request offers”
- supplier bidding
- custom trip intake

while preserving all existing backend execution rules.

## Core rule
This slice is **copy/presentation only**.

It must not:
- change TourSalesModePolicyService behavior
- open self-service whole-bus checkout
- change bridge/RFQ logic
- change payment-entry logic
- change Layer A booking/order/payment semantics
- reopen Track 5f v1 scope

## Required scope

### A. Audit current user-visible Mode 2 strings
Inspect Mini App surfaces where `supplier_route_full_bus` currently appears and identify wording that leaks RFQ/custom-request meaning.

Especially inspect:
- catalog/tour detail CTAs
- preparation/detail support text
- any “request assistance” language
- any “request/offer/team contact” phrasing that could be read as Mode 3

### B. Replace Mode 2 wording with catalog-charter wording
Align wording with the approved 5g.2 matrix.

Mode 2 wording should express:
- listed/full-bus catalog charter
- assisted booking/completion for this listed product
- help/contact about this trip/listing
- not “custom request”
- not “request offers from suppliers”
- not “RFQ”

### C. Keep CTA family consistent with current implementation reality
Because self-service whole-bus execution is not being added in this slice:
- assisted CTAs are allowed
- help/contact CTAs are allowed
- wording must remain honest about current path
- wording must stay tied to **this listing / this trip / this charter**
- wording must not imply instant self-service if backend does not support it

### D. Do not change Mode 3 wording
Ensure RFQ/custom request screens keep Mode 3 language.
Do not blur 5f v1 or bridge flows.

### E. Keep scope minimal
Bias strongly toward:
- Mini App only
- the smallest set of changed strings / presentation branches
- no broad refactor
- no routing changes unless strictly needed for wording correctness

## Strong constraints
Do NOT implement:
- self-service full-bus booking
- reservation/payment behavior changes
- bridge changes
- RFQ changes
- new help/handoff backend
- private bot redesign unless parity is absolutely required and still remains copy-only

## Testing scope
Add focused checks for:
- Mode 2 screens show catalog-charter wording
- Mode 3 screens still show request/RFQ wording
- no regression in existing CTA/actionability rules
- no regression in 5f v1, 5g.1, and bridge-related reads

## Before coding
Summarize:
1. exact files/modules to touch
2. whether migrations are needed
3. exact wording/CTA replacements planned
4. what remains explicitly postponed after 5g.3

## After coding
Report:
1. files changed
2. migrations added
3. tests run
4. results
5. current full-bus catalog UX/copy behavior now supported
6. compatibility notes
7. postponed items