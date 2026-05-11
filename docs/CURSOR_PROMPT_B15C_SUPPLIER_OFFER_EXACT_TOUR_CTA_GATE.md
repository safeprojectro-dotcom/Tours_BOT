# CURSOR_PROMPT_B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE

Implement B15C safely.

## Context

B15A is complete:
- `89ebb6f docs: design admin publishing console`

B15B is complete:
- `785acb9 feat: add read-only admin publishing console`
- Added read-only `GET /admin/publishing-console`
- No publish/mutation behavior.

Now implement the supplier-offer exact-tour CTA gate.

## Product decision

For supplier-offer channel posts, the public channel `Rezervă` CTA must open the exact Mini App tour:

- Desired:
  - `Rezervă -> /tours/{tour_code}`

Not preferred for new supplier-offer channel posts:

- `Rezervă -> /supplier-offers/{offer_id}`

Reason:

The Telegram channel post describes a concrete tour. When a customer clicks `Rezervă`, they should land directly on the exact bookable tour in Mini App.

## Existing problem

Current old sequence allowed:

1. moderation approved
2. publish showcase channel
3. create execution link later

This means the channel post is generated before the exact tour conversion target is ready, so the CTA uses stable supplier-offer landing.

B15C should make the safe supplier-offer publish sequence:

1. packaging approved
2. media/card approved
3. moderation approved
4. tour bridge exists
5. linked tour is open_for_sale / catalog-listed
6. active execution link exists
7. showcase publish is allowed
8. `Rezervă` points to exact `/tours/{tour_code}`

Public channel publish should be the final public step, after exact conversion target is ready.

## Goal

For supplier-offer showcase channel publication:

1. Allow/expect execution link to exist before channel publish when prerequisites are met.
2. Gate `publish_showcase_channel` on active execution link for supplier-offer posts.
3. Generate `Rezervă` CTA as exact Mini App tour URL when active execution link exists.
4. Keep `Detalii` as bot deep-link / supplier-offer context if currently used.
5. Preserve old published posts and existing data. Do not edit Telegram messages.
6. Do not change Layer A booking/payment/reservation logic.

## Required docs to read

Read before coding:

- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md`
- `docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md`
- `docs/B14A_CHANNEL_LINK_AND_RESERVATION_READINESS_DIAGNOSTIC.md`
- `docs/B14G_RECORD_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_RESULT.md`
- `docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`
- `docs/B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/MINI_APP_UX.md`

## Required code inspection

Inspect before changing:

- showcase builder:
  - `build_showcase_publication`
  - `_cta_block_html`
  - `mini_app_supplier_offer_url`
  - `mini_app_tour_detail_url`
  - `cta_rezerva_href`
- supplier offer moderation/publish:
  - `SupplierOfferModerationService.publish`
  - showcase channel payload/preview routes
- operator workflow:
  - `publish_showcase_channel`
  - `create_execution_link`
  - `conversion_status_panel`
  - `execution_links_review`
  - `linked_tour_catalog`
- execution link service/repo:
  - create execution link endpoint/service
  - prechecks that currently require lifecycle `published`
- admin publishing console:
  - make sure B15C does not break read-only cards
- tests around:
  - supplier offer review package
  - showcase publish
  - execution link creation
  - supplier offer publication payload
  - B15B publishing console

Search terms:

- `build_showcase_publication`
- `_cta_block_html`
- `cta_rezerva_href`
- `mini_app_supplier_offer_url`
- `mini_app_tour_detail_url`
- `publish_showcase_channel`
- `create_execution_link`
- `execution_links_review`
- `can_create_execution_link`
- `lifecycle_status`
- `published`
- `review-package`
- `showcase-preview`
- `showcase-channel-payload`
- `publish`

## Implementation requirements

### 1. Execution link before publish

Update execution-link precheck/gate so an execution link can be created before `lifecycle_status == published`, but only when this is safe.

Allow pre-publish execution link only if:

- supplier offer exists;
- packaging is approved for publish;
- moderation is approved or equivalent lifecycle state is allowed by current domain model;
- active tour bridge exists;
- linked tour exists;
- linked tour is `open_for_sale`;
- linked tour is catalog-listed for Mini App semantics;
- linked tour departure is in the future;
- linked tour is not blocked by sales deadline;
- no active execution link already exists.

If some checks are already represented by existing review-package/linked_tour_catalog logic, reuse them.

Do not create execution links for:
- rejected offers;
- unapproved packaging;
- missing bridge;
- draft/non-sale tours;
- past departure;
- inactive catalog;
- duplicate active link.

Important:
- Existing published-offer execution-link behavior must continue to work.
- Do not require channel publish before execution link anymore.

### 2. Publish gate requires exact active execution link

For supplier-offer channel publish readiness:

`publish_showcase_channel` should be enabled only when:

- existing publish gates pass:
  - packaging approved;
  - moderation approved;
  - media/card approved;
  - showcase preview/payload safe;
- active execution link exists;
- active execution link points to linked tour;
- linked tour is open_for_sale and catalog-listed;
- exact tour URL can be built.

If active execution link is missing, disable publish with clear reason:

`Execution link is required before channel publish because Rezervă must open the exact Mini App tour.`

or Romanian equivalent where translations exist.

### 3. Showcase CTA

When building supplier-offer showcase publication for preview/payload/publish:

- `Detalii` can remain:
  - `https://t.me/...start=supoffer_{offer_id}`
