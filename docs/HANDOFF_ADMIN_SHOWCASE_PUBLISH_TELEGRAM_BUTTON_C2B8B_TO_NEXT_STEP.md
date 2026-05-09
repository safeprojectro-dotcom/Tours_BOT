# HANDOFF_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B_TO_NEXT_STEP

Project: Tours_BOT

## Status

**Implemented** (Telegram admin offer card).

## Shipped (C2B8B)

- **Publică / Publish** appears only when **`operator_workflow.actions`** contains **`publish_showcase_channel`** with **`enabled == true`**.
- **Propose → confirm** with **re-read `GET …/review-package`** before showing the confirm keyboard and again immediately before **`SupplierOfferModerationService.publish`**.
- **Notify parity:** **`SupplierOfferSupplierNotificationService.notify_published`** after successful publish (same as HTTP route).
- **Legacy one-step publish** (**`ADMIN_OFFERS_ACTION_PUBLISH`**) is **not** shown on the offer-detail keyboard; the legacy callback responds with **`admin_offer_legacy_publish_retired`** (avoids Telegram bypass of C2B8A read-model gate).

## Pointers

- Handler: `app/bot/handlers/admin_moderation.py` (`admin_ops_operator_workflow_c2b8b_publish_showcase`, `_operator_workflow_c2b8b_publish_propose_callback`, `_detail_keyboard`).
- Callback prefixes: `app/bot/constants.py` (`ADMIN_OPS_OW_PUBLISH_SHOWCASE_*`).
- Copy: `app/bot/messages.py`.
- Tests: `tests/unit/test_operator_workflow_c2b8b_specs.py`, `tests/unit/test_operator_workflow_c2b3_keyboard.py`, `tests/unit/test_telegram_admin_moderation_y281.py`.

## Next

Staging/production smoke: `docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`.
