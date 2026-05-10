# CURSOR_PROMPT_B13D_ALT_DOCS_FINALIZE

Finalize B13D-alt documentation only.

B13D-alt is already implemented:

- `telegram_showcase_channel_publish_request_preview(...)` in `app/services/showcase_channel_adapter.py`
  - builds the same logical `ShowcaseChannelPublishRequest` as publish;
  - uses configured channel_ref;
  - `idempotency_key=None`;
  - no I/O.
- New schemas:
  - `AdminShowcasePublicationPayloadRead`
  - `AdminSupplierOfferShowcaseChannelPayloadRead`
- `SupplierOfferModerationService.showcase_channel_payload_preview(...)`
  - uses `build_showcase_publication`;
  - returns read model;
  - does not call Telegram.
- New read-only endpoint:
  - `GET /admin/supplier-offers/{offer_id}/showcase-channel-payload`
  - same admin auth;
  - 404 if offer missing.
- Tests:
  - `tests/unit/test_showcase_channel_adapter.py`
  - `tests/unit/test_supplier_offer_track3_moderation.py`
  - result: 23 passed.
- Publish path unchanged.
- Telegram send unchanged.
- No migrations.
- No attempt table.
- No retries.
- No new channels.
- No Mini App / booking / payment / orders.

## Required docs updates

Update:

`docs/B13_CHANNEL_ADAPTER_DESIGN.md`

Add B13D-alt implementation note:
- read-only channel payload preview endpoint added;
- payload is derived from current `build_showcase_publication`;
- no Telegram send;
- no publish behavior change;
- no attempt table/idempotency enforcement yet.

Update:

`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`

Add pointer:
- B13D-alt provides preview/read model before audit table implementation;
- can support future content fingerprint/audit design;
- no migration/attempt table yet.

Update:

`docs/CHAT_HANDOFF.md`

Add B13D-alt completed entry:
- read-only channel payload preview endpoint implemented;
- field/endpoint name;
- tests passed;
- no publish/send;
- no behavior/readiness changes;
- no migrations;
- no Mini App / booking / orders.
- next options:
  1. B13D real publish attempt table, if migration approved;
  2. Production publish/content QA smoke;
  3. B13E audit wiring later.

Create/update:

`docs/HANDOFF_B13D_ALT_CHANNEL_PREVIEW_PAYLOAD_READ_MODEL_TO_NEXT_STEP.md`

Include:
- checkpoint;
- files changed summary;
- endpoint/read model;
- no-send guarantee;
- tests run;
- non-goals preserved;
- next options.

Update:

`docs/CURSOR_PROMPT_B13D_ALT_CHANNEL_PREVIEW_PAYLOAD_READ_MODEL.md`

Add completion note:
- implemented;
- tests;
- safety confirmations.

Update `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` only if a real new open issue appears. Otherwise leave unchanged and say so.

## Forbidden

Do not change app code.
Do not change tests.
Do not add migrations.
Do not change publish behavior.
Do not change publish readiness.
Do not add attempt table.
Do not add retries.
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
   - no publish behavior changes;
   - no publish readiness changes;
   - no attempt table;
   - no retries;
   - no new channels;
   - no Mini App;
   - no booking/payment/orders.