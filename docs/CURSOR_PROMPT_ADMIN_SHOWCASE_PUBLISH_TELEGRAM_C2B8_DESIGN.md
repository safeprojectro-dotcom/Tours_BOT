# CURSOR_PROMPT_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_C2B8_DESIGN

You continue Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Plan.

This is a design / safety gate step.

Do not change code.
Do not modify files unless explicitly asked after design approval.

---

## Functional block

ADMIN SHOWCASE PUBLISH — C2B8

Design Telegram admin `Publică` / `Publish` action for supplier offer showcase publication.

---

## Current completed context

The following blocks are implemented and closed:

### C2A / C2B preview + packaging workflow

- Review-package read path exists.
- Telegram admin moderation card exists.
- `Refresh` / `Preview` are read-only.
- `Pregătește` / generate packaging draft exists.
- `Aprobă text` / approve packaging for publish exists.
- Existing safe mutations use propose → confirm/cancel → re-read review-package before execution.

### C2B4

Telegram admin Preview sends the same photo/caption as the channel showcase would send, but privately to admin chat.

It does not publish.

### C2B5

Review-package/operator_workflow includes deterministic cover media warnings.

### C2B6

Telegram admin `Cere poză` / Request photo records replacement_requested metadata only.

It does not mutate cover_media_reference.
It does not publish.

### C2B7.1

Admin HTTP endpoint exists:

```text
PUT /admin/supplier-offers/{offer_id}/cover