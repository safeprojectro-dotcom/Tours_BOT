# CURSOR_PROMPT_B16D1_1_EXPOSE_PREPARE_CHAIN_PLAN_PATH_CODE_FIRST

## Context

Project: Tours_BOT.

Current clean checkpoint:
- `d5d9e8a feat: add prepare conversion chain plan preview`
- `c27044 feat: add ops dashboard navigation paths`
- `a3f100 feat: add ops dashboard filters and limits`
- `b0f11e2 docs: design guarded ops automation`

B16D1 implemented:

`GET /admin/supplier-offers/{offer_id}/prepare-conversion-chain/plan`

Behavior:
- read-only action plan preview endpoint;
- shows ordered future internal preparation steps:
  - ensure/create tour bridge;
  - activate tour for catalog;
  - ensure/create active execution link;
- shows blockers, warnings, recommended next action, and `will_not_do`;
- does not mutate anything.

B16D1 tests passed:
- plan + review package: 12 passed
- publishing console + ops dashboard: 19 passed
- combined focused suite: 31 passed

Current problem:
The plan endpoint exists, but the operator must know the URL manually.

## Goal

Implement B16D1.1 as a code-first read-only discoverability improvement.

Expose the prepare-conversion-chain plan path in relevant read models so admin clients can navigate to it.

No mutation. No action execution.

## Required behavior

Add additive fields where appropriate:

```text
prepare_conversion_chain_plan_path