# CURSOR_PROMPT_B15E_ADMIN_PUBLISHING_CONSOLE_ACTION_AFFORDANCES_DESIGN

## Context

Project: Tours_BOT.

We are continuing after B15D.

Recent clean checkpoint:
- `fab43a6 feat: enrich admin publishing console read view`
- `d4489e1 docs: close B15C exact CTA chain checkpoint`
- `f444a15 fix: align supplier offer publish copy with execution link order`
- `c3dda1c fix: keep admin on supplier offer after bridge actions`

B15C exact CTA chain is closed:
Supplier offer approved/packaged
→ Tour bridge created/linked
→ Tour activated for Mini App catalog
→ Active execution link created
→ Showcase/channel publish allowed
→ Channel `Rezervă` opens exact Mini App tour via Telegram Mini App short-name link
→ Layer A handles reservation/payment.

B15D enriched `GET /admin/publishing-console` with read-only guidance fields:
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

B15D preserved:
- read-only endpoint
- no publish/send/retry/scheduler
- no Layer A changes
- no Mini App routing changes
- no B15C gate changes

## Goal

Implement B15E as a design/read-first action affordances layer for the Admin Publishing Console.

This step should define and expose safe action affordance metadata for console items without performing mutations.

The console should help an admin understand:
- what action can be taken next;
- whether the action is read-only, safe mutation, conversion-enabling, or public-dangerous;
- whether confirmation is required;
- what endpoint/path or admin surface should be used;
- why an action is disabled;
- whether the action is existing, future, or not implemented.

## Important boundary

B15E must NOT implement new mutation behavior.

It may expose action affordances in the read-only console response, but it must not:
- publish;
- send Telegram messages;
- create bridges;
- activate tours;
- create execution links;
- schedule posts;
- auto-draft;
- mutate production data.

## Required behavior

Extend the read-only publishing console item with additive action affordance fields.

Suggested structure:

```json
{
  "actions": [
    {
      "code": "get_showcase_preview",
      "label": "Preview",
      "kind": "safe_read",
      "enabled": true,
      "requires_confirmation": false,
      "danger_level": "safe_read",
      "admin_path": "/admin/supplier-offers/{offer_id}/review-package",
      "method": "GET",
      "implemented": true,
      "disabled_reason": null,
      "source": "operator_workflow"
    }
  ]
}