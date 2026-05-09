# CURSOR_PROMPT_B7_4A_SAVE_AUDIT_DOC

You already completed the B7.4A media storage pipeline readiness audit in chat.

Now save it into repository docs.

This is docs-only.

## Required files

Create:

`docs/B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md`

Content must include:

1. Scope and non-goals
2. Document inventory inspected
3. Current media data model
4. Current media workflow end-to-end
5. Gaps vs durable publish-safe storage
6. Proposed storage design direction
7. Safest next implementation sequence:
   - B7.4B — media storage ingestion contract/design doc
   - B7.4C — minimal config + adapter/service + tests, no auto-publish
   - B7.4D — persist durable media metadata in publish_safe
   - B7.4E — review-package/readiness integration if policy requires durable asset
   - B7.5 — rendered branded card asset
   - B7.6 — Telegram sendPhoto/sendMediaGroup publish
8. Test inventory to reference
9. Explicit confirmations:
   - no code changes
   - no migrations
   - no Mini App
   - no booking/payment/orders
   - no publish readiness behavior changes
   - no real Telegram file download
   - no production storage access

Update:

`docs/CHAT_HANDOFF.md`

Add a short B7.4A line:

- B7.4A media storage readiness audit completed.
- Current media pipeline is metadata-only.
- `publish_safe` is deferred with no durable object key/public URL.
- Next recommended step is B7.4B media storage ingestion contract/design.
- No code/migrations/production storage access.

Update or close:

`docs/CURSOR_PROMPT_MEDIA_STORAGE_PIPELINE_READINESS_B7_4A.md`

Add a short completion note if needed.

Create/update:

`docs/HANDOFF_MEDIA_STORAGE_PIPELINE_READINESS_B7_4A_TO_NEXT_STEP.md`

Include:
- current checkpoint;
- audit summary;
- next recommended step B7.4B;
- non-goals preserved;
- no code/migrations/Mini App/booking/payment/orders.

## Forbidden

Do not change app code.
Do not change tests.
Do not add migrations.
Do not touch Mini App.
Do not touch booking/payment/orders.
Do not change publish readiness behavior.
Do not download Telegram files.
Do not access storage.

## After completion report

Return:

1. docs changed/created;
2. short summary of saved audit;
3. `git status --short`;
4. `git diff --stat`;
5. explicit confirmation:
   - docs-only;
   - no code;
   - no migrations;
   - no Mini App;
   - no booking/payment/orders;
   - no publish readiness behavior changes;
   - no real Telegram file download;
   - no production storage access.