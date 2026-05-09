# HANDOFF_SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A_TO_NEXT_STEP

## Project

Tours_BOT — Supplier Offer -> Tour / Mini App Conversion Bridge.

## Current checkpoint before C2B9A

C2B8B is closed and pushed.

Implemented:

- Telegram admin `Publică / Publish` button.
- Workflow-gated by `operator_workflow.actions.publish_showcase_channel.enabled`.
- Propose and confirm both re-read review-package/operator_workflow.
- Legacy one-step Telegram publish suppressed/retired from main detail keyboard.
- HTTP publish semantics preserved.
- No Mini App changes.
- No booking/payment/order changes.
- No Tour/catalog/execution link changes.
- No migrations.

## Why C2B9A exists

Next strategic block is Supplier Offer -> Tour / Mini App conversion bridge.

This crosses the boundary between:

- Supplier Offer / marketing showcase / publication;
- Tour / catalog / booking/payment execution truth.

Therefore, C2B9A must be a Plan/readiness audit before implementation.

## Core principles

- Supplier Offer is raw/commercial/marketing source, not automatically bookable.
- Telegram channel is discovery/showcase.
- Mini App/catalog execution truth must be strict and current.
- `visibility != bookability`.
- No hidden Tour creation.
- No hidden ORM trigger.
- No AI mutation of source-of-truth execution data.
- Admin must explicitly create/link/activate conversion path.
- Layer A booking/payment/order truth must remain untouched.
- Service layer owns business logic.
- Repository layer remains persistence-only.

## C2B9A expected output

Cursor should inspect current docs and code and report:

1. existing bridge-related models/tables/services/endpoints;
2. existing `/start supoffer_<id>` and Mini App landing behavior if any;
3. existing execution link or bridge entities if any;
4. gaps for safe Offer -> Tour conversion;
5. risks;
6. proposed next implementation sequence;
7. recommended immediate next prompt.

## C2B9A non-goals

Do not implement:

- Tour creation;
- bridge table/model;
- execution link activation;
- Mini App routing;
- Telegram routing changes;
- booking/payment/order changes;
- migrations.

Docs-only updates are allowed if needed.

## Likely next steps after C2B9A

Depending on audit result, likely sequence may be:

1. C2B9B — bridge design/read-model finalization if needed.
2. C2B10A — central admin create/link Tour from supplier offer, guarded and explicit.
3. C2B10B — execution link activation/actionability.
4. C2B11 follow-up — Telegram deep link routes to exact Mini App Tour only when active execution link exists.
5. C2B12 — admin/ops visibility.

Exact names and order must follow Cursor’s audit and current repo state.

## Post-Cursor review checklist

Before any commit/push, GPT must check:

- did Cursor change only docs, or no files?
- no code implementation unless explicitly approved;
- no migrations;
- no Mini App changes;
- no booking/payment/order changes;
- no publish semantics changes;
- `git status --short`;
- `git diff --stat`.

Commit/push only after user provides Cursor report and GPT reviews it.