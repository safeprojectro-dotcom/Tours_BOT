# HANDOFF_A5_CLARIFICATION_OUTBOX_ADMIN_REVIEW_STATUS_MANAGEMENT

## Project
Tours_BOT

## Block
A5 — Clarification outbox admin review & status management

## Goal
Let internal admins move supplier clarification outbox items through the workflow (still no supplier send).

## What shipped
- DB: `last_reviewed_at`, `last_reviewed_by_telegram_user_id`, `review_note` on `supplier_clarification_outbox_items` (Alembic `20260617_33`).
- Service: validated transitions only:
  - `draft` → `ready_for_review` | `cancelled`
  - `ready_for_review` → `cancelled` | `sent_externally_later`
- Admin API: `PATCH /admin/supplier-clarification-outbox/{item_id}` with `SupplierClarificationOutboxStatusPatchRequest` (`workflow_status`, optional `review_note` with omit/null semantics, optional `reviewed_by_telegram_user_id`).
- Telegram: outbox list rows open item detail; detail shows timestamps / note; action buttons apply the same transitions; explicit copy that nothing is auto-sent to suppliers.

## Safety
No supplier messaging, publish, scheduler, or domain mutations outside this table.

## Manual checks
From a supplier-offer card with outbox: open list → open item → move status → confirm API `GET` reflects `updated_at` / review fields; confirm no send/publish UI appears.
