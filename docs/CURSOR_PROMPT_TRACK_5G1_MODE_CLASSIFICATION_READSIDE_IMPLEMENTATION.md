Implement **Track 5g.1 — Commercial mode classification (read-side only)**.

Do not change booking/payment behavior in this slice.

## Continuity / prerequisite
This work comes after the accepted **Track 5g design gate**.

Accepted 3-mode model:

### Mode 1 — supplier_route_per_seat
Ready-made supplier catalog offer.
Supplier/admin define the route/tour, date/time, price, departure point, and conditions.
Customer buys seats on a ready-made catalog product.

### Mode 2 — supplier_route_full_bus
Ready-made supplier catalog offer.
Supplier/admin define the route/tour, date/time, price for the whole bus, departure point, and conditions.
Customer books the whole bus on a ready-made catalog product.

Important:
Mode 2 is still a **catalog offer**, not an RFQ/custom request by default.

### Mode 3 — custom_bus_rental_request
Customer-defined request.
Customer specifies route/date/group size/conditions and suppliers respond with proposals.
This is the RFQ / marketplace flow.

## Core rule
This slice is **classification + read-side exposure only**.

It must not:
- open new booking paths
- change payment logic
- change bridge logic
- change RFQ execution rules
- change Layer A order/payment semantics
- reopen Track 5f v1 scope

## Goal
Add a minimal, explicit read-side classification so the system can distinguish the 3 commercial modes safely and consistently in presentation layers.

Recommended classification values:
- `supplier_route_per_seat`
- `supplier_route_full_bus`
- `custom_bus_rental_request`

You may use another naming shape only if it is clearly better and still maps 1:1 to the accepted 3-mode model.

## Required scope

### A. Introduce derived commercial mode classification
Add a minimal derived classification for relevant read paths.

Classification must be:
- explicit
- additive
- backward-compatible
- computed from existing authoritative objects, not from UI guesswork

### B. Map current objects safely
Expected mapping:
- Layer A `Tour` read paths → Mode 1 or Mode 2 based on existing catalog/tour truth
- RFQ / custom request read paths → Mode 3

Do not invent hybrid modes in this slice.

### C. Expose classification only where needed
Expose the new classification in read models that support presentation and future copy/policy work.

Good candidates:
- Mini App tour detail read
- Mini App customer custom-request detail read
- optionally other safe read models if they directly benefit from the classification

Bias toward the smallest safe surface.

### D. No behavior change yet
Do NOT in this slice:
- change CTA logic
- change reserve/payment flow
- change bridge eligibility
- change supplier/admin RFQ selection behavior
- change effective policy rules
- change bot/Mini App execution routing

### E. Backward compatibility
All new fields must be additive and safe for clients that ignore unknown keys.

## Strong constraints
Do NOT implement:
- self-service full-bus checkout
- RFQ redesign
- bridge redesign
- new payment paths
- new admin workflow
- new operator workflow
- new customer quote actions
- copy/CTA overhaul in this slice

## Testing scope
Add focused tests for:
- correct classification of Mode 1 / Mode 2 / Mode 3
- no regression in existing detail/list reads
- no regression in Tracks 5a–5f v1 behavior
- no unintended behavior changes in booking/payment flows

## Recommended implementation bias
Keep this slice as small as possible.

Preferred outcome:
- one or two read models gain an explicit classification field
- service composition derives the value
- tests prove the mapping
- no unrelated files change

## Before coding
Summarize:
1. exact files/modules to touch
2. whether a migration is needed
3. how the classification will be represented
4. which read paths will expose it
5. what remains explicitly postponed after 5g.1

## After coding
Report:
1. files changed
2. migrations added
3. tests run
4. results
5. current commercial-mode classification behavior now supported
6. compatibility notes against Tracks 5a–5f v1 and Layer A
7. postponed items