# CURSOR_PROMPT_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B_IMPLEMENT_WITH_SUPPLEMENT

Continue C2B8B implementation.

Use these two docs as the active task source:

1. `docs/CURSOR_PROMPT_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B.md`
2. `docs/CURSOR_PROMPT_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B_SUPPLEMENT_LEGACY_PUBLISH.md`

The supplement is mandatory and overrides any ambiguity about the legacy Telegram publish button.

## Goal

Implement Telegram admin `Publică / Publish` button for showcase channel publication.

The button must be workflow-gated by:

```text
operator_workflow.actions[].code == "publish_showcase_channel"
enabled == true
```

Follow the two source docs for confirmation + re-read rules, execution path (`SupplierOfferModerationService.publish`, notification parity), tests, and retirement of the legacy one-step publish row/callback behavior.

If implementation is already merged, verify against `docs/HANDOFF_ADMIN_SHOWCASE_PUBLISH_TELEGRAM_BUTTON_C2B8B_TO_NEXT_STEP.md` instead of re-implementing.
