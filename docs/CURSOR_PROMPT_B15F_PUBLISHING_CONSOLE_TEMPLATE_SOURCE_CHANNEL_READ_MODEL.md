# CURSOR_PROMPT_B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL

## Context

Project: Tours_BOT.

We are continuing after B15E.

Recent clean checkpoint:
- `1aeeb10 feat: add publishing console action affordances`
- `fab43a6 feat: enrich admin publishing console read view`
- `d4489e1 docs: close B15C exact CTA chain checkpoint`
- `f444a15 fix: align supplier offer publish copy with execution link order`

Completed B15 chain so far:

## B15C closed exact CTA chain

Supplier offer approved/packaged
→ Tour bridge created/linked
→ Tour activated for Mini App catalog
→ Active execution link created
→ Showcase/channel publish allowed
→ Channel `Rezervă` opens exact Mini App tour via Telegram Mini App short-name link
→ Layer A handles reservation/payment.

## B15D done

`GET /admin/publishing-console` now exposes rich read fields:
- readiness_summary
- readiness_level
- conversion_target_kind
- conversion_target_url
- cta_safety_status
- primary_blocker
- blocker_codes
- next_action_code
- next_action_label
- admin_action_path
- preview_path
- source_status_summary
- audit_hint

## B15E done

`GET /admin/publishing-console` now exposes read-only action affordances:
- actions[]
- code
- label
- kind
- enabled
- requires_confirmation
- danger_level
- admin_path
- method
- implemented
- disabled_reason
- source

Important preserved boundaries:
- publishing console remains read-only;
- no publish/send/retry/scheduler;
- no mutation services from console read endpoint;
- no Layer A changes;
- no Mini App routing changes;
- no B15C gate changes.

## Goal

Implement B15F as a safe read-model expansion for template/source/channel visibility in the Admin Publishing Console.

The console should help an admin understand:

1. What source object the candidate comes from.
2. What content/template source is used.
3. Whether there is a preview/draft payload.
4. What publication channel/target is intended.
5. Whether the candidate has publish-safe media status.
6. Which future template/channel actions are not yet implemented.
7. What constraints remain before a real template editor/channel selector can be built.

This is still read-only.

## Required behavior

Extend the read-only publishing console item with additive metadata fields.

Suggested fields:

```json
{
  "source_kind": "supplier_offer",
  "source_id": 15,
  "source_title": "Test Direct Mini app link",
  "template_kind": "supplier_offer_showcase",
  "template_version": "deterministic_v1",
  "template_source_status": "available",
  "template_source_summary": "Packaging draft available from supplier offer.",
  "template_preview_available": true,
  "template_preview_path": "/admin/supplier-offers/15/review-package",
  "channel_kind": "telegram_showcase_channel",
  "channel_status": "configured",
  "channel_ref": "-1003955096010",
  "channel_summary": "Telegram showcase channel configured.",
  "media_policy_status": "publish_safe_metadata_only",
  "media_summary": "Cover uses telegram_photo reference and is approved for card.",
  "template_actions": [
    {
      "code": "edit_showcase_template",
      "label": "Edit template",
      "implemented": false,
      "enabled": false,
      "disabled_reason": "Template editor is not implemented in B15F."
    }
  ],
  "channel_actions": [
    {
      "code": "select_channel",
      "label": "Select channel",
      "implemented": false,
      "enabled": false,
      "disabled_reason": "Channel selector is not implemented in B15F."
    }
  ]
}