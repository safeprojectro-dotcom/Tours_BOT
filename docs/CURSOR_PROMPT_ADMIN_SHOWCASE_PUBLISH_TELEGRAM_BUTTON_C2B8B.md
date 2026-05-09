# CURSOR_PROMPT_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B

You continue Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

---

## Functional block

ADMIN SHOWCASE PUBLISH — C2B8B

Implement Telegram admin `Publică` / `Publish` button using existing `publish_showcase_channel` operator_workflow action.

---

## Current completed context

C2B8A is implemented and production-smoked.

`publish_showcase_channel` already exists in operator_workflow/read-package:

- danger_level = public_dangerous
- requires_confirmation = true
- method = POST
- endpoint = /admin/supplier-offers/{offer_id}/publish
- enabled only when publish readiness gate passes

C2B8A blocks publish when hard cover/media blockers exist, including:

- replacement_requested aligned with current cover
- rejected/fallback aligned with current cover
- approved_for_card snapshot mismatch
- cover photo exists but is not explicitly approved/aligned
- not sendable cover
- packaging not approved
- lifecycle/config blockers

Production smoke for Offer #8 confirmed:

```text
publish_showcase_channel.enabled = False
Cover/media gate: [media_review_replacement_requested]