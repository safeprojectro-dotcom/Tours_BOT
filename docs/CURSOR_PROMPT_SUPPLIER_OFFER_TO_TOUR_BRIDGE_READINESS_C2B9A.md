# CURSOR_PROMPT_SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A

You are working on Tours_BOT.

This is C2B9A: Supplier Offer -> Tour / Mini App Conversion Bridge readiness audit and implementation plan.

## Current checkpoint

C2B8B is closed and pushed:

- Telegram admin `Publică / Publish` button implemented.
- Button is workflow-gated by `operator_workflow.actions.publish_showcase_channel.enabled == true`.
- Propose and confirm both re-read review-package/operator_workflow.
- Legacy one-step Telegram publish was suppressed/retired from the main detail keyboard.
- No Mini App, booking/payment/order, Tour/catalog/execution link, storage, or migration changes were made.

## Why this step is Plan mode

The next strategic block is the Offer -> Tour / Mini App conversion bridge.

This touches the boundary between:

- Layer B: Supplier Offer / marketing showcase / supplier commerce;
- Layer A: Tour catalog / reservation / payment execution truth.

Do not implement code yet.

First perform a read-only audit and produce a precise next implementation plan.

## Core architecture principles

Preserve these principles:

1. Supplier Offer is not automatically bookable.
2. Telegram channel/showcase is a marketing/discovery surface.
3. Mini App / catalog execution truth must be strict and current.
4. `visibility != bookability`.
5. No hidden ORM triggers.
6. No AI-driven source-of-truth mutation.
7. No supplier action can directly create a public/bookable Tour.
8. Admin must explicitly approve/publish/activate conversion path.
9. Booking/payment/order truth remains Layer A.
10. Service layer owns business logic.
11. Repository layer stays persistence-oriented.
12. PostgreSQL-first.
13. Do not change existing booking/payment/order behavior.

## Documents to inspect first

Inspect these docs if present:

- `docs/CHAT_HANDOFF.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/TECH_SPEC_TOURS_BOT.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/BUSINESS-план-v2.txt` or equivalent business plan document if present
- `docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`
- `docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md`
- `docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- C2B8B prompt/handoff docs

If some files do not exist, report that clearly and continue with available sources.

## Code areas to inspect

Read-only inspection only.

Inspect current code/schema around:

- `SupplierOffer`
- `supplier_offers`
- supplier offer lifecycle/status fields
- `SupplierOfferModerationService`
- review-package / operator_workflow
- publish showcase path
- Telegram `/start supoffer_<id>` routing if present
- `Tour`
- `tours`
- `TourStatus`
- `TourSalesMode`
- catalog visibility / Mini App catalog services
- any existing bridge/link model:
  - `SupplierOfferTourBridge`
  - `supplier_offer_tour_bridges`
  - `supplier_offer_execution_links`
  - similar names
- any existing admin endpoints that create/link tours from offers
- any existing actionability/readiness services

## What to answer

Produce a concise but complete audit report.

The report must include:

### 1. Current bridge-related state

List what already exists in code/docs:

- existing models/tables;
- existing services;
- existing admin endpoints;
- existing Telegram deep-link routing;
- existing Mini App landing/catalog routing;
- existing operator_workflow actions related to bridge/conversion if any.

### 2. Gaps

List what is missing for a safe Supplier Offer -> Tour conversion bridge.

Important gap categories:

- explicit admin action to create/link Tour from approved/published offer;
- conversion bridge/read model;
- active execution link;
- Mini App actionability state;
- Telegram deep-link target decision;
- catalog visibility guard;
- duplicate/recurrence guard;
- audit trail;
- tests.

### 3. Existing risks

Identify risks if implementation is rushed:

- hidden Tour creation;
- duplicate Tour rows;
- published offer with no bookable execution target;
- Mini App showing stale/non-bookable route;
- channel link opening a wrong/old Tour;
- bypassing admin approval;
- changing Layer A booking/payment semantics;
- confusing `published` with `bookable`.

### 4. Proposed next implementation slices

Propose the next safe sequence after C2B9A.

Use small but meaningful slices, for example:

- C2B9B: bridge design/doc finalization or read-model endpoint if needed;
- C2B10A: central admin create/link Tour from supplier offer, draft-only or guarded;
- C2B10B: execution link activation/actionability;
- C2B11 follow-up: Telegram deep link to exact Mini App Tour when active execution link exists;
- C2B12: admin/ops visibility.

Do not assume these names are final; propose the best sequence based on actual repo state.

### 5. Recommended immediate next Cursor prompt

Write the next recommended implementation prompt title and a short scope summary.

Do not implement it yet.

## Forbidden in this step

Do NOT:

- implement code;
- create migrations;
- create or modify Tour rows;
- create bridge tables;
- change SupplierOffer lifecycle;
- change publish semantics;
- touch Mini App code;
- touch booking/payment/orders;
- change Telegram callbacks;
- change HTTP routes;
- edit services unless only documentation comments are needed, but prefer no code changes.

## Allowed outputs

Allowed:

- audit/report in chat;
- optionally create or update a docs-only file if the repository already has a clear place for this checkpoint, for example:
  - `docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A.md`
  - or update `docs/CHAT_HANDOFF.md` with a short C2B9A planning note.

If you create/update docs, report exact files.

## After Plan report

Return:

1. files inspected;
2. docs inspected;
3. current state summary;
4. gaps;
5. risks;
6. proposed next implementation sequence;
7. recommended immediate next prompt;
8. any docs changed;
9. `git status --short`;
10. `git diff --stat`.

Do not commit.