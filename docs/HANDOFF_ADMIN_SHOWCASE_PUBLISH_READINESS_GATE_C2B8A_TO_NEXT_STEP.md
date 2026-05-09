# HANDOFF_ADMIN_SHOWCASE_PUBLISH_READINESS_GATE_C2B8A_TO_NEXT_STEP

Project: Tours_BOT

## Functional block

C2B8A — Publish readiness gate before Telegram Publică

## Status

**Implemented** (read-model / `operator_workflow` only). **`POST …/publish`** handler semantics unchanged.

## Purpose (historical)

Before adding Telegram admin **`Publică`**, make **`publish_showcase_channel`** safe in **`operator_workflow`** / **`GET …/review-package`**.

## Safety principle

No future public Telegram publish shortcut should trust **`enabled=True`** on **`publish_showcase_channel`** while hard cover/media blockers remain (subset of C2B5 warning codes).

## Shipped behavior

**`publish_showcase_channel`** is **`enabled`** only when **all** hold:

- **`lifecycle_status`** is **`approved`** (published / draft / etc. stay off via existing lifecycle / **`can_publish_now`** chain).
- **`showcase_preview.can_publish_now`** is **`true`** (channel id + bot token + lifecycle technical readiness).
- **`packaging_status`** is **`approved_for_publish`**.
- **`cover_media_publish_blocking_reasons`** (`app/services/supplier_offer_cover_media_quality_review.py`) returns **no** reasons using **`cover_media_quality_review.warnings`** + **`showcase_preview.publication_mode`**:
  - **Always block** on: negative **`media_review`** codes, **`media_review_cover_snapshot_mismatch`**, **`showcase_photo_url_*`** conflicts (exact codes in **`COVER_MEDIA_PUBLISH_BLOCK_CODES_ALWAYS`**).
  - **Block only when `publication_mode == photo_with_caption`:** **`cover_media_not_sendable_for_showcase`**, **`cover_media_not_explicitly_approved_for_card`**.
  - **Never block** on **`cover_media_missing_showcase_photo`** alone (text-only channel post allowed per policy).

**`disabled_reason`** aggregates lifecycle / config / packaging strings plus **`Cover/media gate: [code] …`** lines.

## Non-goals (respected)

No Telegram **`Publică`** button; no new callbacks; **`ModerationService.publish`** untouched; no Mini App / booking / Tour / migrations.

## Code / docs pointers

- Gating: `app/services/supplier_offer_operator_workflow.py` (**`publish_showcase_channel`**).
- Blocking helper + code sets: `app/services/supplier_offer_cover_media_quality_review.py` (**`cover_media_publish_blocking_reasons`**, **`COVER_MEDIA_PUBLISH_*`**).
- Tests: `tests/unit/test_supplier_offer_cover_media_quality_review.py`, `tests/unit/test_supplier_offer_review_package.py`.
- Continuity: [`CHAT_HANDOFF.md`](CHAT_HANDOFF.md) (**Slice C2B5 / C2B8A**).

## Operational note

**`POST …/publish`** can still be called while **`publish_showcase_channel`** is **`disabled`** — automation should **`prefer`** aligning with **`review-package`** before calling **`publish`**.

## Next step

After C2B8A is **production-smoked** on a real channel/staging:

**C2B8B** — Telegram admin **`Publică`** button with strict confirmation (reuse same **`enabled`** / re-read **`review-package`** pattern as C2B1/C2B7.2).
