# CURSOR_PROMPT_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE

You are working on Tours_BOT.

Implement B13F: Admin read surface for showcase publish attempt history.

This is a read-only visibility block.

## Current checkpoint

B13D is closed:
- `supplier_offer_showcase_publish_attempts` table exists.
- FK retention uses `ON DELETE RESTRICT`.
- Repository/service skeleton exists.

B13E is closed / expected closed:
- publish path creates/updates publish attempt audit rows.
- Attempt lifecycle:
  - REQUESTED
  - PROVIDER_SENT
  - PERSISTED
  - FAILED
- HTTP publish records `requested_by="http_admin"`.
- Telegram publish records `requested_by="telegram:{admin_id}"`.
- No publish readiness changes.
- No Telegram output changes.
- No retry/resend.
- No idempotency enforcement.
- No new channels.
- No Mini App / booking/payment/orders.

## Goal

Expose publish attempt history to admin/OPS so operators can see:

- whether publish was attempted;
- whether it succeeded or failed;
- provider chat/message ids;
- actor/source;
- error if any;
- recent attempt timeline.

This must be read-only.

## Non-negotiable constraints

Do NOT:

- retry;
- resend;
- publish;
- create attempt rows manually;
- change publish readiness;
- change operator workflow gates;
- change Telegram output;
- change lifecycle behavior;
- touch Mini App;
- touch booking/payment/orders;
- add migrations.

## Code/docs to inspect

Inspect:

- `app/models/supplier_offer_showcase_publish_attempt.py`
- `app/repositories/supplier_offer_showcase_publish_attempt.py`
- `app/services/supplier_offer_showcase_publish_attempt_service.py`
- `app/services/supplier_offer_review_package_service.py`
- `app/schemas/supplier_admin.py`
- `app/api/routes/admin.py`
- `app/bot/handlers/admin_moderation.py`
- `app/bot/messages.py`
- `docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`
- `docs/B13_CHANNEL_ADAPTER_DESIGN.md`
- `docs/CHAT_HANDOFF.md`

## Required behavior

### 1. Admin schema/read DTO

Add read DTOs for publish attempt history.

Suggested names:

```python
AdminSupplierOfferShowcasePublishAttemptRead
AdminSupplierOfferShowcasePublishAttemptsReviewRead
```

With:

- **`AdminSupplierOfferReviewPackageRead.showcase_publish_attempts_review`**
- **`SupplierOfferShowcasePublishAttemptService.list_attempts_review_read(session, supplier_offer_id=..., limit=50)`**
- **`GET /admin/supplier-offers/{offer_id}/review-package`** includes the block (no dedicated list endpoint in MVP)
- Telegram: **`_showcase_publish_attempts_telegram_compact`** on admin offer detail (read-only, up to 5 rows)

### 2. Tests

- **`tests/unit/test_supplier_offer_showcase_publish_attempt.py`**
- **`tests/unit/test_supplier_offer_review_package.py`**
- Regression: **`tests/unit/test_supplier_offer_ai_public_copy_fact_lock`**, **`tests/unit/test_supplier_offer_catalog_conversion_closure`**

---

## Completion (B13F — implemented; docs finalized)

**Shipped:** Read DTOs and **`showcase_publish_attempts_review`** on review-package; **`list_attempts_review_read`**; Telegram compact audit block; **no** dedicated **`GET …/showcase-publish-attempts`** in MVP (acceptable — review-package is the main admin read model).

**Tests:** Commands above — passed.

**Safety:** No migrations; no retry/resend; no publish or publish-readiness changes; no operator-workflow gate changes; no Telegram channel output changes; no new channels; no Mini App / booking / payment / orders.

**Handoff / design:** [`docs/HANDOFF_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE_TO_NEXT_STEP.md`](HANDOFF_B13F_ADMIN_PUBLISH_ATTEMPT_HISTORY_READ_SURFACE_TO_NEXT_STEP.md) · [`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md) §12 · [`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md) §9e · [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) (B13F bullet).