- `Rezervă` must become:
  - `{TELEGRAM_MINI_APP_URL}/tours/{tour_code}`

where `tour_code` comes from the active execution link / linked tour.

If no exact tour target is available:
- preview may show blocked/warning;
- publish must not proceed.

Do not silently fall back to `/supplier-offers/{offer_id}` for publish when exact target is required.

For local preview/read-only surfaces, if exact target missing, show:
- current fallback preview only if clearly marked blocked;
- or return missing target state.

### 4. Backward compatibility

Do not modify existing published Telegram posts.
Do not migrate old publish attempts.
Do not change `/supplier-offers/{id}` landing route.
Do not remove supplier offer landing — it is still useful for Detalii/fallback/older posts.
Do not break `/start supoffer_<id>` behavior.
Do not break B15B read-only endpoint.

### 5. Tests

Add/update focused tests.

Required test coverage:

1. Execution link can be created before publish when:
   - packaging approved;
   - moderation approved;
   - bridge active;
   - linked tour open_for_sale/catalog-listed/future.
2. Execution link cannot be created before publish when bridge/tour/catalog is missing or tour is draft.
3. `publish_showcase_channel` disabled when no active execution link exists.
4. `publish_showcase_channel` enabled when active execution link exists and all other gates pass.
5. Showcase preview/payload `cta_rezerva_href` is `/tours/{tour_code}` when active execution link exists.
6. Publish refuses or stays disabled when exact tour target is missing.
7. Existing supplier offer landing URL builder remains available.
8. B15B `/admin/publishing-console` tests still pass.
9. Existing publish audit tests still pass.
10. No Layer A reservation/payment tests broken.

Run at minimum:

- `python -m pytest tests/unit/test_admin_publishing_console.py -q`
- existing supplier offer review/publish tests
- existing execution link tests, if present
- existing showcase preview/payload tests, if present

If exact test file names differ, discover and run the relevant unit tests.

### 6. Documentation updates

Create:

`docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`

Include:

- purpose;
- old vs new sequence;
- execution link before publish gate;
- publish requires active exact target;
- `Rezervă -> /tours/{tour_code}`;
- `Detalii -> supoffer` remains;
- backward compatibility;
- tests;
- limitations;
- production smoke checklist;
- next steps.

Update:

`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`

Reflect new sequence for new supplier-offer posts:

- create/link tour;
- activate catalog;
- create execution link;
- preview exact CTA;
- publish.

Update:

`docs/B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE.md`

Add note that B15C changes exact target readiness expectations for supplier offer publish.

Update:

`docs/CHAT_HANDOFF.md`

Add concise B15C bullet.

Update:

`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

Update B15 item:
- B15C implemented exact-tour CTA gate for supplier offer channel publish.
- Remaining future items:
  - tour promotion drafts;
  - private transport ads;
  - scheduler/auto-draft;
  - limited auto-publish.

Create:

`docs/HANDOFF_B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE_TO_NEXT_STEP.md`

Include:

- what changed;
- files;
- tests;
- production smoke;
- known limitations;
- next prompt suggestion.

## Production smoke checklist to document only

Do not run production calls from Cursor.

The runbook should suggest manual smoke after deploy:

1. Create/choose new supplier offer with future departure.
2. Prepare packaging/media/moderation.
3. Link/create tour.
4. Activate catalog.
5. Create execution link before publish.
6. GET review-package:
   - publish_showcase_channel enabled;
   - cta_rezerva_href points to `/tours/{tour_code}`;
   - conversion_status_panel shows exact target ready.
7. Publish.
8. Confirm channel post `Rezervă` opens exact tour in Mini App.
9. Confirm no booking/payment behavior changed.

## Forbidden

Do not:

- edit existing Telegram posts;
- publish to Telegram from Cursor;
- call production APIs;
- mutate production data;
- add migrations unless absolutely unavoidable;
- create orders/reservations/payments;
- change Layer A booking/payment logic;
- change temp hold expiry logic;
- remove supplier offer landing;
- implement tour promotion drafts;
- implement private transport ads;
- implement scheduler;
- implement auto-publish;
- change B15B endpoint semantics except if needed to reflect exact target status read-only.

## After completion report

Return:

1. files changed;
2. old vs new sequence summary;
3. exact CTA behavior summary;
4. execution-link pre-publish gate summary;
5. publish gate summary;
6. tests added/run and results;
7. docs updated;
8. production smoke checklist location;
9. `git status --short`;
10. `git diff --stat`;
11. confirmations:
   - no production API calls;
   - no production data mutation;
   - no Telegram publish/send/retry from Cursor;
   - no existing Telegram post edits;
   - no orders/payments/reservations;
   - no Layer A booking/payment changes;
   - no scheduler/auto-publish;
   - no migrations unless explicitly justified.