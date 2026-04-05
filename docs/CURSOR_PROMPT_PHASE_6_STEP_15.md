# Phase 6 / Step 15 — completed (archive)

Implemented in code:

- **`POST /admin/tours/{tour_id}/archive`** — allowed from `draft`, `open_for_sale`, `collecting_group`, `guaranteed` → `sales_closed`; idempotent if already `sales_closed`.
- **`POST /admin/tours/{tour_id}/unarchive`** — from `sales_closed` → `open_for_sale`; idempotent if already `open_for_sale`; 400 if status is neither archived nor open-for-sale path.

Semantics and constants: `app/services/admin_tour_write.py` (`_TOUR_ARCHIVE_SOURCE_STATUSES`, `_TOUR_ARCHIVED_STATUS`).

Tests: `tests/unit/test_api_admin.py`.

Handoff: `docs/CHAT_HANDOFF.md` (checkpoint Phase 6 / Step 15).
