# CURSOR_PROMPT_B15D_ADMIN_PUBLISHING_CONSOLE_RICH_READ_VIEW

## Context

Project: Tours_BOT.

B15C exact CTA chain is closed.

Recent stable checkpoint:
- `d4489e1 docs: close B15C exact CTA chain checkpoint`
- `f444a15 fix: align supplier offer publish copy with execution link order`
- `c3dda1c fix: keep admin on supplier offer after bridge actions`
- `a19a1ab docs: record B15C5 direct Mini App smoke result`
- `06741d fix: support direct Mini App short-name tour links`

Accepted B15C chain:

Supplier offer approved/packaged
→ Tour bridge created/linked
→ Tour activated for Mini App catalog
→ Active execution link created
→ Showcase/channel publish allowed
→ Channel `Rezervă` opens exact Mini App tour via Telegram Mini App short-name link
→ Layer A handles reservation/payment.

B15B already created:
- `GET /admin/publishing-console`
- read-only admin publishing console
- candidate types including supplier-offer initial cards and tour promotion candidates
- no send path
- no scheduler
- no mutation

## Goal

Implement B15D as a safe richer read/admin view for the Admin Publishing Console.

This is primarily API/read-model polish, not publishing automation.

The console should help the admin understand:

1. What is ready to publish.
2. What is blocked.
3. What the next best action is.
4. Whether the conversion target is exact and safe.
5. Whether the candidate has B15C-compliant CTA readiness.
6. What links/admin paths can be opened next.

## Required behavior

Extend the existing read-only `GET /admin/publishing-console` response with richer fields, while preserving backward compatibility where possible.

Suggested additions per item:

- `readiness_summary`
- `readiness_level`, e.g. `ready`, `needs_action`, `blocked`, `published`, `unknown`
- `conversion_target_kind`, e.g. `exact_tour`, `supplier_offer_landing`, `none`
- `conversion_target_url`
- `cta_safety_status`, e.g. `exact_tour_ready`, `missing_execution_link`, `tour_not_listed`, `media_blocked`, `already_published`
- `primary_blocker`
- `blocker_codes`
- `next_action_code`
- `next_action_label`
- `admin_action_path`
- `preview_path`
- `source_status_summary`
- `audit_hint`

Names may differ if current schema style suggests better naming, but keep them explicit and stable.

## Safety requirements

Do NOT:
- add publish mutation to this endpoint;
- add scheduler;
- add auto-draft;
- add auto-publish;
- send Telegram messages;
- mutate supplier offers, tours, execution links, orders, payments, or reservations;
- change Layer A;
- change B15C CTA/publish gates;
- change Mini App routing;
- create migrations unless absolutely unavoidable.

This must remain read-only.

## Source of truth

Use existing services/read surfaces as much as possible:
- supplier offer review-package / conversion status panel;
- publishing console service from B15B;
- existing tour catalog visibility/read models;
- existing admin paths;
- existing B15C publish readiness.

Do not duplicate business rules in the console layer. The console should aggregate and summarize existing truth.

## API compatibility

If the existing DTOs are used by tests, update them carefully.

Existing fields should continue to work unless there is a strong reason to change them.

Additive DTO changes are preferred.

## Tests

Add/update focused unit tests for:

1. Ready supplier offer candidate with exact tour CTA:
   - readiness says ready;
   - conversion target is exact tour;
   - CTA safety says exact tour ready.

2. Blocked supplier offer candidate missing execution link:
   - readiness says blocked/needs_action;
   - primary blocker references execution link;
   - next action points to execution-link or bridge/catalog prerequisite.

3. Tour promotion candidate:
   - still appears as before;
   - has a reasonable readiness summary;
   - no supplier-offer-only fields are misleading.

4. Existing B15B shape still works.

Suggested command:

```powershell
python -m pytest tests/unit/test_admin_publishing_console.py -q