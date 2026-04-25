Continue Tours_BOT after Y37.2 accepted.

Task:
Create docs-only design gate for the next operator decision step after under_review.

Context:
Accepted:
- Y36 assign-to-me works.
- Y37.2 mark-under-review works.
- under_review does not affect assignment, booking, payment, supplier, bridge, or Mini App.
- current flow: open -> under_review, only if assigned to current operator.

Goal:
Design the next safe operator decision layer for custom marketplace requests.

Scope:
Docs only.

Do not modify:
- runtime code
- migrations
- API routes
- Telegram handlers
- Mini App
- booking/payment
- supplier routes
- execution links
- identity bridge

Create:
docs/OPERATOR_DECISION_GATE.md

Update:
docs/CHAT_HANDOFF.md with Y37.3 docs-only gate and next-safe pointer.

Design must cover:

1. Current accepted state
- request can be assigned
- assigned operator can mark under_review
- no downstream action exists yet

2. Decision goal
- allow operator to choose what should happen next without creating bookings/payments automatically

3. First decision options
Recommended safe options:
- Need supplier offer
- Need manual follow-up
- Not serviceable / close later
But first runtime slice should be one narrow decision only.

4. Data model options
- avoid changing existing status if decision can be stored separately
- if new fields are needed, propose additive columns only
- do not overload request status with too many meanings

5. Recommended first runtime slice
Use internal admin note / decision marker only, no supplier/booking/bridge side effects.
Example:
- POST /admin/custom-requests/{id}/operator-decision
- decision = need_manual_followup or need_supplier_offer
But choose the safest first slice in the doc.

6. Permissions
- only assigned current operator can decide
- unassigned blocked
- assigned-to-other blocked
- terminal statuses blocked
- under_review required

7. Telegram UI concept
- button appears only when Owner = you and Status = under_review
- decision menu with compact callbacks
- no PII in callback_data

8. Fail-safe behavior
- no automatic supplier publication
- no booking/order creation
- no payment entry
- no bridge creation
- no customer-visible change unless separately gated

9. Tests required
- API allowed/blocked states
- Telegram button visibility
- no side effects to Mini App/My requests
- supplier/booking/payment regressions

10. Postponed
- resolve/close
- supplier RFQ send
- bridge
- booking conversion
- reassign/unassign
- customer notifications

Stop after docs-only design gate.