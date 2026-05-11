# CURSOR_PROMPT_B15A_ADMIN_PUBLISHING_CONSOLE_DESIGN

Docs-first design step. Do not change application code.

## Context

We completed the B13/B14 chain:

- Supplier Offer #12 → Tour #6 → catalog → Telegram publish → publish audit → execution link → Mini App exact tour route.
- B14D fixed existing Tour #6 boarding data manually.
- B14C fixed future bridge-created supplier tours by materializing boarding points.
- B14F fixed lazy temporary hold expiry persistence.
- B14G recorded production verification:
  - Orders #52/#53 expired correctly as unpaid holds.
  - Tour #6 seats restored from 7 to 10.
  - Offer #12 conversion chain remained green.

Now we need to design the next layer.

Important product insight:

The Telegram channel is not only for Supplier Offer publication.

The channel will publish different commercial and informational messages:

1. New tours from suppliers.
2. Urgent / last seats posts for existing tours.
3. Departure reminders.
4. Individual transport / private transport ads.
5. Informational posts without direct sales.
6. Future unknown marketing formats.

The system must not require new code for every new advertising format.

The admin must not drown in technical fields or approvals.

## Goal

Design an Admin Publishing Console and Channel Publication model.

The model must support:

- Supplier Offer initial publication.
- Existing Tour promotion.
- Last seats / urgency posts.
- Reminder posts.
- Private transport / custom request ads.
- Informational posts.
- Future configurable templates.

The design must keep admin UX simple:

- Today’s publication queue.
- Ready / blocked / needs attention.
- Preview / Publish / Skip / Schedule.
- Hide technical fields by default.
- Show debug fields only in advanced mode.

## Required docs to read

Read:

- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/B14A_CHANNEL_LINK_AND_RESERVATION_READINESS_DIAGNOSTIC.md`
- `docs/B14G_RECORD_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_RESULT.md`
- `docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`
- `docs/B13_CHANNEL_ADAPTER_DESIGN.md`
- `docs/B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/MINI_APP_UX.md`
- `docs/BUSINESS-план-v2.txt` if present

## Required code inspection

Inspect but do not modify:

- Supplier Offer publish flow.
- Showcase message builder.
- Channel adapter.
- Publish attempt audit.
- Supplier Offer review-package / operator workflow.
- Execution link services.
- Mini App supplier-offer landing.
- Mini App exact tour route.
- Custom request / RFQ / private transport related routes if present.
- Admin tour read routes.
- Tour catalog services.

Search for:

- `build_showcase_publication`
- `showcase_preview`
- `publish_showcase_channel`
- `supplier-offers`
- `execution_link`
- `tour_code`
- `custom_request`
- `transport`
- `channel`
- `publication`
- `template`
- `last_seats`
- `showcase_marketing_template`

## Design questions to answer

### 1. Separation of workspaces

Define the separation between:

- Supplier Offer Admin
- Admin Publishing Console

Supplier Offer Admin prepares products.

Publishing Console manages channel communication.

Do not merge these into one confusing workflow.

### 2. Publication object model

Design a conceptual model for:

- Channel Publication
- Publication Template
- Conversion Target
- Safety Policy
- Publication Draft
- Publication Attempt/Audit

The model should support source entities:

- supplier_offer
- tour
- service
- campaign
- manual/info

The model should support conversion targets:

- exact_tour
- supplier_offer_landing
- custom_transport_request
- custom_trip_request
- contact_bot
- mini_app_page
- external_url
- no_cta

### 3. Admin UX

Design the simple admin screen:

- Today’s queue
- Ready / blocked / needs attention
- Preview / Publish / Skip / Schedule

Include examples for:

- New supplier tour.
- Last seats post.
- Private transport ad.
- Info post.

Show what normal admin sees and what advanced/debug mode can show.

### 4. New advertising formats

Explain how new marketing formats can be added without code:

- configurable template;
- existing target type;
- existing safety rules.

Explain when code is still required:

- new Mini App page/form;
- new safety rule;
- new external publication channel;
- new payment/product flow.

### 5. Automation modes

Define modes:

- manual draft
- auto draft
- approval required
- limited auto-publish
- disabled

Define which post types are safe for each mode.

### 6. Scheduler / campaign calendar

Design weekly schedule examples:

- Monday: new tours digest.
- Wednesday/Thursday: existing tour promotion.
- Friday: last seats / final call / private transport promo.

Include anti-spam rules:

- max posts per day;
- no duplicate promotion for same tour within X hours;
- no last-seats post if seats are zero;
- no publish after sales deadline;
- no publish if exact target is unavailable.

### 7. Safety gates

For exact tour target, require:

- tour exists;
- tour open_for_sale;
- departure future;
- catalog listed;
- seats available or valid assisted state;
- reservation allowed by sales_mode_policy;
- Mini App target route known;
- no stale seat fact in generated text.

For custom transport target, require:

- request flow enabled;
- Mini App target route exists;
- operator intake available.

For info/no CTA, require:

- no false booking claim.

### 8. Relation to current Supplier Offer flow

Define new preferred sequence for supplier-offer initial publication:

- packaging approved;
- moderation approved;
- media approved;
- tour bridge created;
- tour catalog active;
- execution link active;
- publication draft target resolved;
- preview;
- publish.

Explain that public channel publish should be the last public step when exact booking destination is ready.

### 9. Migration strategy

Define safe rollout:

- B15A design only.
- B15B read-only publishing console.
- B15C exact-tour CTA for supplier offer posts.
- B15D tour promotion drafts.
- B15E service/custom transport drafts.
- B15F scheduler auto-draft.
- B15G limited auto-publish.

## Deliverable

Create:

`docs/B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md`

The doc must include:

1. Purpose.
2. Problem statement.
3. Workspace separation.
4. Channel Publication conceptual model.
5. Conversion Target registry.
6. Template model.
7. Safety policy model.
8. Admin UX model.
9. Automation modes.
10. Scheduler / campaign calendar.
11. Anti-spam rules.
12. Supplier Offer initial publication sequence.
13. Tour promotion / last seats sequence.
14. Service / private transport ad sequence.
15. Future extensibility.
16. Rollout plan B15B–B15G.
17. Explicit non-goals.

Update:

`docs/CHAT_HANDOFF.md`

Add concise B15A design bullet.

Update:

`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

Add or update item:
- B15 Publishing Console design created.
- Product decision pending/accepted:
  - admin UX;
  - exact-tour CTA;
  - auto-draft vs auto-publish.

Create:

`docs/HANDOFF_B15A_ADMIN_PUBLISHING_CONSOLE_DESIGN_TO_NEXT_STEP.md`

Include:

- design summary;
- recommended rollout;
- next prompt;
- safety boundaries.

## Forbidden

Do not:

- edit app code;
- edit tests;
- add migrations;
- call production APIs;
- mutate production data;
- publish/retry/resend;
- create/close/replace execution links;
- create orders/reservations/payments;
- change CTA behavior in code;
- implement scheduler;
- implement campaign engine.

## After completion report

Return:

1. docs changed;
2. main design decisions;
3. how admin avoids drowning in fields;
4. how new ad formats are added without code;
5. recommended next prompt;
6. `git status --short`;
7. `git diff --stat`;
8. confirmations:
   - docs-only;
   - no app code;
   - no tests;
   - no migrations;
   - no production API calls;
   - no production data mutation;
   - no publish/retry/resend;
   - no execution-link mutation;
   - no orders/payments/reservations;
   - no CTA behavior change.