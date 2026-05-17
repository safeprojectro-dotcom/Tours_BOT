# CURSOR_PROMPT_A5_CLARIFICATION_OUTBOX_ADMIN_REVIEW_STATUS_MANAGEMENT

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoint:

- 3eb1dac feat: add supplier clarification outbox
- 0f97a8b fix: humanize admin cockpit text surfaces
- 483c38b fix: clean up admin cockpit card readability
- 29e5c8 fix: humanize supplier clarification drafts
- b0143e7 feat: add supplier clarification draft split

A4 has been committed, pushed, deployed, and Railway DB migration is applied:

- alembic current on Railway: 20260611_32 (head)

## Current state

A4 Supplier Clarification Outbox Foundation is live:

- internal DB table exists
- supplier clarification drafts can be saved from Telegram cockpit
- active draft replay works
- no duplicate active draft is created
- no supplier send
- no publish
- no scheduler
- no Layer A / B11 change

Current gap:

The outbox item can be created/listed, but admin cannot yet manage its lifecycle meaningfully.

A5 should add internal admin review/status management:

- view outbox items
- open item detail
- mark draft as ready_for_review
- cancel item
- mark as sent_externally_later manually
- no actual send

---

# Current block

# A5 — Clarification Outbox Admin Review & Status Management

## Goal

Turn Supplier Clarification Outbox from saved drafts into a manageable internal admin workflow.

Admin should be able to:

1. See supplier clarification outbox items.
2. Open a specific item.
3. Move status:
   - draft → ready_for_review
   - draft/ready_for_review → cancelled
   - ready_for_review → sent_externally_later
4. See status history fields:
   - updated_at
   - last_reviewed_at if implemented
   - review_note if implemented
5. Confirm no automatic supplier send happened.

This is still internal admin workflow only.

---

# Hard safety boundary

Do NOT:
- send Telegram messages to suppliers
- publish to Telegram channel
- schedule messages
- call AI
- call external providers
- change booking/payment/order/reservation logic
- change Layer A
- change B11 routing
- execute prepare_conversion_chain
- create supplier execution links
- auto-notify suppliers
- add broadcast
- add WhatsApp/Email sending

Allowed:
- internal DB status updates on supplier_clarification_outbox_items
- protected admin API status update endpoint
- Telegram admin buttons for status changes
- tests
- docs

---

# Required references

Inspect and align with:

- app/models/supplier_clarification_outbox.py
- app/repositories/supplier_clarification_outbox.py
- app/schemas/supplier_clarification_outbox.py
- app/services/supplier_clarification_outbox_service.py
- app/api/routes/admin.py
- app/bot/handlers/automation_cockpit_admin.py
- app/bot/automation_cockpit_telegram.py
- app/bot/constants.py
- app/bot/messages.py
- tests/unit/test_supplier_clarification_outbox_api.py
- tests/unit/test_automation_cockpit_telegram.py
- docs/HANDOFF_A4_SUPPLIER_CLARIFICATION_OUTBOX_FOUNDATION.md

Also inspect existing project style for:
- status transition validation
- admin protected PATCH/POST endpoints
- Telegram confirm/cancel workflows if already used elsewhere

---

# Existing A4 status values

Use the A4-specific statuses:

- draft
- ready_for_review
- cancelled
- sent_externally_later

Do not reintroduce:
- open
- done
- dismissed

---

# Required service behavior

Extend:

```python
SupplierClarificationOutboxService