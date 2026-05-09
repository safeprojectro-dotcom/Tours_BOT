# HANDOFF_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B_IMPLEMENT_WITH_SUPPLEMENT

Project: Tours_BOT

## Purpose

Single handoff entry for **C2B8B** when the implementer uses **main prompt + legacy supplement** together.

## Task sources

1. `docs/CURSOR_PROMPT_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B.md`
2. `docs/CURSOR_PROMPT_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B_SUPPLEMENT_LEGACY_PUBLISH.md` (mandatory: legacy one-step publish on the card)

Combined agent entry: `docs/CURSOR_PROMPT_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B_IMPLEMENT_WITH_SUPPLEMENT.md`

## Required final behavior

Telegram admin **offer detail** gets **Publică / Publish** for showcase channel publication **only** when:

```text
operator_workflow.actions[].code == "publish_showcase_channel"
enabled == true
```

- **No** extra readiness logic in the bot beyond that gate (C2B8A remains authoritative in `operator_workflow`).
- **Propose → confirm → cancel**; **re-read `GET …/review-package`** before confirm UI and again immediately before calling **`SupplierOfferModerationService.publish`** (parity with HTTP + **`notify_published`**).
- **Legacy** **`ADMIN_OFFERS_ACTION_PUBLISH`** **must not** appear on the detail keyboard; stale callbacks should **not** publish (retired message).

## Implementation status

**Shipped** in codebase — see closure notes: `docs/HANDOFF_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B_TO_NEXT_STEP.md`, `docs/CHAT_HANDOFF.md` (slice C2B8B).

## Related

- Readiness gate: `docs/HANDOFF_ADMIN_SHOWCASE_PUBLISH_READINESS_GATE_C2B8A_TO_NEXT_STEP.md`
- Legacy supplement narrative: `docs/HANDOFF_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B_SUPPLEMENT_LEGACY_PUBLISH.md`
