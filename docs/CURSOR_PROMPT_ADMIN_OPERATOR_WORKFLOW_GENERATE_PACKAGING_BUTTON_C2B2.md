# CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_GENERATE_PACKAGING_BUTTON_C2B2

> **Status: ARCHIVE / already implemented. Do not run as an implementation prompt.** See `docs/HANDOFF_ADMIN_OPERATOR_WORKFLOW_GENERATE_PACKAGING_BUTTON_C2B2_TO_NEXT_STEP.md` and `docs/CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_C2B2_DOCS_SYNC.md`.

## Canonical pointers

- **`docs/CHAT_HANDOFF.md`** — **Slice C2B2** summary.
- **`docs/HANDOFF_ADMIN_OPERATOR_WORKFLOW_GENERATE_PACKAGING_BUTTON_C2B2_TO_NEXT_STEP.md`** — shipped labels, behavior, tests **`/`** handler pointers.
- **`docs/CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_C2B2_DOCS_SYNC.md`** — docs-only sync checklist used after implementation.

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode (historical)

Use the strongest available reasoning model.

Originally: **Cursor mode: Agent** — add Telegram **`generate_packaging_draft`** with mandatory confirmation. **C2B2 is shipped**; use the handoff for current truth.

---

## Functional block

ADMIN OPERATOR WORKFLOW — C2B2

**Historical scope:** Telegram workflow mutation action:

```text
generate_packaging_draft
```

with mandatory confirmation.

---

## Context

Prerequisite slices **already implemented and deployed**:

- Slice B: `GET /admin/supplier-offers/{offer_id}/review-package` includes `operator_workflow`.
- Slice C1/C1.1: Telegram admin card displays compact `operator_workflow`.
- Slice C2A: read-only workflow buttons `review_package_refresh`, `get_showcase_preview`.
- Slice C2B design: mutations require confirmation; re-read review-package before execute; execute only if action still enabled; no hidden chained actions.
- Slice C2B1: `approve_packaging_for_publish` with confirmation; `SupplierOfferPackagingReviewService.approve`; no publish / bridge / catalog / execution-link; legacy Aprobă / Respinge unchanged.

### C2B2 (shipped)

- Button **Pregătește** (RO) / **Prepare** (EN); messages `admin_offer_ow_pkg_gen_*` in `app/bot/messages.py`.
- Handler `admin_ops_operator_workflow_c2b2_generate_packaging` in `app/bot/handlers/admin_moderation.py`; callbacks `ADMIN_OPS_OW_PKG_*` in `app/bot/constants.py`.
- Confirm runs **`SupplierOfferPackagingService.generate_and_persist`** only; **does not** auto-approve packaging (C2B1 stays separate).

---

## Strict boundaries (historical — still policy)

Do not change booking/payment/order/reservation.

Do not change Mini App UI.

Do not change Telegram showcase template.

Do not change publish behavior.

Do not change Tour bridge/catalog activation behavior.

Do not add migrations.

Do not call external AI directly from Telegram.

Do not add web UI.

Do not add batch/macro endpoints.

Do not auto-publish.

Do not auto-create Tour.

Do not auto-activate catalog.

Do not auto-create execution link.

Do not add Telegram buttons for:

- `approve_offer_moderation`
- `create_tour_bridge`
- `activate_tour_for_catalog`
- `publish_showcase_channel`
- `create_execution_link`

Do not duplicate legacy Aprobă / Respinge.

C2B2 scope was only:

```text
generate_packaging_draft
```
