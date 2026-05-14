# CURSOR_PROMPT_B16D2A_GUARDED_ACTION_AUDIT_IDEMPOTENCY_FOUNDATION

## Context

Project: Tours_BOT.

Current clean checkpoint:
- `3057ba8 docs: design prepare conversion chain execution`
- `e301088 feat: add ops dashboard audit visibility`
- `a3e435 feat: add prepare conversion chain readiness summary`
- `e74f505 feat: expose prepare conversion chain plan paths`
- `d5d9e8a feat: add prepare conversion chain plan preview`

B16D2 design gate is closed.

Future action:

`POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain`

Future chain:
1. ensure tour bridge
2. activate tour for catalog
3. ensure active execution link

But this prompt is **B16D2A only**.

## Goal

Implement the persistence foundation for guarded admin actions:

- action attempt audit;
- idempotency key tracking;
- step-level audit records;
- repository/service helpers;
- tests.

Do NOT implement the actual `prepare_conversion_chain` execution.

Do NOT add the POST endpoint.

## Required boundary

This slice must not perform any business mutation except writing its own audit/idempotency rows in tests/service helpers.

Do NOT:
- create tour bridge;
- activate catalog;
- create execution link;
- publish/send Telegram;
- retry publish;
- mutate orders;
- mutate payments;
- mutate reservations;
- change seats;
- call Layer A booking/payment services;
- change Mini App routing;
- create supplier execution attempts;
- create notification outbox rows.

## New persistence

Create tables for generic guarded admin action attempts.

Preferred names:

```text
admin_guarded_action_attempts
admin_guarded_action_steps