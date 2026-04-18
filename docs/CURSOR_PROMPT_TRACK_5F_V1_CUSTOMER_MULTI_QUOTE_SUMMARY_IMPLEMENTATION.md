Implement **Track 5f v1 — Customer Multi-Quote Summary / Aggregate Visibility**.

Do not implement customer quote selection, customer-side winner choice, or a full quote comparison UI.

## Preconditions already completed
- Track 5a — Commercial Resolution Selection Foundation
- Track 5b.1 — RFQ Booking Bridge Record Foundation
- Track 5b.2 — bridge execution entry
- Track 5b.3a — supplier policy + effective execution resolver
- Track 5b.3b — bridge payment eligibility
- Track 5c — RFQ Mini App UX wiring
- Track 5d — Mini App My Requests / RFQ status hub
- Track 5e — bridge supersede / cancel lifecycle
- Track 5f design gate concluded:
  - customer multi-quote visibility must remain read-only
  - admin selection remains authoritative
  - no customer quote picking
  - bridge/actionability stays unchanged
  - minimal safe v1 = aggregate/summary only

## Core principle
Customer-facing quote visibility is informational only.
It must not create a second execution path, a second commercial truth, or a bidding UI.

## Goal
Add the smallest safe customer-facing quote visibility to Mini App RFQ detail.

Recommended v1 scope:
- aggregate count of proposed responses
- neutral “offers received / under review” messaging
- optional selected-offer read-only snippet after resolution only if fields are tightly allowlisted

## Required scope

### A. Customer read model expansion
Additive only.

Extend customer-facing RFQ detail read model with safe, bounded fields such as:
- `proposed_response_count`
- `offers_received_hint` or equivalent summary field
- optionally `selected_offer_summary` with a tightly controlled shape

Keep fields optional/additive where appropriate.

### B. Service-layer composition
Compute these values in the service layer.

Rules:
- count only `proposed` responses
- do not expose declined responses to customers
- do not expose raw internal supplier/admin fields
- selected-offer snippet, if included, must be tightly filtered and only for the selected response after 5a resolution

### C. Safe selected-offer snippet (optional in v1)
If implemented in this slice, keep it minimal and allowlisted.

Allowed examples:
- quoted price/currency
- short safe message excerpt
- safe execution summary label

Do NOT expose:
- competing supplier identities
- all response free-text
- alternate non-selected quotes as actionable
- raw internal notes

If this is too risky for the first slice, implement only aggregate count + neutral summary.

### D. Mini App rendering
Render the new information only in the RFQ/My Request detail area.

Do not add:
- dedicated comparison screen
- bridge flow comparison
- customer quote selection UI
- extra payment/booking CTA logic

### E. Actionability unchanged
All existing CTA rules must remain unchanged:
- Continue booking only via active bridge/path rules
- Continue to payment only via existing hold/eligibility/order path
- Open booking only via Layer A truth
- no “Accept offer” customer CTA

### F. Safety/visibility rules
Customer should see:
- neutral progress information
- whether offers were received
- optionally safe selected-offer summary after selection

Customer should not see:
- supplier competition mechanics
- competing supplier identities
- declined-response dirt
- actionable alternate offers
- any field that can conflict with selected bridge/order/payment path

## Strong constraints
Do NOT implement:
- customer quote choice
- full comparison cards
- competing supplier cards
- new booking/payment logic
- new bridge logic
- new FastAPI write routes
- request lifecycle redesign
- supplier/admin portal redesign

## Must-not-break rules
Preserve:
- 5a admin selection authority
- 5b bridge execution logic
- 5b.3a effective execution policy behavior
- 5b.3b payment eligibility behavior
- 5c bridge continuation flow
- 5d My Requests hub CTA rules
- 5e bridge supersede/cancel lifecycle behavior
- Layer A booking/payment truth

## Testing scope
Add focused tests for:
- proposed_response_count composed correctly
- declined responses excluded
- selected-offer snippet included only when allowed
- no alternate/non-selected offer becomes actionable
- My Request detail renders new summary safely
- no regression in hub CTA logic
- no regression in bridge/payment behavior

## Before coding
First summarize:
1. exact files/modules to touch
2. whether migrations are needed
3. exact customer-facing fields you will add
4. whether selected-offer snippet is included in this v1 or postponed
5. what remains explicitly postponed after 5f v1

## After coding
Report:
1. files changed
2. migrations added
3. tests run
4. results
5. current customer multi-quote summary behavior now supported
6. compatibility notes against Tracks 0–5e
7. postponed items