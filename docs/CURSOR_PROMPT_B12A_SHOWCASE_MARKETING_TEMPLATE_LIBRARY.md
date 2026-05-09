# CURSOR_PROMPT_B12A_SHOWCASE_MARKETING_TEMPLATE_LIBRARY

You are working on Tours_BOT.

Implement B12A: Showcase Marketing Copy Template Library foundation.

This is a larger functional block, but still must preserve safety.

## Current checkpoint

Closed and pushed:

- Telegram admin conversion chain:
  - Link tour
  - List for sale
  - Publish
  - Booking link

- C2B11A Admin/OPS conversion status panel:
  - `conversion_status_panel` in review-package
  - Telegram admin detail panel
  - read-only

- B10.6A Bot-as-router:
  - `/start supoffer_<id>` customer copy driven by resolver `copy_bucket`
  - no B11 semantic changes

- Media pipeline:
  - paused intentionally at B7.4D
  - no durable rendering/publishing yet

## Goal

Create a safe marketing template library foundation for Supplier Offer showcase copy.

The goal is to standardize public-facing copy for Telegram showcase posts without weakening fact locks or inventing availability/discount claims.

## Business principles

Preserve:

- Supplier gives facts.
- AI/system can package copy.
- Admin approves.
- Channel showcases.
- Mini App converts.
- Layer A executes reservation/payment.

Important:

- Template structures copy.
- System must not lie.
- No fake urgency.
- No fake seat count.
- Discounts only from real fields.
- Availability only from live/verified data.
- Published offer != bookable Tour.

## Scope

Implement foundation for template selection and text generation, but do not change live publish behavior unless current code already has a deterministic draft builder and tests can safely align it.

Allowed:

- add template enum/constants;
- add template selection service/helper;
- add deterministic copy builder for supported templates;
- integrate into packaging draft generation only if existing architecture clearly has a safe extension point;
- add tests;
- update docs.

Not allowed:

- changing Telegram publish semantics;
- weakening review-package gates;
- auto-publishing;
- creating tours;
- changing booking/payment/orders;
- Mini App changes;
- migrations unless absolutely impossible to avoid — prefer no migration;
- AI calls / external calls;
- fake availability/urgency.

## Documents to inspect

Inspect:

- `docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`
- `docs/B10_6_BOT_AS_ROUTER_DESIGN_GATE.md`
- `docs/ADMIN_OPERATOR_WORKFLOW.md`
- `docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- any existing B12/B13 template docs/prompts/handoffs
- showcase/publish/copy related docs

## Code to inspect

Inspect current copy/showcase generation:

- supplier offer packaging / AI draft services
- showcase publication builder
- Telegram showcase client
- supplier offer public copy / fact lock services
- review-package service
- tests around:
  - supplier offer showcase RO
  - AI public copy fact lock
  - review package
  - publish/showcase generation

Likely files to inspect:

- `app/services/supplier_offer_showcase_*`
- `app/services/supplier_offer_ai_*`
- `app/services/supplier_offer_public_copy_*`
- `app/services/supplier_offer_review_package_service.py`
- `tests/unit/test_supplier_offer_showcase_ro.py`
- `tests/unit/test_supplier_offer_ai_public_copy_fact_lock.py`

Use actual repo names.

## Template library

Add or formalize these template types:

```text
PER_SEAT_STANDARD
FULL_BUS_PRIVATE_GROUP
CUSTOM_REQUEST_CTA
EARLY_BIRD_DISCOUNT
LAST_SEATS_URGENT
SUPPLIER_SERVICE_PROMO
SHORT_ANNOUNCEMENT
IMAGE_ONLY_TEASER
BRAND_AWARENESS_POST