
---

## HANDOFF name

`HANDOFF_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER_TO_NEXT_STEP.md`

---

## HANDOFF content

```md
# HANDOFF_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER_TO_NEXT_STEP

## Status

**B13B implemented.** Behavior-preserving refactor: **`ShowcaseChannelAdapter`** (sync **`Protocol`**) + **`TelegramShowcaseChannelAdapter`** wrap **`telegram_showcase_client.send_showcase_publication`**; **`SupplierOfferModerationService.publish`** delegates to the adapter then persists **`showcase_chat_id`**, **`showcase_message_id`**, lifecycle **`published`** unchanged. **`build_showcase_publication`** unchanged. No readiness, routing, B12 template publish, Mini App, booking, media pipeline, or migrations.

## Project

Tours_BOT — showcase channel adapter layer.

## Step

B13B — Channel adapter interface + Telegram wrapper.

## Checkpoint (before this step)

- **B13A:** **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)** — gates vs assembly vs optional outbox vs transport.

## Delivered (code)

| Area | Path |
|------|------|
| DTOs + Protocol + Telegram adapter | **`app/services/showcase_channel_adapter.py`** — **`ShowcaseChannelPublishRequest`**, **`ShowcaseChannelPublishResult`**, **`ShowcaseChannelAdapter`**, **`TelegramShowcaseChannelAdapter`**, **`default_telegram_showcase_adapter`**, **`TELEGRAM_SHOWCASE_PROVIDER`** |
| Publish orchestration | **`app/services/supplier_offer_moderation_service.py`** — **`publish`** uses adapter + **`int(result.message_id)`** for ORM |

## Design / test note

- **`send_showcase_publication`** is imported **inside** **`TelegramShowcaseChannelAdapter.publish`** so **`unittest.mock.patch("app.services.telegram_showcase_client.send_showcase_publication", ...)`** applies (avoids early-bound import alias).
- Tests that used **`app.services.supplier_offer_moderation_service.send_showcase_publication`** now patch **`app.services.telegram_showcase_client.send_showcase_publication`**.

## Non-goals (preserved)

No new channel, outbox, publish-attempt table, migrations, readiness changes, showcase HTML/photo semantics changes, B12 effective template in **`build_showcase_publication`**, Mini App, booking/payment/orders, or B7.4+ media continuation.

## Tests

- **`tests/unit/test_showcase_channel_adapter.py`** — adapter delegates with expected kwargs.
- **`tests/unit/test_supplier_offer_track3_moderation.py`**, **`tests/unit/test_supplier_offer_review_package.py`**, **`tests/unit/test_supplier_offer_catalog_conversion_closure.py`**, **`tests/unit/test_telegram_admin_moderation_y281.py`** — publish mocks updated; **89** passed for this matrix (finalize report).

Representative run:

```text
python -m pytest tests/unit/test_showcase_channel_adapter.py ^
  tests/unit/test_supplier_offer_track3_moderation.py ^
  tests/unit/test_supplier_offer_review_package.py ^
  tests/unit/test_supplier_offer_catalog_conversion_closure.py ^
  tests/unit/test_telegram_admin_moderation_y281.py -q
```

## Validation checklist

- [x] Same `send_showcase_publication` arguments as pre-B13B
- [x] Same DB fields and error mapping (`TelegramShowcaseSendError` → `SupplierOfferModerationStateError`)
- [x] `build_showcase_publication` untouched
- [x] No `operator_workflow` / review-package logic changes in this slice

## Next options

1. **B13C** — publish attempt / audit design.
2. **B13D** — channel preview payload read model.
3. **B13E** — manual copy adapters.

(Optional: **B12** effective template in **`build_showcase_publication`**; B7.x rendered assets by explicit decision.)

```

---

## Notes (wrapper)

Design baseline: **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)**. Implementation prompt: **[`docs/CURSOR_PROMPT_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER.md`](CURSOR_PROMPT_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER.md)**. Prior slice: **[`docs/HANDOFF_B13A_CHANNEL_ADAPTER_DESIGN_TO_NEXT_STEP.md`](HANDOFF_B13A_CHANNEL_ADAPTER_DESIGN_TO_NEXT_STEP.md)**.
