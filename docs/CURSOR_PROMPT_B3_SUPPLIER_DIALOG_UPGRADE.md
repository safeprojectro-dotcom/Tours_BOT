You are continuing Tours_BOT after B2.

Goal:
B3 — Supplier Dialog Upgrade.

Implement structured supplier offer intake dialog using the B2 fields.

Read:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md

Scope:
Upgrade supplier Telegram/admin intake flow so supplier provides structured raw facts, not free-form sales copy.

Allowed:
- Telegram supplier-admin FSM/dialog updates
- supplier-admin offer create/update glue for B2 fields
- validation/missing-field prompts
- draft/ready_for_moderation criteria aligned with B1/B2
- focused tests

Dialog principles:
- one question at a time
- supplier gives facts, not marketing text
- collect required fields first
- optional fields after required fields
- support skipping optional fields
- support summary before submit
- submit only when required fields are complete

Collect:
Required:
- title / route
- departure date or recurrence indication
- departure/return time if one-time offer
- price + currency
- capacity/seats
- basic program points
- included/excluded
- at least one media/cover reference or explicit “no photo yet”
- supplier contact/admin notes if current flow needs it

Optional:
- short_hook
- marketing_summary
- discount_code
- discount_percent / discount_amount
- discount_valid_until
- recurrence_type / recurrence_rule
- valid_from / valid_until
- additional media references

Must NOT:
- implement AI generation
- create Tour
- modify Mini App catalog
- change booking/order/payment
- change publish behavior
- send supplier/customer notifications
- create offer-to-tour bridge
- generate branded image/card

Before coding:
1. summarize B1/B2 current state
2. list files expected to change
3. explain why B3 is dialog-only and does not affect Layer A

After coding:
1. files changed
2. dialog steps added
3. required/optional fields supported
4. tests run
5. confirm no AI/Tour/Mini App/booking/payment/publish behavior changed
6. next safe step: B4 AI Packaging Layer