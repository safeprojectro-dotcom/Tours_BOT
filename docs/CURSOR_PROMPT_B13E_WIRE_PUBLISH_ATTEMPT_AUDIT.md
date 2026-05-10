# CURSOR_PROMPT_B13E_WIRE_PUBLISH_ATTEMPT_AUDIT

You are working on Tours_BOT.

Implement B13E: wire showcase publish attempt audit into the existing publish path while preserving behavior.

This step uses the B13D audit foundation.

## Current checkpoint

B13D is closed and pushed:

- migration/table:
  - `supplier_offer_showcase_publish_attempts`
- FK retention:
  - `ON DELETE RESTRICT`
  - no ORM delete-orphan cascade
- model:
  - `SupplierOfferShowcasePublishAttempt`
- enums:
  - `SupplierOfferShowcasePublishAttemptStatus`
  - `SupplierOfferShowcasePublishActorSurface`
- repository:
  - `app/repositories/supplier_offer_showcase_publish_attempt.py`
- service skeleton:
  - `app/services/supplier_offer_showcase_publish_attempt_service.py`
- no live publish integration yet
- tests passed

B13B is closed:

- `TelegramShowcaseChannelAdapter` wraps existing `send_showcase_publication`
- `SupplierOfferModerationService.publish` uses adapter
- behavior-preserving

B13D-alt is closed:

- read-only channel payload preview endpoint exists
- no send/publish

## Goal

Create/update publish attempt audit rows during the existing showcase publish flow.

The publish behavior must remain the same from the user/operator perspective.

## Non-negotiable behavior rule

Do NOT change:

- publish readiness;
- operator workflow gates;
- admin confirmation flow;
- Telegram output;
- `build_showcase_publication` output;
- `sendPhoto` / `sendMessage` behavior;
- lifecycle transition semantics;
- Mini App;
- booking/payment/orders;
- media review;
- B12 template publish behavior.

Only add audit persistence around the existing publish side effect.

## Desired attempt lifecycle

Use existing B13D statuses.

Recommended mapping:

```text
requested -> provider_sent -> persisted
requested -> failed
```

## Completion (B13E — implemented; docs finalized)

**Shipped:** **`SupplierOfferModerationService.publish`** writes **`supplier_offer_showcase_publish_attempts`** (`requested` → `provider_sent` → `persisted`, or `failed`); payload **SHA-256** fingerprint; HTTP **`requested_by="http_admin"`**; Telegram **`TELEGRAM_BOT`** + **`telegram:{id}`**. **Adapter** unchanged. **No** readiness/gate/output/retry/idempotency/channel/Mini App/booking changes.

**Tests:** **`tests/unit/test_supplier_offer_track3_moderation.py`** (persisted + failed paths); **`tests/unit/test_supplier_offer_showcase_publish_attempt.py`**; **`tests/unit/test_showcase_channel_adapter.py`** — all OK (per project runs).

**Handoff:** [`docs/HANDOFF_B13E_WIRE_PUBLISH_ATTEMPT_AUDIT_TO_NEXT_STEP.md`](HANDOFF_B13E_WIRE_PUBLISH_ATTEMPT_AUDIT_TO_NEXT_STEP.md).

**Design refs (post-finalize):** [`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md) §11, [`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md) §9d, [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md) B13E bullet.
