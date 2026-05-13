# CURSOR_PROMPT_B16D1_PREPARE_CONVERSION_CHAIN_PLAN_PREVIEW_CODE_FIRST

## Context

Project: Tours_BOT.

Current clean checkpoint:
- `c27044 feat: add ops dashboard navigation paths`
- `a3f100 feat: add ops dashboard filters and limits`
- `b0f11e2 docs: design guarded ops automation`
- `6d4a911 feat: add admin ops dashboard read view`

B16D design gate is already closed.

B16D decision:
- do not jump to auto-publish;
- create staged guarded automation;
- future `prepare_conversion_chain` may internally prepare an approved supplier offer by:
  1. creating/linking tour bridge if missing;
  2. activating linked tour for catalog if eligible;
  3. creating active execution link if missing;
- it must NOT publish to Telegram;
- public publish remains a separate `public_dangerous` action requiring explicit confirmation.

B16D1 goal:
Add a read-only action plan preview endpoint.

This endpoint must show what would happen if future `prepare_conversion_chain` were executed, but it must not execute anything.

## Goal

Implement B16D1 as a code-first, read-only preview endpoint for supplier offer conversion preparation.

Recommended endpoint:

`GET /admin/supplier-offers/{offer_id}/prepare-conversion-chain/plan`

The endpoint returns a structured plan:

- overall eligibility;
- ordered steps;
- what is already done;
- what would be done;
- blockers;
- warnings;
- explicit "will not do" list;
- recommended next action.

## Hard safety boundary

This endpoint is read-only.

Do NOT:
- create tour bridge;
- activate tour;
- create execution link;
- publish Telegram post;
- send Telegram message;
- create supplier execution attempts;
- mutate orders;
- mutate payments;
- mutate reservations;
- change seats;
- call Layer A mutation services;
- change Mini App routing;
- add migrations.

## Source of truth / reuse

Inspect and reuse existing read logic where possible:

- supplier offer review-package service;
- conversion status panel;
- linked_tour_catalog data;
- active_tour_bridge data;
- execution_links_review;
- operator_workflow actions;
- existing action gate/status logic;
- existing admin route auth pattern.

Do not duplicate complex business rules if an existing read service already exposes the relevant status.

If the endpoint needs a small service, create a narrow read-only service, e.g.:

- `app/services/admin_prepare_conversion_chain_plan.py`

or similar project-style name.

Keep route thin.

## Suggested response schema

Create additive schemas in an appropriate file, likely:

- `app/schemas/admin_prepare_conversion_chain_plan.py`

or extend an existing admin/supplier-offer schema if that is project style.

Suggested models:

```python
AdminPrepareConversionChainPlanStepRead
AdminPrepareConversionChainPlanRead
