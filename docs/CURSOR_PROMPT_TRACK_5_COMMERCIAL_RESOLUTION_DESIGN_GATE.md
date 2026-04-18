Do not implement new application code yet.

Run a design/decision gate for **Track 5 — Commercial Resolution Layer**.

## Context
The following tracks are already completed and accepted:
- Track 0 — frozen core baseline
- Track 1 — design package acceptance/alignment
- Track 2 — Supplier Admin Foundation
- Track 3 — moderated supplier-offer publication to Telegram showcase
- Track 4 — Custom Request Marketplace Foundation

The current architecture already supports:
- supplier-owned offers
- moderated publication into Telegram showcase
- custom request intake from Mini App and private bot
- supplier responses to requests
- central admin oversight

## Critical rule
Track 5 must not silently collapse the distinction between:
- ready-made offer publication / booking flows
- RFQ / custom-request lifecycle
- eventual booking/payment execution

This step is a design/decision gate only, not implementation.

## Goal
Determine the minimum safe commercial-resolution model for requests after suppliers respond.

Main question:
**How should a request move from “supplier responses exist” to an actual commercial outcome, without breaking Layer A booking/payment semantics?**

## What to review
Review the current state across:
- Track 2 supplier-admin model
- Track 3 publication model
- Track 4 request and supplier-response model
- current Layer A booking/order/payment model
- current Phase 7.1 `sales_mode` and assisted full-bus path

## Required decision areas

### A. Winner / selection model
Decide how a request gets resolved commercially:
- can the customer choose directly?
- does central admin choose?
- does supplier “win” by first proposal?
- is there a manual assignment step?
- is there a status like selected / awarded / closed?

### B. Commercial ownership model
Clarify the allowed resolution models:
- platform-owned checkout
- supplier-assisted closure
- hybrid model
- request closes outside platform but is recorded internally

### C. Request → booking bridge
Decide whether Track 5 should later create:
- a dedicated bridge from winning request/response into a normal order
- a separate commercial resolution record first
- no bridge yet, only admin/supplier/customer coordination

This must be explicit.

### D. Payment model
Clarify whether payment should remain:
- entirely outside Track 5 for now
- future platform checkout only after bridge design
- supplier-side/manual payment handling
- configurable by supplier/payment mode

### E. Customer visibility
Decide what the customer should see after supplier responses exist:
- all supplier responses?
- one selected proposal?
- only admin-guided outcome?
- request still “in review”?

### F. Admin role
Clarify how central admin participates:
- monitor only
- select supplier
- approve final outcome
- trigger the bridge into booking/payment later

## Required output
Produce a concise but concrete design/review result that includes:

1. **Current state summary**
   - what Tracks 2–4 already support
   - what is still missing for commercial closure

2. **Commercial resolution options**
   - compare at least 2–3 realistic models
   - explain pros/cons and operational risk

3. **Recommendation**
   Choose one recommended Track 5 direction for this project now.

4. **Bridge decision**
   State explicitly whether:
   - request/order bridge should be implemented next
   - only a commercial-resolution state machine should be implemented next
   - or Track 5 should stop before any booking/payment bridge

5. **Minimum safe future rollout order**
   If Track 5 is approved later, outline a safe implementation order, for example:
   - resolution statuses / winner selection
   - admin-controlled closure
   - customer-visible selected proposal
   - optional bridge object
   - only later booking/payment integration

6. **Must-not-break reminder**
   Reconfirm that Layer A booking/order/payment semantics must remain protected.

## Constraints
- do not modify application code
- do not add migrations
- do not refactor services
- do not broaden supplier auth
- do not redesign marketplace from scratch
- keep this as a design gate only

## Before doing anything
Summarize:
1. what Tracks 2–4 already established
2. what exact commercial gap remains
3. which docs you will update or use

## After completion
Report:
1. final recommendation
2. whether Track 5 implementation should start now or not
3. whether a request/order bridge is recommended now or later
4. exact next safe step if implementation is approved