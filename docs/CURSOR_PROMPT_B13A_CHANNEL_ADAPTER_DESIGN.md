# CURSOR_PROMPT_B13A_CHANNEL_ADAPTER_DESIGN

You are working on Tours_BOT.

Run B13A: Channel Adapter Design for Supplier Offer showcase publishing.

This is a docs/design step, not implementation.

## Current checkpoint

B12A is closed:
- Showcase marketing template library foundation.
- Template metadata is stored in `packaging_draft_json`.
- Publish output unchanged.

B12B is closed:
- Admin review-package exposes `showcase_template_preview`.
- Admin PATCH endpoint can select/clear template metadata.
- Selection does not publish.
- Selection does not approve packaging.
- Publish output unchanged.

B12C is expected to be closed before this step:
- Telegram admin `Template / Șablon` UI.
- Safe direct template selection.
- `LAST_SEATS_URGENT` requires verified positive seat count.
- Selection uses B12B service path.
- No publish output change.
- No publish readiness change.

Media pipeline is paused at B7.4D:
- no durable image rendering/publishing integration yet.

## Goal

Design the channel adapter layer for future showcase publishing.

The system currently publishes mainly to Telegram channel.

B13A must define how future channels should be supported without breaking:

- existing Telegram publish flow;
- admin approval gates;
- template fact-lock;
- media review;
- conversion chain;
- Layer A booking/payment truth.

## Why design first

Channel publishing can easily become dangerous if it mixes:

- content generation;
- approval;
- media rendering;
- publish side effects;
- retries;
- conversion/deep links;
- analytics.

Therefore B13A must design the contract before code.

## Documents to inspect

Inspect:

- `docs/B12_SHOWCASE_MARKETING_TEMPLATE_LIBRARY.md`
- `docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`
- `docs/ADMIN_OPERATOR_WORKFLOW.md`
- `docs/CHAT_HANDOFF.md`
- `docs/TELEGRAM_CONVERSION_AND_MEDIA_FOUNDATION_CHECKPOINT.md`
- `docs/CONVERSION_CHAIN_OPS_SMOKE_READINESS.md`
- `docs/B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md`
- `docs/B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

If files are missing, report and continue.

## Code to inspect read-only

Inspect current publish-related code:

- Telegram showcase publish client/path;
- `SupplierOfferModerationService.publish`;
- `build_showcase_publication`;
- showcase message builder;
- review-package/operator_workflow publish gate;
- B12 template preview/selection services;
- media review / publish_safe helpers;
- existing Telegram sendPhoto/text behavior;
- tests around publish/showcase/moderation.

Do not edit code.

## Required design deliverable

Create:

`docs/B13_CHANNEL_ADAPTER_DESIGN.md`

## Required sections

### 1. Purpose

Define why a channel adapter layer is needed.

It should support future channels such as:

- Telegram channel;
- Telegram group;
- WhatsApp broadcast/manual copy;
- Facebook/Instagram manual copy;
- website/blog card;
- email/newsletter;
- future partner feeds.

But B13A must not implement them.

### 2. Core principles

State:

- channel adapter publishes approved content only;
- channel adapter does not decide business truth;
- channel adapter does not approve content;
- channel adapter does not create Tour;
- channel adapter does not create booking/order/payment;
- channel adapter does not invent discounts/seats/urgency;
- channel adapter does not bypass media review;
- channel adapter does not bypass `operator_workflow.actions.publish_showcase_channel`;
- channel adapter must be idempotent or explicitly non-retryable.

### 3. Existing Telegram baseline

Document current Telegram path:

```text
review-package/operator_workflow gate
→ admin confirmation
→ SupplierOfferModerationService.publish
→ build_showcase_publication
→ Telegram showcase client
→ channel message
```

### 4. Additional design sections (in deliverable)

The authored design document also includes: target layering (gates / assembly / optional outbox / adapters), contract sketch for B13B+, media (B7.4D) notes, conversion / Layer A boundaries, and B13A non-goals. See **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)**.

---

## Completion (B13A)

- **Design doc:** **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)** (purpose, principles, Telegram baseline, layering, contract sketch, media, conversion, non-goals).
- **Continuity:** **[`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md)** B13A bullet; **[`docs/HANDOFF_B13A_CHANNEL_ADAPTER_DESIGN_TO_NEXT_STEP.md`](HANDOFF_B13A_CHANNEL_ADAPTER_DESIGN_TO_NEXT_STEP.md)**.
- **No** application code, **no** tests, **no** migrations, **no** publish behavior or readiness changes.
- **Recommended next slice:** **B13B** — **`B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER`**: introduce adapter interface + Telegram wrapper with **no** output or gate changes; regression tests prove parity.