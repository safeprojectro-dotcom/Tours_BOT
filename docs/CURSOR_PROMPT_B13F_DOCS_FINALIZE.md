# CURSOR_PROMPT_B13F_DOCS_FINALIZE

Finalize B13F documentation only.

B13F is already implemented:

- `AdminSupplierOfferShowcasePublishAttemptRead`
- `AdminSupplierOfferShowcasePublishAttemptsReviewRead`
- `AdminSupplierOfferReviewPackageRead.showcase_publish_attempts_review`
- `SupplierOfferShowcasePublishAttemptService.list_attempts_review_read(...)`
- review-package now includes compact publish attempt history
- Telegram admin card appends compact publish audit block
- no dedicated endpoint was added; this is acceptable for B13F MVP because review-package is the main admin read model
- no migrations
- no retry/resend
- no publish behavior changes
- no publish readiness changes
- no new channels
- no Mini App
- no booking/payment/orders

Tests already run:
- `python -m unittest tests.unit.test_supplier_offer_showcase_publish_attempt tests.unit.test_supplier_offer_review_package -v`
- `python -m unittest tests.unit.test_supplier_offer_ai_public_copy_fact_lock tests.unit.test_supplier_offer_catalog_conversion_closure -v`

## Required docs updates

Update:

`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`

Add B13F implementation note:
- read-only attempt history is now exposed through review-package;
- Telegram admin detail shows compact audit block;
- dedicated endpoint was deferred;
- no retry/resend.

Update:

`docs/B13_CHANNEL_ADAPTER_DESIGN.md`

Add B13F pointer:
- publish attempt history read surface exists;
- still no retries/resend/new channels.

Update:

`docs/CHAT_HANDOFF.md`

Add B13F completed entry:
- `showcase_publish_attempts_review` added to review-package;
- Telegram admin publish audit summary added;
- no dedicated endpoint in MVP;
- tests passed;
- no migrations;
- no retry/resend;
- no publish/readiness changes;
- no Mini App / booking / payment / orders.

Create/update:

`docs/HANDOFF_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE_TO_NEXT_STEP.md`

Include:
- checkpoint;
- files changed summary;
- read model names;
- review-package field name;
- Telegram summary behavior;
- tests run;
- non-goals preserved;
- next likely steps:
  1. Production publish smoke with audit verification;
  2. B13G manual retry/resend design, docs-only first;
  3. optional dedicated admin endpoint if operators need it.

Update:

`docs/CURSOR_PROMPT_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE.md`

If the prompt file is truncated, close it and add completion note:
- implemented;
- no endpoint in MVP;
- tests;
- safety confirmations.

Update `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` only if a real new open item appears. If not, leave unchanged and say so.

## Forbidden

Do not change app code.
Do not change tests.
Do not add migrations.
Do not add endpoint in this finalize pass.
Do not change publish behavior.
Do not change publish readiness.
Do not add retry/resend.
Do not add new channels.
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
   - no endpoint added;
   - no publish behavior changes;
   - no publish readiness changes;
   - no retry/resend;
   - no new channels;
   - no Mini App;
   - no booking/payment/orders.