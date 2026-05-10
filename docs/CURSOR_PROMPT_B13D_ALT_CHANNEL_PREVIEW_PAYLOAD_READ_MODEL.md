# CURSOR_PROMPT_B13D_ALT_CHANNEL_PREVIEW_PAYLOAD_READ_MODEL

You are working on Tours_BOT.

Implement B13D-alt: Showcase channel preview payload read model.

This is a read-only implementation slice.

It must not publish anything.

It must not add migrations.

It must not change current Telegram publish behavior.

## Current checkpoint

B13A closed:
- channel adapter design created.

B13B closed:
- `ShowcaseChannelAdapter` interface added.
- `TelegramShowcaseChannelAdapter` wraps existing `send_showcase_publication`.
- `SupplierOfferModerationService.publish` uses adapter wrapper.
- Behavior-preserving refactor.

B13C closed:
- publish attempt/audit design created.
- No attempt table implemented yet.
- No retry/idempotency implementation yet.

B12A/B/C closed:
- showcase marketing template library;
- admin preview/select;
- Telegram template selection UI;
- publish output unchanged.

Media pipeline remains paused at B7.4D.

## Goal

Add a read-only preview payload model for future channel adapters.

Operators/admin API should be able to inspect the payload that would be sent to the current Telegram showcase channel without actually sending it.

This creates a bridge between:

```text
build_showcase_publication
→ channel adapter request shape
→ future audit/idempotency layer
```

## Completion (B13D-alt — 2026-05-09)

**Implemented:** read-only **`GET /admin/supplier-offers/{offer_id}/showcase-channel-payload`**; Pydantic read models **`AdminShowcasePublicationPayloadRead`**, **`AdminSupplierOfferShowcaseChannelPayloadRead`**; **`SupplierOfferModerationService.showcase_channel_payload_preview`**; **`telegram_showcase_channel_publish_request_preview`** in **`app/services/showcase_channel_adapter.py`**.

**Tests:** **`tests/unit/test_showcase_channel_adapter.py`**, **`tests/unit/test_supplier_offer_track3_moderation.py`** — **23** passed (preview shape + HTTP 200/404; Telegram API not called from this path).

**Safety confirmations:** **no** Telegram send from preview; **no** change to **`POST …/publish`**, **`send_showcase_publication`**, or publish-readiness gates; **no** migrations; **no** publish-attempt table or idempotency enforcement; **`idempotency_key`** **`null`** on preview payload; non-goals (retries, extra channels, Mini App, booking/payment/orders) preserved per slice scope.

**Docs:** design/traceability in **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)** §9b, **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)** (B13D-alt bridge pointer), **[`docs/HANDOFF_B13D_ALT_CHANNEL_PREVIEW_PAYLOAD_READ_MODEL_TO_NEXT_STEP.md`](HANDOFF_B13D_ALT_CHANNEL_PREVIEW_PAYLOAD_READ_MODEL_TO_NEXT_STEP.md)**.