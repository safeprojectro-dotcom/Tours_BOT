# CURSOR_PROMPT_B12C_DOCS_FINALIZE

Finalize B12C documentation only.

B12C is already implemented:

- Telegram admin detail has `Template / Șablon` button.
- Button is shown when `operator_workflow.patch_showcase_marketing_template.enabled`.
- Placement: after `Approve text / Aprobă text`, before bridge/publish actions.
- Template picker shows:
  - inferred template;
  - effective template;
  - selected template or none;
  - notes from review-package;
  - blocked last-seats note when verified seats are required.
- Direct template buttons apply safe templates through `SupplierOfferPackagingReviewService.patch_showcase_marketing_template`.
- Handler re-reads review-package and checks workflow/action + `_template_id_allowed_for_telegram_direct_apply`.
- `LAST_SEATS_URGENT` uses FSM state:
  - `AdminModerationState.awaiting_showcase_template_last_seats`
  - requires positive integer input;
  - then PATCHes `last_seats_urgent + live_seats_remaining`.
- Clear selection uses `template_id = null`.
- Back / cancel returns to fresh offer detail.
- Persistence remains B12B service path with approved packaging lock and `flag_modified`.
- No publish output changes.
- No publish readiness changes.
- No auto-publish.
- No packaging approval.
- No lifecycle/media_review changes except selected template metadata.
- No Mini App.
- No booking/payment/orders.
- No migrations.

## Required docs updates

Update:

`docs/B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md`

Add B12C section:
- Telegram template picker;
- safe direct apply;
- last-seats positive integer FSM;
- clear selection;
- validation/re-read;
- no publish output/readiness changes;
- no fake urgency/discount/availability.

Update:

`docs/CHAT_HANDOFF.md`

Add B12C completed entry:
- Telegram Template/Șablon UI implemented;
- gated by `patch_showcase_marketing_template.enabled`;
- same B12B service path;
- last-seats requires verified positive count;
- clear supported;
- no publish output/readiness/Mini App/booking/orders/migrations.

Create/update:

`docs/HANDOFF_B12C_TELEGRAM_TEMPLATE_SELECTION_UI_TO_NEXT_STEP.md`

Include:
- checkpoint;
- files changed summary;
- Telegram behavior;
- callback prefixes/FSM state summary;
- validation/re-read behavior;
- tests run;
- non-goals preserved;
- next likely steps:
  1. B13 — channel adapter design;
  2. Production content QA;
  3. optional template copy polish.

Update:

`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`

Add short operator note:
- Template / Șablon in Telegram changes packaging metadata only.
- It does not publish.
- It does not approve text.
- Last seats requires a verified positive count.
- Final public publish still follows existing publish gate.

Update `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` only if a real open issue appears.

## Forbidden

Do not change app code.
Do not change tests.
Do not add migrations.
Do not change publish output.
Do not change publish readiness.
Do not touch Mini App.
Do not touch booking/payment/orders.

## After completion report

Return:
1. docs changed;
2. whether OPEN_QUESTIONS changed and why;
3. tests already run;
4. `git status --short`;
5. `git diff --stat`;
6. confirmation:
   - docs-only for this finalize pass;
   - no code changes in this pass;
   - no tests changed in this pass;
   - no migrations;
   - no publish output changes;
   - no publish readiness changes;
   - no Mini App;
   - no booking/payment/orders.