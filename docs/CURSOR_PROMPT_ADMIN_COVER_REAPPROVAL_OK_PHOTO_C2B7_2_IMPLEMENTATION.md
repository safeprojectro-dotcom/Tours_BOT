# CURSOR_PROMPT_ADMIN_COVER_REAPPROVAL_OK_PHOTO_C2B7_2_IMPLEMENTATION

> **Status: ARCHIVE / already implemented. Do not run as an implementation prompt.** **C2B7.2 Telegram OK photo** is in production code (`admin_ops_operator_workflow_c2b7_2_ok_photo`, `approve_cover_for_card`). Do not re-implement from this document.

## Canonical pointers

- **`docs/CHAT_HANDOFF.md`** — **Slice C2B7.2** summary.
- **`docs/HANDOFF_ADMIN_COVER_REAPPROVAL_AFTER_REPLACEMENT_C2B7_2_DESIGN.md`** — behavior, gates, file pointers.

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode (historical)

Use the strongest available reasoning model.

Originally: **Cursor mode: Agent** — implement Telegram **`OK poză` / `OK photo`** calling **`SupplierOfferMediaReviewService.approve_for_card`** with the same confirmation pattern as other C2B mutations. **This work is done in the codebase** (see handoff).

---

## Functional block

ADMIN / SUPPLIER COVER REPLACEMENT PATH — C2B7.2

**Historical goal:** Add a narrow Telegram admin action to re-approve the current cover after replacement (alongside existing HTTP approve-for-card).

---

## Context

Upstream slices **implemented and deployed**:

### C2B4

Telegram admin Preview sends local photo + showcase caption to admin private chat.

### C2B5

Review-package / `operator_workflow` includes deterministic cover media warnings.

### C2B6

Telegram admin `Cere poză` / `Request photo` records:

- `packaging_draft_json.media_review.status = replacement_requested`
- `reviewed_by = telegram:{admin_id}`
- does not change `cover_media_reference`
- does not publish
- `request_cover_photo_replacement` hidden/disabled when replacement is already recorded per workflow rules

### C2B7.1

Admin endpoint added and deployed:

```text
PUT /admin/supplier-offers/{offer_id}/cover
```

### C2B7.2 — shipped summary

- **`operator_workflow`** action **`approve_cover_for_card`** when enabled (sendable cover, not already aligned with approved snapshot).
- Handler **`admin_ops_operator_workflow_c2b7_2_ok_photo`** in `app/bot/handlers/admin_moderation.py`; propose → confirm → re-read `GET …/review-package` → execute only if still enabled.
- **`approve_cover_for_card_operator_action_disabled_reasons`** in `app/services/supplier_offer_cover_media_quality_review.py`.
- Tests: e.g. `tests/unit/test_operator_workflow_c2b7_2_specs.py`, coverage in `test_supplier_offer_review_package.py`, keyboard specs in `test_operator_workflow_c2b3_keyboard.py`.

For narrative and boundaries, use **`docs/HANDOFF_ADMIN_COVER_REAPPROVAL_AFTER_REPLACEMENT_C2B7_2_DESIGN.md`**.
