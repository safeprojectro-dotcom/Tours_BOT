# CURSOR_PROMPT_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON

You are working on Tours_BOT.

Implement B13D: Showcase publish attempt table + repository/service skeleton.

This is an audit foundation step.

It may add a DB migration, but must not change live publish behavior.

## Current checkpoint

B13A:
- channel adapter design completed.

B13B:
- `ShowcaseChannelAdapter` interface added.
- `TelegramShowcaseChannelAdapter` wraps existing `send_showcase_publication`.
- `SupplierOfferModerationService.publish` uses the adapter wrapper.
- Behavior-preserving.

B13C:
- publish attempt/audit design completed.
- No code/migrations in B13C.

B13D-alt:
- read-only showcase channel payload preview endpoint implemented:
  - `GET /admin/supplier-offers/{offer_id}/showcase-channel-payload`
- No send/publish.
- No attempt table.
- No retries.

## Goal

Add the first persistent audit foundation for showcase publish attempts.

This step must create:

1. DB model/table for publish attempts.
2. Alembic migration.
3. Repository methods.
4. Service skeleton to create/update attempt records.
5. Unit tests.

But this step must NOT wire the attempt table into live publish yet.

## Critical rule

Do not change current publish behavior.

Do not modify `SupplierOfferModerationService.publish` to create attempt rows in this step unless explicitly needed for tests. Prefer no live-path integration.

B13D should be a foundation only.

## Proposed table

Use project naming conventions.

Suggested table name:

```text
supplier_offer_showcase_publish_attempts
```

## Completion (B13D — finalized for commit)

**Implemented:** table **`supplier_offer_showcase_publish_attempts`**; migration **`20260531_29`** (`alembic/versions/20260531_29_supplier_offer_showcase_publish_attempts.py`); model **`SupplierOfferShowcasePublishAttempt`**; enums **`SupplierOfferShowcasePublishAttemptStatus`**, **`SupplierOfferShowcasePublishActorSurface`**; repository **`SupplierOfferShowcasePublishAttemptRepository`**; service **`SupplierOfferShowcasePublishAttemptService`**.

**Retention:** FK **`ON DELETE RESTRICT`** (audit rows are not silently removed when a **`supplier_offer`** is deleted); **`SupplierOffer.showcase_publish_attempts`** uses **`passive_deletes=True`** only (**no** ORM **`delete-orphan`**).

**Tests:** **`tests/unit/test_supplier_offer_showcase_publish_attempt.py`**.

**Safety:** **no** live **`publish`** wiring; **no** Telegram/send changes; **no** publish readiness changes; **no** retries, **no** Mini App, **no** booking/payment/orders.

**Handoff:** [`docs/HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP.md`](HANDOFF_B13D_PUBLISH_ATTEMPT_TABLE_SKELETON_TO_NEXT_STEP.md).
