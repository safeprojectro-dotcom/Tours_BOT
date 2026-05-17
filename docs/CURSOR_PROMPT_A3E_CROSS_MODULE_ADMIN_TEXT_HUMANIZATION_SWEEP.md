# CURSOR_PROMPT_A3E_CROSS_MODULE_ADMIN_TEXT_HUMANIZATION_SWEEP

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoint:

- 483c38b fix: clean up admin cockpit card readability
- 29e5c8 fix: humanize supplier clarification drafts
- b0143e7 feat: add supplier clarification draft split
- 79010f5 feat: add supplier intake auto validation
- ba6564b feat: standardize cockpit card detail UX

## Current state

A3D improved humanization in cockpit queue/detail rendering, but manual UAT still shows raw English/admin-internal text in some places, especially queue rows and tour cards.

Visible examples:

- Candidate for tour promotion / last-seats style posts (B15B does not send)
- Departure is in the past.
- Not ideal for catalog promotion until gates pass.

The user correctly noted that the same issue may exist in other admin Telegram modules, not only in Automation Cockpit.

## Current block

# A3E — Cross-Module Admin Text Humanization Sweep

## Goal

Find and fix admin-facing Telegram text leaks across related modules so non-technical admins see human-readable Romanian text instead of internal/debug/English strings.

This is not a new feature. This is a targeted production-readability sweep.

## Scope

Inspect and, only where needed, fix admin-facing text in:

- app/bot/automation_cockpit_telegram.py
- app/bot/messages.py
- app/bot/handlers/automation_cockpit_admin.py
- app/bot/handlers/admin_moderation.py
- app/bot/handlers/automation_cockpit_admin.py if present
- app/services/admin_automation_cockpit_service.py
- app/services/supplier_clarification_draft_service.py
- related tests under tests/unit/

Also search for hard-coded admin-facing English/debug strings in bot/admin modules.

Use targeted search for:

- `Candidate for tour promotion`
- `Departure is in the past`
- `Not ideal for catalog promotion`
- `B15B`
- `B7`
- `B10`
- `B11`
- `prepare_chain`
- `cta_safety`
- `publish_readiness`
- `media_review_replacement_requested`
- `content_quality`
- `description_thin`
- `orphan_promo_code`
- `execution link`
- `conversion not green`
- `catalog promotion`
- `last-seats`
- `does not send`
- snake_case debug values shown in bot/admin UI

## Safety boundaries

Do NOT:
- add migrations
- add write endpoints
- mutate supplier_offers
- mutate tours
- mutate orders/payments/reservations
- publish to Telegram
- send supplier notifications
- schedule messages
- call AI
- call external providers
- change B11 routing
- change Layer A logic
- execute prepare_conversion_chain
- create execution links

This is read-only rendering / i18n / admin text cleanup only.

---

# Required behavior

## 1. Global admin-facing humanization helper

If not already sufficient, create/extend one shared helper for admin-facing Telegram text.

It should be used anywhere admin UI may show blocker/warning/reason/task text.

Suggested behavior:

- known raw phrases → Romanian human-readable text
- known technical keys → Romanian human-readable text
- unknown technical-looking text → `Necesită verificare internă.`
- non-technical already human text may pass through

## 2. Queue rows must be clean

Queue list rows must not show:

```text
Candidate for tour promotion / last-seats style posts (B15B does not send)
Departure is in the past.
Not ideal for catalog promotion until gates pass.
B15B
B7
snake_case/debug terms