# CURSOR_PROMPT_MEDIA_STORAGE_PIPELINE_READINESS_B7_4A

You are working on Tours_BOT.

Run B7.4A: media storage pipeline readiness/design audit for Supplier Offer showcase media.

This is a Plan/readiness step, not implementation.

## Current checkpoint

C2B8B is closed:
- Telegram admin `Publică / Publish` implemented.
- Publish is gated by `operator_workflow.actions.publish_showcase_channel.enabled`.
- Media blockers from review-package can disable publish.

C2B10T-A/B/C are closed:
- Telegram operator conversion chain exists:
  - Link tour
  - List for sale
  - Publish
  - Booking link
- All actions are gated by operator_workflow and use double review-package reads.

C2B10T-D is docs/verification:
- OPS smoke/runbook validation documented.
- Full live OPS smoke remains operator-owned.

Current media state:
- B7.3 metadata-only publish-safe block exists.
- Supplier offer cover may be referenced as `telegram_photo:{file_id}`.
- Current MVP does not yet download/store media bytes.
- Durable storage / object storage / Telegram getFile pipeline remains future work.
- Published showcase should not depend on unstable/raw media assumptions once storage pipeline is introduced.

## Goal

Audit current media pipeline and propose the safest next implementation slice for durable media storage.

Do not implement code yet.

## Core principles

Preserve:

1. No public publish with unreviewed or unsafe media.
2. Media review state remains authoritative for publish readiness.
3. `cover_media_reference` is supplier/source reference, not necessarily durable public media.
4. `media_review.status` and snapshot logic must not be broken.
5. `approve_for_card` / OK photo behavior must remain stable.
6. `request replacement` must remain stable.
7. Publishing readiness must still flow through review-package/operator_workflow.
8. No booking/payment/orders changes.
9. No Mini App changes unless only docs mention future usage.
10. PostgreSQL-first and service-layer ownership.

## Documents to inspect

Inspect if present:

- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`
- `docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A.md`
- `docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`
- `docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`
- any B7.3/B7.4 media docs/prompts/handoffs
- any media review / publish-safe docs

If files are missing, report clearly.

## Code areas to inspect

Read-only inspect:

- supplier offer model fields:
  - `cover_media_reference`
  - `packaging_draft_json`
  - media review fields / JSON
- `supplier_offer_cover_media_quality_review.py` (module functions such as `evaluate_cover_media_quality_review`, not a `*Service` class)
- `supplier_offer_media_review_service.py`
- `supplier_offer_card_render_preview.py`
- review-package service
- operator_workflow readiness for publish/media gates
- Telegram OK photo / request photo handlers
- Telegram publish service/path
- current Telegram Bot API client usage if any
- settings/config for Telegram bot token and storage env vars
- current media/file/object storage abstractions, if any
- tests around:
  - media review
  - B7.1/B7.2/B7.3
  - publish readiness
  - review package

## What to report

Produce a concise audit with:

### 1. Current media data model

List current fields and JSON blocks related to:

- raw cover reference;
- media review;
- publish_safe block;
- card preview/render preview;
- Telegram photo file id;
- any stored public URL/object key if already present.

### 2. Current media workflow

Describe current flow:

```text
supplier sends cover
-> cover_media_reference stored
-> media review
-> OK photo / replacement requested
-> publish_safe metadata
-> publish readiness gate
-> Telegram preview/publish path
```

---

## Completion (B7.4A saved to repo)

**Done (docs):** Findings and phased plan are recorded in [`docs/B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md`](B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md). Continuity: [`docs/HANDOFF_MEDIA_STORAGE_PIPELINE_READINESS_B7_4A_TO_NEXT_STEP.md`](HANDOFF_MEDIA_STORAGE_PIPELINE_READINESS_B7_4A_TO_NEXT_STEP.md) and B7.4A bullet in [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md). **Next implementation slice:** B7.4B — ingestion contract/design doc. This prompt step did not modify application code, tests, migrations, or live systems.