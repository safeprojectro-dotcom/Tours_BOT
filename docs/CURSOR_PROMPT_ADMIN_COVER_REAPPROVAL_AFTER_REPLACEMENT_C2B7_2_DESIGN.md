# CURSOR_PROMPT_ADMIN_COVER_REAPPROVAL_AFTER_REPLACEMENT_C2B7_2_DESIGN

> **Status: ARCHIVE — historical Plan-mode design prompt.** The decision and **as-shipped behavior** are recorded in `docs/HANDOFF_ADMIN_COVER_REAPPROVAL_AFTER_REPLACEMENT_C2B7_2_DESIGN.md`. **Do not run this file as a greenfield implementation prompt.**

## Canonical pointers

- **`docs/CHAT_HANDOFF.md`** — session continuity (**Slice C2B7.2** and related showcase **`/`** operator-workflow slices).
- **`docs/HANDOFF_ADMIN_COVER_REAPPROVAL_AFTER_REPLACEMENT_C2B7_2_DESIGN.md`** — resolved decision, operational flow, boundaries, code pointers.

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode (historical)

Use the strongest available reasoning model.

Originally intended: **Cursor mode: Plan** — design / safety policy only (“do not change code until design approval”). That phase is **complete**; Telegram **`OK poză` / `OK photo`** + HTTP **`POST …/media/approve-for-card`** are both supported per handoff.

---

## Functional block

ADMIN / SUPPLIER COVER REPLACEMENT PATH — C2B7.2

Re-approve cover after replacement.

---

## Context

Upstream slices **implemented and deployed**:

### C2B4

Telegram admin Preview sends local photo + showcase caption to admin private chat.

### C2B5

Review-package / `operator_workflow` includes deterministic cover media quality warnings.

### C2B6

Telegram admin `Cere poză` / `Request photo` records:

- `packaging_draft_json.media_review.status = replacement_requested`
- `reviewed_by = telegram:{admin_id}`
- does not change `cover_media_reference`
- does not publish
- after confirm:
  - C2B5 warnings surface `media_review_replacement_requested`
  - `request_cover_photo_replacement.enabled = False`

### C2B7.1

Admin endpoint added and deployed:

```text
PUT /admin/supplier-offers/{offer_id}/cover
```

Body: narrow replacement of `SupplierOffer.cover_media_reference` (validated schemes). **Does not** auto-approve media for card; **does not** mutate publish lifecycle.

### C2B7.2 — design outcome (see HANDOFF)

**Problem:** After `PUT …/cover`, `media_review` can remain stale until `approve_for_card` runs again.

**Decision (resolved):** Operators may complete re-approval via **HTTP** `POST /admin/supplier-offers/{offer_id}/media/approve-for-card` **or** Telegram **`OK poză` / `OK photo`** (confirmation, re-read `review-package`, `SupplierOfferMediaReviewService.approve_for_card`, `reviewed_by = telegram:{admin_id}`). Boundaries: no publish, no auto-approve on `PUT …/cover`, no bridge/catalog/execution-link.

Full operational flow and code pointers: **`docs/HANDOFF_ADMIN_COVER_REAPPROVAL_AFTER_REPLACEMENT_C2B7_2_DESIGN.md`**.
