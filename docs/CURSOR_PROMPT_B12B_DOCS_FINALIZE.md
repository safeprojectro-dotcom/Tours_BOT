# CURSOR_PROMPT_B12B_DOCS_FINALIZE

Finalize B12B documentation only.

B12B is already implemented:

- GET `/admin/supplier-offers/{id}/review-package` includes `showcase_template_preview`.
- `showcase_template_preview` includes:
  - inferred template;
  - effective template;
  - optional admin selection;
  - RO HTML fact lines for ops;
  - template choices;
  - invalid selection notes;
  - `channel_publish_unchanged: true`.
- PATCH `/admin/supplier-offers/{id}/packaging/showcase-template`
  - body: `AdminPackagingShowcaseTemplatePatch`
  - writes admin selection into `packaging_draft_json.showcase_marketing_template_library_v1`
  - supports `template_id: null` to clear selection
  - `last_seats_urgent` requires `live_seats_remaining >= 1`
  - blocked when packaging is `approved_for_publish`
- Regenerate packaging preserves admin template selection / live seats.
- `flag_modified(row, "packaging_draft_json")` is used after nested JSONB mutation.
- Operator workflow exposes `patch_showcase_marketing_template` with method PATCH.
- Telegram detail shows a short B12B read-only block when preview exists.
- Channel publish output remains unchanged.
- No publish readiness changes.
- No Mini App / booking / payment / orders.
- No migrations.

## Required docs updates

Update / complete:

`docs/CURSOR_PROMPT_B12B_ADMIN_TEMPLATE_PREVIEW_SELECT.md`

Close the truncated prompt and add a completion note with:
- implemented behavior;
- tests run;
- explicit safety confirmations.

Update:

`docs/B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md`

Add B12B section:
- review-package preview;
- PATCH selection endpoint;
- template selection rules;
- last-seats validation;
- clear selection behavior;
- approved packaging lock;
- publish output unchanged.

Update:

`docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`

Add admin/operator note:
- template preview/selection is packaging metadata only;
- selecting template does not publish;
- selecting template does not approve packaging;
- channel publish still uses existing publish path until later step.

Update:

`docs/CHAT_HANDOFF.md`

Add B12B completed entry:
- preview exposed;
- admin selection endpoint;
- Telegram read-only summary;
- channel publish unchanged;
- no publish readiness changes;
- no Mini App / booking / orders / migrations.

Create/update:

`docs/HANDOFF_B12B_ADMIN_TEMPLATE_PREVIEW_SELECT_TO_NEXT_STEP.md`

Include:
- checkpoint;
- files changed summary;
- API behavior;
- review-package field shape;
- Telegram behavior;
- tests run;
- non-goals preserved;
- next likely steps:
  1. B12C — Telegram admin template selection UI if needed;
  2. B13 — channel adapter design;
  3. production content QA.

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