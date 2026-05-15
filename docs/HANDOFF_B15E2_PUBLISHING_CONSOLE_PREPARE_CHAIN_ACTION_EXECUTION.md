# HANDOFF_B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_ACTION_EXECUTION

## Project
Tours_BOT

## Block
B15E2 — Publishing Console **action execution** for **`prepare_conversion_chain`**

## Status
**Closed (implemented).** Continuity: **`docs/CHAT_HANDOFF.md`**.

## Prerequisites (checkpoints)

Closed checkpoints (reference):

- B16D2C — **`POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain`**
- B16D2D — read-model **`prepare_conversion_chain_action`** affordances
- B16D2E — production smoke runbook **[`docs/B16D2E_PREPARE_CONVERSION_CHAIN_PRODUCTION_SMOKE.md`](B16D2E_PREPARE_CONVERSION_CHAIN_PRODUCTION_SMOKE.md)**

## Goal

Allow operators to run guarded **`prepare_conversion_chain`** from a **publishing-console-scoped** admin entry, without using **`GET /admin/publishing-console`** for mutation (that route stays read-only).

## Action

**`code`:** `prepare_conversion_chain`

## Execution routes (both delegate to the same service)

| Surface | Method / path | `actor_surface` in result |
|--------|----------------|----------------------------|
| **Primary admin (B16D2C)** | **`POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain`** | **`admin_http`** |
| **Publishing console (B15E2)** | **`POST /admin/publishing-console/supplier-offers/{offer_id}/prepare-conversion-chain`** | **`publishing_console`** |

Shared handler: **`_handle_prepare_conversion_chain_post`** in **`app/api/routes/admin.py`** → **`PrepareConversionChainExecutionService.execute(...)`** only.

**Body / response:** same as B16D2C — **`AdminPrepareConversionChainExecuteBody`**, **`AdminPrepareConversionChainExecutionResultRead`**.

## Required safeguards

- Admin auth (`Authorization: Bearer` or `X-Admin-Token`) on **`/admin`**
- **`idempotency_key`** required (non-blank after trim)
- **`confirm=true`** required for live (**`dry_run=false`**), else **422**
- **`dry_run`** supported (`confirm` may be false)
- Idempotent replay unchanged (service / audit foundation)
- Routes thin; business rules in **`PrepareConversionChainExecutionService`**

## Must not happen

- Telegram publish / send / retry
- Showcase channel post
- Scheduler / auto-publish
- Mini App routing / B11 deep-link changes
- Order / payment / reservation / Layer A booking mutation (outside existing prepare-chain service path)
- New migration / table for this slice

## Expected verification (local)

- **`python -m compileall app tests`**
- **`tests/unit/test_admin_publishing_console_prepare_chain_action.py`**
- Regression: **`test_admin_prepare_conversion_chain_api`**, **`test_admin_publishing_console`**, **`test_prepare_conversion_chain_execution_service`**, **`test_prepare_conversion_chain_d2d_affordance`**

## Next after B15E2

- **B15E2 smoke (ops):** **`docs/CURSOR_PROMPT_B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_SMOKE.md`** (or equivalent) — e.g. **dry_run** + safe **already_prepared** / staging **`offer_id`** only.
- If a bug appears: small scoped fix + tests; no broad action framework.

## Implementation reference

- **Tests:** **`tests/unit/test_admin_publishing_console_prepare_chain_action.py`**
- **Docs touchpoints:** **`docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`** (note: **GET** console read-only; **POST** execute is separate).
