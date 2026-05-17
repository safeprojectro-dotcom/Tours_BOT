
---

# HANDOFF

```md
# HANDOFF_A4_SUPPLIER_CLARIFICATION_OUTBOX_FOUNDATION

## Project
Tours_BOT

## Block
A4 — Supplier Clarification Outbox Foundation

## Goal
Persist supplier clarification drafts as internal admin outbox work items so clarification tasks are not lost.

## Scope
- internal outbox DB table
- model/schema/repository/service
- protected admin API create/list/detail
- Telegram cockpit button to save clarification draft
- no sending

## Key safety rule
A4 saves an internal draft only. It does not send anything to suppliers.

## Status lifecycle
- draft
- ready_for_review
- cancelled
- sent_externally_later

## MVP data model (A4 correction)
- A4 MVP binds each outbox row to `supplier_offer_id` only (FK to `supplier_offers`).
- A future generalization to `source_type` / `source_id` (tour, custom_request, etc.) is out of scope for this block; it can be added later if needed.
- This matches the product surface: the save/list controls exist only on supplier-offer cockpit cards.

## No-go
No supplier notification, no Telegram publish, no scheduler, no AI, no external provider calls, no Layer A, no B11, no booking/payment/order mutation.

## Manual UAT
Open supplier-offer cockpit card with supplier draft, click save draft, confirm saved/replayed existing outbox item and no send/publish/schedule buttons.