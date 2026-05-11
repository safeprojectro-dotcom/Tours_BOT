# CURSOR_PROMPT_B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE

Implement the first read-only Admin Publishing Console surface.

This is a safe read-only implementation step.

Do not implement publish/send/schedule/mutation behavior.

## Context

B15A is complete and committed:

- commit: `89ebb6f`
- message: `docs: design admin publishing console`

B15A designed the Admin Publishing Console / Channel Publication model.

Core principles:

- Supplier Offer Admin prepares product/conversion truth.
- Publishing Console manages channel communication.
- Channel Publication = Template + Conversion Target + Safety Policy + Publication Mode.
- Admin should not see technical complexity by default.
- Admin should see:
  - Today’s queue / candidate cards;
  - Ready / blocked / needs attention;
  - target summary;
  - next best action;
  - Preview / Publish / Skip / Schedule as future actions.
- B15B must be read-only.

Relevant closed context:

- B14D/B14F/B14G closed production smoke:
  - Offer #12 → Tour #6 → catalog → publish → execution link → Mini App path.
  - temp hold expiry fixed and production-verified.
- B15A created the design direction for a broader Publishing Console.

## Goal

Create a read-only Admin Publishing Console backend surface that returns publication candidates/cards.

This should not create a new publish pipeline yet.

Use existing data and existing services where possible.

The first B15B scope should focus on read-only candidate visibility for:

1. Supplier Offer initial publication candidate.
2. Existing Tour promotion candidate.
3. Optional placeholder/service candidate only if existing routes/data already support it safely.
4. Blocked candidates with clear reasons.

## Required docs to read first

Read:

- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md`
- `docs/HANDOFF_B15A_ADMIN_PUBLISHING_CONSOLE_DESIGN_TO_NEXT_STEP.md`
- `docs/B14G_RECORD_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_RESULT.md`
- `docs/B14A_CHANNEL_LINK_AND_RESERVATION_READINESS_DIAGNOSTIC.md`
- `docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`
- `docs/B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/MINI_APP_UX.md`

## Required code inspection

Inspect existing patterns before editing:

- admin route structure and auth:
  - `app/api/routes/admin.py`
  - admin token dependency / route conventions
- supplier offer review-package:
  - existing service/read models behind `/admin/supplier-offers/{offer_id}/review-package`
- supplier offer publish/readiness/action gates:
  - operator workflow actions
  - conversion_status_panel
  - linked_tour_catalog
  - execution_links_review
  - showcase_preview
- tour admin read routes:
  - `/admin/tours`
  - `/admin/tours/{id}`
- catalog preparation/listing services
- Mini App catalog/tour detail services
- existing schemas for admin DTOs
- tests for admin/supplier offer review package
- tests for catalog/tour readiness
- publish attempt audit read surfaces

Search for:

- `review-package`
- `operator_workflow`
- `conversion_status_panel`
- `linked_tour_catalog`
- `execution_links_review`
- `showcase_publish_attempts_review`
- `AdminTour`
- `AdminSupplierOffer`
- `TourStatus.OPEN_FOR_SALE`
- `catalog_listed_for_mini_app`
- `sales_mode_policy`
- `showcase_preview`
- `publish_showcase_channel`

## Implementation requirements

### 1. New read-only endpoint

Add an admin read endpoint, for example:

`GET /admin/publishing-console`

Query parameters should be conservative:

- `limit` default 20, max 50
- optional `kind` filter if easy/safe:
  - `supplier_offer_initial`
  - `tour_promotion`
  - `blocked`
  - `ready`
- optional `status` filter if useful:
  - `ready`
  - `blocked`
  - `needs_attention`

If simpler, implement only `limit` for B15B and document future filters.

Must require the same admin auth as other `/admin` routes.

Must be read-only and side-effect free.

### 2. Response model

Create clear admin DTOs.

Suggested top-level response:

```json
{
  "items": [],
  "total_returned": 0,
  "console_notice": "Read-only publishing console preview. No publish, schedule, skip, retry, or send is executed from this view.",
  "debug_notice": "Technical fields are included for diagnostics only.",
  "query_debug": null
}
```

Additional fields per item: see `AdminPublishingConsoleItemRead` in `app/schemas/admin_publishing_console.py` (`candidate_key`, `kind`, `console_status`, `target_summary`, `offer_debug` / `tour_debug`, paths to `review-package` / admin tour).

---

## Completion record (B15B)

**Status:** Implemented (read-only); documentation completed in **`docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md`**.

### Files changed (implementation + docs)

| Area | Path |
|------|------|
| Route | `app/api/routes/admin.py` — `GET /admin/publishing-console` |
| Service | `app/services/admin_publishing_console_service.py` |
| Schemas | `app/schemas/admin_publishing_console.py` |
| Tests | `tests/unit/test_admin_publishing_console.py` |
| Spec | `docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md` |
| Handoff | `docs/HANDOFF_B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE_TO_NEXT_STEP.md` |
| Continuity | `docs/CHAT_HANDOFF.md` (B15B bullet), `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` (B15 item) |
| Prompt | `docs/CURSOR_PROMPT_B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md` (this completion section) |

### Tests run

```bash
python -m pytest tests/unit/test_admin_publishing_console.py -v
```

**Result:** 4 passed (401 gate, response shape, `kind=supplier_offer_initial`, `kind=tour_promotion`).

### Non-goals verified for B15B

No publish, schedule, Telegram send, execution-link mutation, booking/payment/order changes, or CTA behavior change — console is a read aggregation only.