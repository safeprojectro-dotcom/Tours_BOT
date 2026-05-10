# CURSOR_PROMPT_B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN

You are working on Tours_BOT.

Run B13C: Showcase publish attempt / audit design.

This is a docs/design step, not implementation.

## Current checkpoint

B13A closed:
- Channel adapter design created.
- Existing Telegram publish baseline documented.
- Future adapter/outbox/audit layer separated from gates and content assembly.

B13B closed / expected closed:
- `ShowcaseChannelAdapter` interface added.
- `TelegramShowcaseChannelAdapter` wraps existing `send_showcase_publication`.
- `SupplierOfferModerationService.publish` uses adapter wrapper.
- Behavior-preserving refactor:
  - same publish output;
  - same Telegram send behavior;
  - same chat_id/message_id persistence;
  - same readiness;
  - no new channels;
  - no migrations;
  - no Mini App / booking / payment / orders.

B12A/B/C closed:
- marketing template foundation;
- admin preview/select;
- Telegram template selection UI;
- publish output unchanged.

Media pipeline remains paused at B7.4D.

## Goal

Design the future publish attempt / audit model before implementation.

The design must answer:

- whether a publish attempt table is needed;
- what should be audited before/during/after channel publish;
- how to avoid duplicate sends;
- how retries should work;
- how to preserve current Telegram behavior until implementation;
- what B13D/B13E should do next.

Do not implement code.

## Why design first

Publishing is a public side effect.

Adding retries/audit/idempotency without a clear contract can cause:
- duplicate Telegram posts;
- mismatch between SupplierOffer lifecycle and provider message id;
- hidden retries;
- unclear operator accountability;
- broken rollback semantics.

## Documents to inspect

Inspect:

- `docs/B13_CHANNEL_ADAPTER_DESIGN.md`
- `docs/HANDOFF_B13B_CHANNEL_ADAPTER_INTERFACE_TELEGRAM_WRAPPER_TO_NEXT_STEP.md`
- `docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`
- `docs/ADMIN_OPERATOR_WORKFLOW.md`
- `docs/CHAT_HANDOFF.md`
- `docs/CONVERSION_CHAIN_OPS_SMOKE_READINESS.md`
- `docs/TELEGRAM_CONVERSION_AND_MEDIA_FOUNDATION_CHECKPOINT.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

If files are missing, report and continue.

## Code to inspect read-only

Inspect current code only for factual grounding:

- `app/services/showcase_channel_adapter.py`
- `app/services/supplier_offer_moderation_service.py`
- `app/services/telegram_showcase_client.py`
- `app/services/supplier_offer_showcase_message.py`
- `app/services/supplier_offer_operator_workflow.py`
- `app/bot/handlers/admin_moderation.py`
- admin publish route in `app/api/routes/admin.py`
- tests around publish/moderation/admin Telegram.

Do not edit code.

## Required deliverable

Create:

`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`

## Required sections

### 1. Purpose

Explain why publish attempt audit is needed:

- public side-effect accountability;
- duplicate prevention;
- provider reference tracking;
- operator traceability;
- future retries;
- future multi-channel support.

### 2. Current behavior baseline

Document current behavior:

```text
admin action / HTTP publish
→ readiness/lifecycle/config checks
→ build_showcase_publication
→ Telegram adapter
→ send_showcase_publication
→ on success: SupplierOffer lifecycle/status + showcase_chat_id + showcase_message_id updated
```

### 3. Additional sections (in deliverable)

The full authored document also includes: whether an attempt **table** is needed (options), **audit** fields and phases, **idempotency** / duplicate prevention, **retry** policy, **transaction** boundary, phased rollout, and **B13D / B13E** forward pointers. See **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)**.

---

## Completion (B13C)

- **Design doc:** **[`docs/B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md`](B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN.md)**.
- **No** application code, **no** tests, **no** migrations, **no** publish behavior or readiness changes.
- **Continuity:** **[`docs/B13_CHANNEL_ADAPTER_DESIGN.md`](B13_CHANNEL_ADAPTER_DESIGN.md)** B13C pointer; **[`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md)**; **[`docs/HANDOFF_B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN_TO_NEXT_STEP.md`](HANDOFF_B13C_PUBLISH_ATTEMPT_AUDIT_DESIGN_TO_NEXT_STEP.md)**.
- **Implement** attempt storage or retries only after **explicit** product approval.