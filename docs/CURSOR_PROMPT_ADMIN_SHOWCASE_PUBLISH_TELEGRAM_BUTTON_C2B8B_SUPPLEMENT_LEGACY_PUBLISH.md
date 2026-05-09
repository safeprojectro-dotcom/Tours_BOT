# CURSOR_PROMPT_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B_SUPPLEMENT_LEGACY_PUBLISH

This is a supplement to the already running C2B8B task.

Continue the implementation from the previous prompt, but add the following mandatory clarification about the existing legacy Telegram Publish action.

## Problem to resolve

There is already a one-step legacy `Publish` action in `_action_button_rows` for `ADMIN_OFFERS_ACTION_PUBLISH`.

C2B8B adds a new workflow-gated Telegram admin publish path based on:

```text
operator_workflow.actions[].code == "publish_showcase_channel"
enabled == true
```

Both paths ultimately call the same service used by HTTP `POST /admin/supplier-offers/{offer_id}/publish` — `SupplierOfferModerationService.publish(...)`.

If both stay visible, Telegram operators get **duplicate** “Publish”/“Publică” affordances, and the legacy path **bypasses** the C2B8B contract: it does **not** require the two-step **propose → confirm** flow and does **not** re-read `review-package` before executing. That recreates a **Telegram-side bypass** of the C2B8A read-model gate (operators could publish from the card when `publish_showcase_channel.enabled == false`, as long as lifecycle is `APPROVED`).

## Mandatory product/engineering rule (Telegram only)

1. **Single publish entry on the supplier-offer admin card:** After C2B8B, showcase publish from Telegram must go **only** through the workflow action (`publish_showcase_channel`) with mandatory confirmation and **re-read** on confirm, as in the main C2B8B prompt.

2. **Remove the legacy one-step publish button** from the offer-detail keyboard path:
   - Stop appending the `ADMIN_OFFERS_ACTION_PUBLISH` row from `_action_button_rows` for `SupplierOfferLifecycle.APPROVED` when building `_detail_keyboard` (or remove that branch entirely for this surface — choose the smallest change that guarantees the legacy button no longer appears on the card).
   - Do **not** register a second public-dangerous shortcut that calls `moderation.publish` without the workflow checks.

3. **Keep** other legacy lifecycle actions unchanged unless already in scope (e.g. Approve/Reject for `READY_FOR_MODERATION`, Retract/link actions for `PUBLISHED` — do not broaden this supplement).

4. **Do not** change HTTP or in-process semantics of `SupplierOfferModerationService.publish` — automation and Admin API may still call publish when appropriate; this supplement only removes the **unsafe duplicate Telegram** entry.

5. **Tests:** Update or add keyboard/handler tests so that for an `APPROVED` offer, the keyboard **does not** expose the legacy `ADMIN_OFFERS_ACTION_PUBLISH` callback, while the C2B8B workflow button appears **only** when `publish_showcase_channel.enabled`.

6. **Docs:** Note in `docs/HANDOFF_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B_TO_NEXT_STEP.md` (or `docs/CHAT_HANDOFF.md` if that is your continuity file) that the legacy Telegram publish row was retired for `APPROVED` in favor of the workflow-gated path.

## Non-goals

- Do not add new business rules for when publish is allowed (C2B8A + `operator_workflow` remain the authority).
- Do not change retract/publish service behavior beyond removing the duplicate Telegram entry point above.
