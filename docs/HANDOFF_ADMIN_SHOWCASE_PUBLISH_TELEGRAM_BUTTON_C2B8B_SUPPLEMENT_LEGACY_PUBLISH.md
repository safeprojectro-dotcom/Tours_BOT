# HANDOFF_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B_SUPPLEMENT_LEGACY_PUBLISH

Project: Tours_BOT

## Functional block

Supplement to **C2B8B** — legacy Telegram **Publish** row vs workflow-gated **Publică / Publish**.

## Context

The main C2B8B task adds a Telegram admin showcase publish control that must follow **only** the operator_workflow action:

```text
operator_workflow.actions[].code == "publish_showcase_channel"
enabled == true
```

with **propose → confirm**, **re-read `GET …/review-package`** on both steps before execute, and **`SupplierOfferModerationService.publish(...)`** on successful confirm (parity with HTTP `POST …/publish`).

Full task prompt: `docs/CURSOR_PROMPT_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B.md`.  
Implementation supplement: `docs/CURSOR_PROMPT_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B_SUPPLEMENT_LEGACY_PUBLISH.md`.

## Problem

`_action_button_rows` already adds a **one-step** legacy **Publish** button for `SupplierOfferLifecycle.APPROVED` (`ADMIN_OFFERS_ACTION_PUBLISH`). It calls the same publish service **without** the C2B8B confirmation / re-read contract.

If both legacy and C2B8B buttons exist:

- duplicate **Publish** / **Publică** affordances;
- **Telegram bypass** of the C2B8A read-model gate: an operator could publish while `publish_showcase_channel.enabled == false` whenever lifecycle is **APPROVED**.

## Mandatory rule (Telegram card only)

1. **One** showcase publish entry on the supplier-offer admin card: workflow path only (see main C2B8B handoff).
2. **Remove** the legacy `ADMIN_OFFERS_ACTION_PUBLISH` row from the offer-detail keyboard (smallest change: omit that branch for `APPROVED` in `_action_button_rows` usage inside `_detail_keyboard`, or equivalent).
3. **Leave** other legacy actions as-is (Approve/Reject, Retract, link flows) unless already in C2B8B scope.
4. **Do not** change HTTP publish or `SupplierOfferModerationService.publish` semantics — only remove the unsafe duplicate **Telegram** shortcut.

## Tests

- `APPROVED` offer: keyboard must **not** expose legacy publish callback prefix for `ADMIN_OFFERS_ACTION_PUBLISH`.
- Workflow **Publică / Publish** appears **only** when `publish_showcase_channel.enabled` (existing C2B8B test plan).

## Continuity

After implementation, note retirement of the legacy Telegram publish row in `docs/HANDOFF_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B_TO_NEXT_STEP.md` and/or `docs/CHAT_HANDOFF.md` as appropriate.
