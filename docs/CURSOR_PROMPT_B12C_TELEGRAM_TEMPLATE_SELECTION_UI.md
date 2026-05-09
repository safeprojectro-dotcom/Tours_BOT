# CURSOR_PROMPT_B12C_TELEGRAM_TEMPLATE_SELECTION_UI

You are working on Tours_BOT.

Implement B12C: Telegram admin template selection UI for Supplier Offer showcase marketing templates.

This block builds on B12B.

## Current checkpoint

B12A closed:
- marketing template library foundation;
- metadata stored in `packaging_draft_json`;
- publish output unchanged.

B12B closed/expected closed:
- review-package exposes `showcase_template_preview`;
- Admin PATCH endpoint:
  - `PATCH /admin/supplier-offers/{id}/packaging/showcase-template`
  - writes selected template into JSON metadata;
  - supports `template_id: null` to clear selection;
  - validates blocked templates;
  - `LAST_SEATS_URGENT` requires verified `live_seats_remaining >= 1`;
  - blocked after `approved_for_publish`;
- Telegram detail shows read-only template summary;
- channel publish output unchanged.

## Goal

Add Telegram admin UI for template preview/selection.

Admin should be able to:

1. open template selection from the offer detail card;
2. see available/blocked templates;
3. select a safe enabled template;
4. clear selection;
5. return to refreshed offer detail.

## Scope

Allowed:
- Telegram admin callback/button flow;
- service call equivalent to B12B Admin PATCH selection;
- translations EN/RO;
- tests;
- docs.

Not allowed:
- changing B12B validation rules;
- changing publish output;
- changing publish readiness;
- auto-publishing;
- approving packaging automatically;
- changing lifecycle;
- Mini App;
- booking/payment/orders;
- migrations.

## Source of truth

Telegram UI must not implement template selection rules itself.

It must rely on:

- `showcase_template_preview.template_choices`;
- B12B service/API-equivalent validation path.

If a template choice is disabled/blocked in preview:
- do not show it as selectable, or show as disabled/read-only if Telegram UI convention supports that;
- confirm handler must still re-read review-package and revalidate before mutating JSON.

## Required UX

### Button on offer detail

Add a button:

EN:
- `Template`

RO:
- `Șablon`

Placement:
- near packaging/showcase actions;
- not near dangerous public publish if possible.

### Template list screen/message

When tapped:

- re-read review-package;
- display:
  - inferred template;
  - selected/effective template;
  - enabled template choices;
  - blocked templates with reason summary if concise;
  - note: selection changes packaging metadata only and does not publish.

Example EN:

```text
Showcase template

Current: Per-seat standard
Selected: none

Choose a template for admin packaging metadata.
This does not publish or approve the offer.