# CURSOR_PROMPT_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER

You are working on Tours_BOT.

Implement B13B: Showcase channel adapter interface + Telegram wrapper.

This is a behavior-preserving refactor.

## Current checkpoint

B13A is closed / expected closed:

- `docs/B13_CHANNEL_ADAPTER_DESIGN.md` created.
- Design separates:
  - review-package/operator workflow gates;
  - content assembly;
  - idempotency/audit/outbox future layer;
  - channel adapters / transport I/O.
- Existing Telegram publish behavior is documented as the baseline.
- Recommended next implementation: adapter interface + Telegram wrapper with no behavior change.

B12A/B/C are closed:

- template library foundation;
- admin preview/select;
- Telegram template selection UI;
- publish output unchanged.

Media pipeline remains paused at B7.4D.

## Goal

Introduce a small showcase channel adapter abstraction and wrap the existing Telegram send path without changing behavior.

This is the first implementation slice for B13.

## Non-negotiable behavior rule

The output and side effects of current Telegram showcase publish must remain the same.

Do not change:

- publish readiness;
- review-package/operator workflow gates;
- admin confirmation flow;
- `SupplierOfferModerationService.publish` external behavior;
- `build_showcase_publication` output;
- Telegram message text/photo behavior;
- stored `showcase_chat_id`;
- stored `showcase_message_id`;
- lifecycle transition to published;
- template metadata behavior;
- media review behavior.

## Code to inspect first

Inspect:

- `docs/B13_CHANNEL_ADAPTER_DESIGN.md`
- `app/services/telegram_showcase_client.py`
- `app/services/supplier_offer_moderation_service.py`
- `app/services/supplier_offer_showcase_message.py`
- `app/api/routes/admin.py`
- Telegram admin publish callback in:
  - `app/bot/handlers/admin_moderation.py`
- tests around:
  - publish moderation;
  - Telegram admin moderation;
  - showcase RO;
  - review-package/operator workflow.

## Required implementation

### 1. Adapter DTO / interface

Add a small module, for example:

`app/services/showcase_channel_adapter.py`

or if project style prefers:

`app/services/showcase_channels.py`

Define lightweight DTOs / protocol:

```python
@dataclass(frozen=True)
class ShowcaseChannelPublishRequest:
    offer_id: int
    publication: ShowcasePublication
    channel_ref: str | None = None
    idempotency_key: str | None = None

@dataclass(frozen=True)
class ShowcaseChannelPublishResult:
    provider: str
    chat_id: str | None
    message_id: str | None
    raw_reference: str | None = None

class ShowcaseChannelAdapter(Protocol):
    async def publish(self, request: ShowcaseChannelPublishRequest) -> ShowcaseChannelPublishResult:
        ...
```

---

## Completion (B13B)

- **Implemented:** **`app/services/showcase_channel_adapter.py`**; **`SupplierOfferModerationService.publish`** uses **`TelegramShowcaseChannelAdapter`** → **`send_showcase_publication`** (same args as pre-refactor). **`ShowcaseChannelAdapter`** is **synchronous** `publish()` to match the existing moderation stack (prompt sketch showed `async`; code uses sync).
- **Tests:** **`test_showcase_channel_adapter`**; publish mocks patch **`app.services.telegram_showcase_client.send_showcase_publication`**; **`test_supplier_offer_track3_moderation`**, **`test_supplier_offer_review_package`**, **`test_supplier_offer_catalog_conversion_closure`**, **`test_telegram_admin_moderation_y281`** — **89** passed (representative full matrix).
- **Unchanged:** publish readiness/output, admin confirmation, lifecycle/persistence, **no** outbox/attempt table/migrations/new channels/Mini App/booking/payment/orders.
- **Docs finalize:** **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)** §9; **[`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md)**; **[`docs/HANDOFF_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER_TO_NEXT_STEP.md`](HANDOFF_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER_TO_NEXT_STEP.md)**.