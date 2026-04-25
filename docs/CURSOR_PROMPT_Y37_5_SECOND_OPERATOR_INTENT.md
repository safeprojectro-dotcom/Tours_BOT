Y37.5 — Second operator intent (expand decision layer safely)

Goal:
Extend operator decision layer with one additional intent value without changing any existing behavior.

Rules:
- Keep Y37.4 behavior intact
- No supplier actions, no booking, no bridge
- Only extend intent enum + API + Telegram UI

Scope:

1. Add new enum value:
   OperatorWorkflowIntent.NEED_SUPPLIER_OFFER

2. API:
POST /admin/custom-requests/{id}/operator-decision

Allow:
{
  "decision": "need_supplier_offer"
}

3. Service:
- Same rules as Y37.4
- Same idempotency
- Same permissions

4. Telegram:
- Show BOTH buttons when:
  - Owner = you
  - status = under_review
  - intent = null

Buttons:
- Need manual follow-up
- Need supplier offer

- After selection → hide both buttons
- Show selected intent in "Next step"

5. Tests:
- API allow/deny
- Telegram:
  - both buttons appear
  - disappear after selection
  - correct intent displayed

Out of scope:
- Supplier logic
- RFQ
- Bridge
- Booking
- Mini App

Important:
This is still a pure intent layer expansion.