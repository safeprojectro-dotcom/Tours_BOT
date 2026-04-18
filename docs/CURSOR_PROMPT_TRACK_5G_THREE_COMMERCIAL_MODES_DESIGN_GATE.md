Do not implement code yet.

Run a design/decision gate for **Track 5g — Separate 3 commercial modes safely**.

## Continuity / positioning
This gate comes **after** the already accepted RFQ/customer-visibility slice (`Track 5f v1`) and must **not** reopen or redesign that work.

Important:
- Treat `Track 5f v1` as completed and accepted.
- Do not use this gate to redesign RFQ customer summary visibility.
- Do not directly resume old `Phase 7.1 Step 6` wording if it is less precise than the 3-mode model below.
- This gate is the new, cleaner framing for that problem.

## Problem to solve
The system risks conflating three distinct commercial modes that must be separated clearly:

### Mode 1 — Supplier route / per-seat ready-made offer
A supplier-defined catalog offer where the route/tour, date/time, price, departure point, and conditions are already fixed by the supplier.
Customer buys **seats** on a ready-made offer.

### Mode 2 — Supplier route / full-bus ready-made offer
A supplier-defined catalog offer where the route/tour, date/time, price for the whole bus, departure point, and conditions are already fixed by the supplier.
Customer books **the whole bus** on a ready-made offer.

Important:
Mode 2 is still a **catalog offer**, not a custom RFQ by default.

### Mode 3 — Customer custom bus rental request
A customer-defined request where the customer specifies route/date/group size/conditions and suppliers respond with proposals.
This is the RFQ / marketplace flow.

## Core rule
The system must stop treating **Mode 2** as if it were automatically **Mode 3**.

## Must preserve
Do not break or redesign:
- accepted Track 5f v1 customer multi-quote summary slice
- existing RFQ bridge/payment/hub logic (Tracks 5a–5e)
- Layer A order/payment truth
- supplier/admin authority already established in current flows

This is design only.

## Required decision areas

### A. Exact definitions
Define the 3 modes precisely:
- who defines the product parameters
- whether the offer is ready-made or customer-defined
- whether it belongs to catalog flow or RFQ flow
- whether customer is selecting a product or creating a request

### B. Mapping to current system entities
Map the current entities to the 3 modes, including as relevant:
- tours
- supplier offers
- custom marketplace requests
- supplier custom request responses
- selected response
- booking bridge
- Mini App catalog/detail
- My Requests hub

### C. What must never be conflated
Make explicit at least:
- Mode 2 must not automatically inherit RFQ/operator wording
- Mode 3 must not be rendered like a ready-made catalog checkout
- RFQ selected proposal must not masquerade as a generic catalog offer unless explicitly materialized
- full_bus must not automatically mean operator-only if the offer is a ready-made supplier catalog offer

### D. Execution/payment ownership by mode
For each mode, clarify:
- whether self-service booking is conceptually possible
- whether self-service payment is conceptually possible
- whether operator/assisted flow is required by default
- whether RFQ bridge logic applies
- whether admin winner selection applies
- whether supplier-defined execution/payment policy is relevant

### E. Customer-facing UX implications by mode
For each mode, define the intended customer-facing meaning in Mini App:
- correct main CTA family
- whether “Reserve”, “Reserve bus”, “Request offer”, “Continue booking”, or “Need help” is appropriate
- whether generic operator/help wording is misleading
- whether the mode belongs in catalog UI or RFQ/My Requests UI

### F. Supplier/admin authority by mode
Clarify:
- where supplier-defined offer conditions are authoritative
- where admin selection is authoritative
- where customer has no choice
- where customer is buying a ready-made offer
- where customer is initiating a request

### G. Safe rollout strategy
Recommend the smallest safe rollout order after this gate.
Bias strongly toward:
1. design clarity first
2. read-side classification second
3. review/stabilization third
4. policy/copy correction later
5. deeper execution changes only in a separate explicit gate

## Required output
Produce:
1. current state summary
2. exact 3-mode definition
3. mapping from current system entities to the 3 modes
4. what is currently conflated and why it is dangerous
5. final recommendation
6. safe rollout order
7. must-not-break reminder

## Constraints
- no code
- no migrations
- no payment redesign
- no bridge redesign
- no RFQ redesign
- no Layer A redesign
- no reopening Track 5f v1 scope

## Before doing anything
Summarize:
1. what current catalog / RFQ / bridge layers already support
2. what 3-mode separation gap remains
3. which docs and code areas you will inspect

## After completion
Report:
1. final recommendation
2. whether implementation should start now or not
3. exact next safe implementation step